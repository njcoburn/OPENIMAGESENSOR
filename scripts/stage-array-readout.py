"""Stage shared schematic readout onto independently C-extracted array coupons.
All stages share one startup/scan schedule. Run in the project tools container.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,runpy,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1]
read_raw=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--timeout',type=float,default=180);a=p.parse_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
results=[]
for nr,nc,stage in [(3,3,s) for s in range(5)]+[(4,4,4)]:
 d=out/f'r{nr}c{nc}-stage{stage}';d.mkdir()
 source=R/f'build/array-extension-finite-20260920/r{nr}c{nc}'
 model=(source/'capacitance.spice').read_text();(d/'array.spice').write_text(model)
 old=(source/'capacitance-tb.spice').read_text();instance=next(l for l in old.splitlines() if l.startswith('Xarray '));lights=[l for l in old.splitlines() if l.startswith('Ilight')]
 lines=['Staged C-only array plus schematic shared readout']+[l for l in old.splitlines() if l.startswith(('.include /foss/pdks','.lib ','.options '))]
 lines+=['.include array.spice','.temp 27',instance,*lights]
 if stage<4:lines+=['Vsource VDD 0 3.3','Vreset VRESET 0 2']
 else:lines+=['Vsource RAW 0 3.3','Rsupply RAW VDD 2','Vreset RESETDRV 0 2','Rreset RESETDRV VRESET 1']
 for r in range(nr):
  t=.00125+r*.001
  points=[0,1,.00122,1,.00122001,0,t,0,t+1e-8,1,t+20.01e-6,1,t+20.02e-6,0]
  lines += [f'Vr{r} CTL_RST{r} 0 PWL('+ ' '.join(f'{x:.12g}' for x in points)+')',f'Vs{r} CTL_ROW{r} 0 PULSE(0 1 { .00217+r*.001:.12g} 10n 10n {6+18*nc}u {nr}m)']
  for kind in ['RST','ROW']:
   n=f'{kind}{r}';lines += [f'Bdrive_{n} DRIVE_{n} 0 V=V(CTL_{n})*V(VDD)',f'Rdrive_{n} DRIVE_{n} {n} 100',f'Rpull_{n} {n} '+('VDD' if kind=='RST' else '0')+' 100k']
 save=['v(VDD)']+[f'v(COL{c})' for c in range(nc)]
 if stage==0:
  for c in range(nc):lines += [f'Rload{c} COL{c} 0 1Meg',f'Cload{c} COL{c} 0 1p']
 else:
  geom='nfet_03v3 w=2u l=2u ad=0.88p as=0.88p pd=4.88u ps=4.88u'
  lines+=['Rbias VDD BIAS 5.1Meg','Cbias BIAS 0 1p','Xref BIAS BIAS 0 0 '+geom]
  for c in range(nc):
   lines += [f'Xbias{c} COL{c} BIAS 0 0 '+geom,f'Xmux{c} OUT SEL{c} COL{c} 0 nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',f'Vsel{c} CTL_SEL{c} 0 PULSE(0 1 {.002175+c*18e-6:.12g} 10n 10n 16u 1m)',f'Bdrive_SEL{c} DRIVE_SEL{c} 0 V=V(CTL_SEL{c})*V(VDD)',f'Rdrive_SEL{c} DRIVE_SEL{c} SEL{c} 100',f'Rpull_SEL{c} SEL{c} 0 100k']
  lines+=['Cout OUT 0 1p','Rout OUT 0 1T'];save+=['v(OUT)','v(BIAS)']
 if stage>=2:
  buffer=(R/'circuits/output-buffer.spice').read_text();(d/'buffer.spice').write_text(buffer)
  lines+=['.include buffer.spice','Xbuffer OUT BUF PREF VDD 0 output_buffer','Rpref PREF 0 49.9k','Cpref PREF 0 1p'];save+=['v(BUF)','v(PREF)']
  if stage==2:lines+=['Cbuf BUF 0 1p','Rbuf BUF 0 1Meg']
 if stage>=3:
  lines+=['Rbond BUF BOND 1','Lbond BOND ADC_PAD 5n','Cexternal ADC_PAD 0 1p','Riso ADC_PAD ADCIN 100','Cboard ADCIN 0 100p','Rinput ADCIN 0 1Meg','Csample HOLD 0 20p','Bsample ADCIN HOLD I=V(ADCIN,HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(ACQ)-1.65)/0.1)))','Bsample_reset HOLD 0 I=V(HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(RSTADC)-1.65)/0.1)))']
  for name,offset,width in [('ACQ',.00218,5e-6),('RSTADC',.002178,1e-6)]:
   pts=[0,0]
   for r in range(nr):
    for c in range(nc):
     t=offset+r*.001+c*18e-6;pts += [t,0,t+1e-8,3.3,t+width,3.3,t+width+1e-8,0]
   lines += [f'V{name} {name} 0 PWL('+' '.join(f'{x:.12g}' for x in pts)+')']
  save+=['v(ADCIN)','v(HOLD)']
 stop=.00225+(nr-1)*.001
 lines += ['.save '+' '.join(save),f'.tran 200n {stop:.12g} 0 200n','.control','set num_threads=1','set filetype=binary','run stream.raw','quit','.endc','.end']
 deck='\n'.join(lines)+'\n';(d/'test.spice').write_text(deck)
 result={'rows':nr,'columns':nc,'stage':stage,'array_sha256':hashlib.sha256(model.encode()).hexdigest(),'deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),'target_s':stop,'completed':False,'scope':'C-only extracted unfilled array; schematic readout; no pads/clamps or shared-readout wiring PEX'}
 start=time.monotonic()
 with (d/'ngspice.log').open('w') as log:
  proc=subprocess.Popen(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'OMP_NUM_THREADS':'1'})
  try:proc.wait(timeout=a.timeout);result['timed_out']=False
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=10);result['timed_out']=True
 result['seconds']=time.monotonic()-start;log=(d/'ngspice.log').read_text();result['errors']=[l for l in log.splitlines() if re.search('timestep too small|aborted|^Error',l,re.I)]
 result['solver']='KLU' if 'Using KLU as Direct Linear Solver' in log else 'SPARSE 1.3' if 'Using SPARSE 1.3' in log else 'unknown'
 result['compatibility']='none' if 'No compatibility mode selected!' in log else 'see log'
 result['included_files_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in d.glob('*.spice')}
 try:
  names,data=read_raw(d/'stream.raw');result['end_s']=float(data[-1,0]);result['completed']=bool(not result['timed_out'] and proc.returncode==0 and not result['errors'] and np.isfinite(data).all() and data[-1,0]>=stop-1e-12)
  def interp(n,t):return float(np.interp(t,data[:,0],data[:,names.index(n.lower())]))
  samples=[]
  for r in range(nr):
   for c in range(nc):
    t=.002185+r*.001+c*18e-6
    if t>data[-1,0]:continue
    sample={'row':r,'column':c,'time_s':t,'photocurrent_pA':[0,80,240][(c+2*r)%3]}
    for n in ['VDD',f'COL{c}']+(['OUT'] if stage>=1 else [])+(['BUF'] if stage>=2 else [])+(['ADCIN','HOLD'] if stage>=3 else []):sample[n]=interp('v('+n+')',t)
    sample['signal_V']=sample['HOLD' if stage>=3 else 'BUF' if stage>=2 else 'OUT' if stage>=1 else f'COL{c}'];samples.append(sample)
  result['samples']=samples
  result['brightness_order_correct']=len(samples)==nr*nc and all(x['signal_V']>y['signal_V'] for x in samples for y in samples if x['row']==y['row'] and x['photocurrent_pA']<y['photocurrent_pA'])
  if stage>=3:result['max_acquisition_error_V']=max(abs(x['HOLD']-x['ADCIN']) for x in samples)
 except Exception as e:result['capture_error']=repr(e)
 (d/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(result),flush=True)
