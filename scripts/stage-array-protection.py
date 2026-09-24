"""Add exact extracted protection devices to the staged 3x3 coupon.
Pad/clamp wiring parasitics are deliberately absent; frozen MOS capacitors are
restored with the full clamp bank. This is not a full-layout model.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,runpy,shutil,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1]
helpers=runpy.run_path(str(R/'scripts/diagnose-shared-circuit.py'));partition=helpers['partition'];pins=helpers['pins'];read_raw=helpers['read_raw']
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--timeout',type=float,default=180);p.add_argument('--cases',nargs='+',default=['5','6','7'],choices=['5','6','7','6-rails','6-unused','6-reset-norton']);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
source=R/'build/functional-camera-diagnostic/reset-edge-internal-20260920';model=(source/'model.spice').read_text();groups=partition(model.splitlines());records={l.split()[0]:l.split() for l in model.splitlines() if l.startswith(('X','D'))}
photo={x['photodiode'] for x in json.loads((R/'simulations/final-chip-pixel-map.json').read_text())['pixels']}
pads={n for n in groups['CAMERA']['devices'] if (n.startswith('D') and n not in photo) or (n.startswith('X') and records[n][4]=='ppolyf_u')}
assert len(pads)==143
other={n for k,g in groups.items() if k!='CAMERA' and not k.startswith('PEX_SAFE_') for n in g['devices']}
clamps={n for k,g in groups.items() if k.startswith('PEX_SAFE_') for n in g['devices']}
base=R/'build/staged-readout-20260921/r3c3-stage4';base_deck=(base/'test.spice').read_text();results=[]
cases={'5':pads,'6':pads|other,'7':pads|other|clamps,'6-rails':pads|set(groups['RAILS']['devices']),'6-unused':pads|(other-set(groups['RAILS']['devices'])),'6-reset-norton':pads|other}
for label in a.cases:
 stage=int(label[0]);selected=cases[label]
 d=out/f'stage{label}';d.mkdir()
 for f in ['array.spice','buffer.spice']:shutil.copyfile(base/f,d/f)
 def rename(n):return '0' if n=='GND' else n.removeprefix('sensor_3x3_0.')
 rows=[]
 for n in sorted(selected):
  f=records[n].copy();npins=len(pins(f));f[0]=f[0][0]+'protect_'+f[0][1:]
  f[1:npins+1]=[rename(v) for v in f[1:npins+1]];rows.append(' '.join(f))
 if stage==7:
  for l in model.splitlines():
   if l.startswith('Cfreeze'):
    f=l.split();f[1:3]=[rename(v) for v in f[1:3]];rows.append(' '.join(f))
 (d/'protection.spice').write_text('\n'.join(rows)+'\n')
 lines=[]
 for line in base_deck.splitlines():
  f=line.split()
  if f and (f[0].startswith(('Rdrive_','Rpull_')) or f[0] in ['Rreset','Rbias','Cbias','Rpref','Cpref','Rbond']):
   f[1:3]=['PAD_'+n if n in ['VRESET','BIAS','PREF','BUF'] or re.fullmatch('(RST|ROW|SEL)[0-2]',n) else n for n in f[1:3]];line=' '.join(f)
  lines.append(line)
 idx=lines.index('.include array.spice');lines[idx:idx]=['.include protection.spice','.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical','.nodeset V(NC_P10)=1.65 V(NC_P11)=1.65 V(NC_P12)=1.65 V(NC_P15)=1.65']
 deck='\n'.join(lines)+'\n'
 if label=='6-reset-norton':
  old='Vreset RESETDRV 0 2\nRreset RESETDRV PAD_VRESET 1\n';assert deck.count(old)==1
  deck=deck.replace(old,'Breset PAD_VRESET 0 I=(V(PAD_VRESET)-2)/1\n')
 (d/'test.spice').write_text(deck)
 result={'stage':stage,'variant':label,'protection_device_records':len(selected),'frozen_caps':sum(l.startswith('Cfreeze') for l in rows),'completed':False,'source_sha256':hashlib.sha256(model.encode()).hexdigest(),'deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),'selected_original_devices':sorted(selected)}
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
  names,data=read_raw(d/'stream.raw');result['end_s']=float(data[-1,0]);result['completed']=bool(not result['timed_out'] and proc.returncode==0 and not result['errors'] and np.isfinite(data).all() and data[-1,0]>=.00425-1e-12)
  samples=[]
  for r in range(3):
   for c in range(3):
    t=.002185+r*.001+c*18e-6
    if t>data[-1,0]:continue
    v={n:float(np.interp(t,data[:,0],data[:,names.index('v('+n.lower()+')')])) for n in ['VDD','OUT','BUF','ADCIN','HOLD']};samples.append(dict(row=r,column=c,time_s=t,photocurrent_pA=[0,80,240][(c+2*r)%3],**v))
  result['samples']=samples;result['brightness_order_correct']=len(samples)==9 and all(x['HOLD']>y['HOLD'] for x in samples for y in samples if x['row']==y['row'] and x['photocurrent_pA']<y['photocurrent_pA'])
  if samples:result['max_acquisition_error_V']=max(abs(s['HOLD']-s['ADCIN']) for s in samples)
 except Exception as e:result['capture_error']=repr(e)
 (d/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['samples','selected_original_devices']}),flush=True)
