"""Start the nonlinear corner from zero supply, then compare a settled load pulse."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,re,os
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced/corner-full'
def run(mode):
 d=B/f'startup-{mode}';d.mkdir(exist_ok=True)
 s=(B/f'practical-{mode}'/'test.spice').read_text().replace('.include model.spice',f'.include ../practical-{mode}/model.spice').replace('Vsrc src 0 DC 3.3 AC 1','Vsrc src 0 PWL(0 0 100u 3.3)').replace('1m 1u 1n','1m 151u 1n').replace('reltol=5e-5','reltol=1e-6')
 start=s.index('ac dec');end=s.index('tran 1n');s=s[:start]+s[end:];s=s.replace('tran 1n 3u 0 1n','tran 100n 153u 0 100n uic')
 (d/'test.spice').write_text(s);row={'mode':mode,'scope':'100us supply ramp; load pulse at 151us; zero-charge startup; 100ns maximum step with adaptive steps at 1ns edges'}
 try:
  with (d/'ngspice.log').open('w') as log:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=600,env={**os.environ,'SPICE_USERINIT_DIR':str(R/'checkpoints/pad-closure/ngspice-init')})
  log=(d/'ngspice.log').read_text();errors=[x for x in log.splitlines() if re.search('aborted|timestep too small|^Error',x,re.I)]
  assert p.returncode==0 and not errors,errors[-3:]
  a=np.loadtxt(d/'tran.dat',skiprows=1,ndmin=2);assert np.isfinite(a).all() and a[-1,0]>=152.99e-6,(a[-1,0],a.shape)
  row.update(completed=True,points=len(a),preload_V=[float(np.interp(150e-6,a[:,0],a[:,i])) for i in [1,2]])
 except Exception as e:row.update(completed=False,error=str(e))
 print(row,flush=True);return row
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,['nominal','remote']))
result={'runs':rows}
if all(x['completed'] for x in rows):
 a,b=[np.loadtxt(B/f'startup-{m}'/'tran.dat',skiprows=1,ndmin=2) for m in ['nominal','remote']];t=np.unique(np.r_[a[a[:,0]>=150e-6,0],b[b[:,0]>=150e-6,0]]);dif=np.stack([np.interp(t,a[:,0],a[:,i])-np.interp(t,b[:,0],b[:,i]) for i in [1,2]])
 result['max_post_startup_difference_V']=float(np.max(abs(dif)));result['load_sample_difference_V']=[float(np.interp(151.5e-6,a[:,0],a[:,i])-np.interp(151.5e-6,b[:,0],b[:,i])) for i in [1,2]]
(B/'startup-placement.json').write_text(json.dumps(result,indent=2)+'\n')
