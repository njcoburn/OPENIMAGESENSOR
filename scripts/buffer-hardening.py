"""Diagnose cold idle failure and measure stronger-buffer candidates."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,re,json,hashlib,subprocess
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'build/buffer-hardening';out.mkdir(parents=True,exist_ok=True)
source_files=[root/'scripts/output-buffer.py',root/'circuits/output-buffer.spice',root/'checkpoints/readout/pex/readout_reduced.spice',root/'simulations/extracted-20um/rc-filled/array_reduced.spice']
fingerprint=''.join(hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files)
def ng(dest,s):
 key=hashlib.sha256((s+fingerprint).encode()).hexdigest();stamp=dest/'success.sha256'
 if stamp.exists() and stamp.read_text()==key:return np.loadtxt(dest/'wave.txt',skiprows=1)
 (dest/'testbench.spice').write_text(s);p=subprocess.run(['ngspice','-b',str(dest/'testbench.spice')],capture_output=True,text=True);(dest/'run.log').write_text(p.stdout+p.stderr)
 assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',p.stdout+p.stderr,re.I|re.M),str(dest)
 d=np.loadtxt(dest/'wave.txt',skiprows=1);assert np.isfinite(d).all();stamp.write_text(key);return d

def combined(corner,temp,ua,precharge=False,step=.1,diode='diode_typical',variant=''):
 name=f'{corner}_{temp}C_{ua}uA'+('_precharge' if precharge else '')+f'_{step}us'+('_'+diode if diode!='diode_typical' else '')+variant;dest=out/name;dest.mkdir(exist_ok=True)
 m=runpy.run_path(str(root/'scripts/output-buffer.py'));run=m['run'];g=run.__globals__;base=g['base']
 base=base.replace('sm141064.ngspice typical',f'sm141064.ngspice {corner}').replace('sm141064.ngspice diode_typical',f'sm141064.ngspice {diode}').replace('Vdd VDD',f'.temp {temp}\nVdd VDD',1).replace('tran 0.2u',f'tran {step}u').replace('reltol=1e-4','reltol=1e-5' if step<.1 else 'reltol=5e-5')
 if precharge:
  # Real NMOS switch; externally provided 0.8V precharge reference and timing.
  # On during idle, off 5us before row selection and throughout all mux slots.
  pre='Vpre VPRE 0 0.8\nXpre OUT PRE VPRE 0 nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u\nVprectl PRE 0 PULSE(3.3 0 965u 10n 10n 70u 1m)\n'
  base=base.replace('.control',pre+'.control')
 if variant=='_no_inductor':
  stage=g['stage']
  g['stage']=lambda *a,**kw:stage(*a,**kw).replace('Lbond BOND PAD 5n','Rbondtest BOND PAD 0.001')
 if variant=='_schematic_readout':base=base.replace(str(root/'checkpoints/readout/pex/readout_reduced.spice'),str(root/'checkpoints/readout/pex/readout_devices.spice')).replace('SEL2 readout_pex','SEL2 readout_devices')
 if variant=='_schematic_array':
  base=base.replace('/simulations/extracted-20um/rc-filled/array_reduced.spice','/simulations/extracted-20um/rc-filled/array_devices.spice').replace('ROW2 array_pex','ROW2 array_devices')
  mapping=json.loads((root/'simulations/extracted-20um/rc-filled/reduction.json').read_text())['node_map']
  for key,nodes in mapping.items():
   for role,node in nodes.items():base=base.replace('xarray.'+node, '0' if role=='anode' else 'xarray.'+('s' if role=='sense' else 'f')+key)
 if variant=='_startup_reset':
  # All rows reset at power-up, then retain the original rolling-reset schedule.
  for row in range(3):
   pts=[(0,3.3),(20e-6,3.3),(20.01e-6,0)]
   for frame in range(3):
    t=50e-6+row*.001+frame*.003
    pts.extend([(t,0),(t+10e-9,3.3),(t+20.01e-6,3.3),(t+20.02e-6,0)])
   line=f'Vr{row} RST{row} 0 PWL('+ ' '.join(f'{t:.12g} {v}' for t,v in pts)+')'
   base=re.sub(rf'(?m)^Vr{row} .*$',line,base)
 g['base']=base;g['out']=dest;g['ng']=ng
 if variant=='_probe_sense':
  def probe(folder,s):
   if '\ntran ' in s:s=re.sub(r'(?m)^(wrdata .*)$',r'\1 v(xarray.n312)-v(xarray.n186) v(xarray.n276)-v(xarray.n187)',s)
   return ng(folder,s)
  g['ng']=probe
 try:
  _,r,d,dc=run((ua,100,True,5));assert d[-1,0]>=.00905
  assert all(dc[0,0]<=s['input_V']<=dc[-1,0] for s in r['samples'])
  samples=np.array([s['output_V'] for s in r['samples']]).reshape(3,3);pattern=np.array([[0,80,240],[240,0,80],[80,240,0]])
  order=all(np.all(np.diff(samples[row,np.argsort(pattern[row])])<0) for row in range(3))
  r.update(status='complete',corner=corner,temp_C=temp,precharge=precharge,step_us=step,diode=diode,max_hold_error_mV=max(abs(s['hold_error_mV']) for s in r['samples']),brightness_order_ok=bool(order))
 except Exception as e:r={'status':'simulation_failed','error':str(e),'corner':corner,'temp_C':temp,'precharge':precharge,'bias_reference_uA':ua}
 (dest/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(name,r['status'],r.get('max_hold_error_mV'),flush=True)
 return name,r

def isolate(board):
 name='cold_buffer_alone'+('_board' if board else '_RCload');dest=out/name;dest.mkdir(exist_ok=True)
 m=runpy.run_path(str(root/'scripts/output-buffer.py'));header=m['base'].split('Vdd VDD')[0].replace('sm141064.ngspice typical','sm141064.ngspice ss')
 stage=m['stage'](20,100,False)
 if not board:stage=re.sub(r'Rbond BUF BOND 1\nLbond BOND PAD 5n\nCpad PAD 0 5p\nRiso PAD ADCIN 100', 'Rsimple BUF ADCIN 100',stage)
 s=header+'.temp -40\nVdd VDD 0 3.3\nVin OUT 0 PWL(0 0.1 1m 0 2m 0.1)\n'+stage+f'.control\nset num_threads=1\nset wr_singlescale\nset wr_vecnames\ntran 0.1u 2m\nwrdata {dest}/wave.txt v(OUT) v(BUF) v(ADCIN)\nquit\n.endc\n.end\n'
 try:d=ng(dest,s);assert d[-1,0]>=.002;r={'status':'complete','min_input_V':float(d[:,1].min()),'max_input_V':float(d[:,1].max())}
 except Exception as e:r={'status':'simulation_failed','error':str(e)}
 (dest/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(name,r,flush=True);return name,r
if __name__=='__main__':
 tasks=[lambda:isolate(False),lambda:isolate(True)]+[lambda u=u:combined('fs',125,u) for u in [20,30,40,60]]
 results=dict(ThreadPoolExecutor(max_workers=4).map(lambda f:f(),tasks))
 (root/'simulations/buffer-hardening.json').write_text(json.dumps({'initial_tests':results},indent=2)+'\n')
