"""Half-step numerical refinement of the already completed placement fixtures."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,re
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced'
def run(job):
 case,mode=job;src=B/case/mode;d=B/case/f'refine-{mode}';d.mkdir(exist_ok=True);s=(src/'test.spice').read_text().replace('.include model.spice',f'.include ../{mode}/model.spice').replace('tran 1n 3u 0 1n','tran .5n 3u 0 .5n');s=s[:s.index('ac dec')]+s[s.index('tran .5n'):];(d/'test.spice').write_text(s)
 with (d/'ngspice.log').open('w') as log:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 text=(d/'ngspice.log').read_text();assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',text,re.M|re.I)
 a=np.loadtxt(src/'tran.dat',skiprows=1,ndmin=2);b=np.loadtxt(d/'tran.dat',skiprows=1,ndmin=2);assert b[-1,0]>=2.999e-6 and np.isfinite(b).all();t=np.unique(np.r_[a[:,0],b[:,0]]);error=max(float(np.max(abs(np.interp(t,a[:,0],a[:,i])-np.interp(t,b[:,0],b[:,i])))) for i in [1,2]);return {'case':case,'mode':mode,'max_timestep_change_V':error,'completed':True}
jobs=[(c,m) for c in ['fill10-full','fill10-metal','corner-metal'] for m in ['nominal','remote']]
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,jobs))
comparisons={}
for case in ['fill10-full','fill10-metal','corner-metal']:
 a,b=[np.loadtxt(B/case/f'refine-{m}'/'tran.dat',skiprows=1) for m in ['nominal','remote']];t=np.unique(np.r_[a[:,0],b[:,0]]);delta=max(float(np.max(abs(np.interp(t,a[:,0],a[:,i])-np.interp(t,b[:,0],b[:,i])))) for i in [1,2]);comparisons[case]={'refined_max_placement_difference_V':delta}
(B/'refinement.json').write_text(json.dumps({'runs':rows,'comparisons':comparisons},indent=2)+'\n');print(json.dumps({'runs':rows,'comparisons':comparisons},indent=2))
