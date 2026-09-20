"""Two fixed refinement checks of the newly completed isolated-clamp candidate.
No automatic retry or model promotion. Runtime budget 300 s/case allows twice
as many maximum-step intervals as the observed 104 s / 50 ns baseline.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,re,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'checkpoints/clamp-review/package';D=R/'build/clamp-scaled-refinement';D.mkdir(exist_ok=True)
source=R/'build/clamp-control-breakpoints/clamp-scaled-50ns';base=np.loadtxt(source/'tran.dat',skiprows=1)
assert base[-1,0]>=152.99e-6
s=(source/'test.spice').read_text();assert 'tran 50n 153u 0 50n uic' in s
model=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice');assert hashlib.sha256(model.read_bytes()).hexdigest()==json.loads((P/'pdk-provenance.json').read_text())['sha256']
def run(strict):
 name='25ns-strict' if strict else '25ns';d=D/name;d.mkdir(exist_ok=True);text=s.replace('tran 50n 153u 0 50n uic','tran 25n 153u 0 25n uic')
 if strict:text=text.replace('.control','.options reltol=1e-7 abstol=1e-14\n.control',1)
 (d/'test.spice').write_text(text);(d/'tran.dat').unlink(missing_ok=True);start=time.monotonic();err=None;comparison=None
 try:
  with (d/'ngspice.log').open('w') as f:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=300,env={**os.environ,'SPICE_USERINIT_DIR':str(P/'init')})
  log=(d/'ngspice.log').read_text();assert p.returncode==0 and not re.search(r'aborted|timestep too small|^Error',log,re.I|re.M)
  a=np.loadtxt(d/'tran.dat',skiprows=1);assert np.isfinite(a).all() and a[-1,0]>=152.99e-6
  t=np.unique(np.r_[a[:,0],base[:,0]]);delta=np.array([abs(np.interp(t,a[:,0],a[:,j])-np.interp(t,base[:,0],base[:,j])) for j in range(1,5)])
  post=t>=150e-6;comparison=dict(full_trace_max_by_column=np.max(delta,axis=1).tolist(),post_startup_max_by_column=np.max(delta[:,post],axis=1).tolist(),rail_refinement_pass=bool(np.max(delta[:2,post])<1e-5),moscap_refinement_pass=bool(np.max(delta[2,post])<1e-5),scope='150–153 us including load edges; full-trace differences retained separately')
 except Exception as e:err=repr(e)
 row=dict(case=name,completed=err is None,error=err,seconds=time.monotonic()-start,timeout_s=300,comparison=comparison,deck_sha256=hashlib.sha256(text.encode()).hexdigest());print(json.dumps(row),flush=True);return row
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,[False,True]))
r=dict(runs=rows,base_deck_sha256=hashlib.sha256(s.encode()).hexdigest(),base_wave_sha256=hashlib.sha256((source/'tran.dat').read_bytes()).hexdigest(),accepted_full_chip_fix=False,refinement_screen_pass=all(x['completed'] and x['comparison']['rail_refinement_pass'] and x['comparison']['moscap_refinement_pass'] for x in rows),stop_rule='Exactly these two refinement runs. Any incomplete or failed comparison blocks promotion; no retries.')
(D/'result.json').write_text(json.dumps(r,indent=2)+'\n');(R/'simulations/clamp-scaled-refinement.json').write_text(json.dumps(r,indent=2)+'\n')
