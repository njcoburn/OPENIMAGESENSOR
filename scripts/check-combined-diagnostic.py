"""LVS and 80 short corner transients on freshly extracted diagnostic blocks."""
from pathlib import Path
import subprocess,json,concurrent.futures
import numpy as np
R=Path(__file__).resolve().parents[1]; B=R/'build/combined-patch'
results={'scope':'Fresh buffer and readout extraction; reduced fill; readout BIAS capacitance approximation retained','lvs':[],'runs':[]}
for block,ref,cell in [('buffer','circuits/output-buffer.spice','output_buffer'),('readout','layout/column_readout.spice','column_readout')]:
 for mode in ['baseline','combined']:
  d=B/block/mode
  p=subprocess.run(['netgen','-batch','lvs',f'{d}/{block}_devices.spice {block}_devices',f'{R/ref} {cell}','/foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl',str(d/'lvs.log')],capture_output=True,text=True,timeout=120)
  (d/'netgen.log').write_text(p.stdout+p.stderr)
  results['lvs'].append({'block':block,'mode':mode,'pass':p.returncode==0 and 'Circuits match uniquely.' in (d/'lvs.log').read_text()})
def run(job):
 block,mode,corner,temp=job;d=B/block/mode; w=d/f'{corner}_{temp}';w.mkdir(exist_ok=True)
 model=d/f'{block}_reduced.spice'
 ports=next(x.split()[2:] for x in model.read_text().splitlines() if x.lower().startswith('.subckt'))
 mapping={'GND':'0','VDD':'vdd'}
 pins=' '.join(mapping.get(x,x) for x in ports)
 if block=='buffer':
  fixture='Iref PREF 0 40u\nVin IN 0 PWL(0 .7 2u .7 2.1u .9)\nCload BUF 0 100p'
  end=6e-6; samples=[1.9e-6,6e-6];target='BUF'
 else:
  fixture='Iref vdd BIAS .5u\nV0 COL0 0 .5\nV1 COL1 0 .8\nV2 COL2 0 1.1\nCload OUT 0 30p\n'+ '\n'.join(f'Vs{i} SEL{i} 0 PULSE(0 3.3 {2+5*i}u 10n 10n 4u 30u)' for i in range(3))
  end=16e-6;samples=[5e-6,10e-6,15e-6];target='OUT'
 deck=f'''Combined diagnostic {block} {mode} {corner} {temp}
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice {corner}
.include {model}
.options reltol=1e-6 abstol=1e-14 method=gear
.temp {temp}
Vdd vdd 0 3.3
Xdut {pins} {block}_pex
{fixture}
.control
set numdgt=12
set wr_singlescale
set wr_vecnames
tran 10n {end}
wrdata wave.dat v({target})
quit
.endc
.end
'''
 (w/'test.spice').write_text(deck)
 record=dict(block=block,mode=mode,corner=corner,temp=temp)
 try:
  p=subprocess.run(['ngspice','-b','test.spice'],cwd=w,capture_output=True,text=True,timeout=90)
  (w/'ngspice.log').write_text(p.stdout+p.stderr)
  a=np.loadtxt(w/'wave.dat',skiprows=1); valid=bool(p.returncode==0 and np.isfinite(a).all() and a[-1,0]>=end*.999)
  vals=np.interp(samples,a[:,0],a[:,1]);functional=bool(np.all((vals>0)&(vals<3.3)) and np.all(np.diff(vals)>0))
  if block=='readout':functional=bool(np.max(abs(vals-[.5,.8,1.1]))<.01)
  record.update(pass_run=valid and functional,samples_V=vals.tolist())
 except Exception as e:record.update(pass_run=False,error=str(e))
 return record
jobs=[(b,m,c,t) for b in ['buffer','readout'] for m in ['baseline','combined'] for c in ['typical','ff','ss','fs','sf'] for t in [-40,27,85,125]]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for row in pool.map(run,jobs):results['runs'].append(row);print(row,flush=True)
comparisons=[]
for b in ['buffer','readout']:
 for c in ['typical','ff','ss','fs','sf']:
  for t in [-40,27,85,125]:
   pair=[next(x for x in results['runs'] if (x['block'],x['mode'],x['corner'],x['temp'])==(b,m,c,t)) for m in ['baseline','combined']]
   if all(x['pass_run'] for x in pair):
    delta=float(np.max(abs(np.array(pair[0]['samples_V'])-pair[1]['samples_V'])))
    comparisons.append(dict(block=b,corner=c,temp=t,max_sample_delta_V=delta,pass_screen=delta<1e-4))
results['comparisons']=comparisons
(B/'regression.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(x['pass'] for x in results['lvs']), 'LVS failure'
assert all(x['pass_run'] for x in results['runs']), 'Transient failure'
assert len(comparisons)==40 and all(x['pass_screen'] for x in comparisons), 'Comparison failure'
