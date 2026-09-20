"""Combined half-step/tighter-tolerance screen on both complete-corner placements.
Exactly two cases, maximum 1200 s/case; no automatic retries or model promotion.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,re,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'checkpoints/clamp-review/package';S=R/'build/corner-scaled-candidate';B=R/'build/corner-scaled-refinement';B.mkdir(exist_ok=True)
assert json.loads((S/'result.json').read_text())['both_complete']
def run(mode):
 src=S/mode;d=B/mode;d.mkdir(exist_ok=True);model=(src/'model.spice').read_bytes();(d/'model.spice').write_bytes(model)
 text=(src/'test.spice').read_text().replace('tran 50n 153u 0 50n uic','tran 25n 153u 0 25n uic').replace('reltol=1e-6 abstol=1e-12','reltol=1e-7 abstol=1e-14');(d/'test.spice').write_text(text);(d/'tran.dat').unlink(missing_ok=True);start=time.monotonic();err=None;comparison=None
 try:
  with (d/'ngspice.log').open('w') as f:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=1200,env={**os.environ,'SPICE_USERINIT_DIR':str(P/'init')})
  log=(d/'ngspice.log').read_text();assert p.returncode==0 and not re.search(r'aborted|timestep too small|^Error',log,re.I|re.M)
  a=np.loadtxt(src/'tran.dat',skiprows=1);b=np.loadtxt(d/'tran.dat',skiprows=1);assert np.isfinite(b).all() and b[-1,0]>=152.99e-6
  t=np.unique(np.r_[a[:,0],b[:,0]]);delta=np.array([abs(np.interp(t,a[:,0],a[:,j])-np.interp(t,b[:,0],b[:,j])) for j in range(1,4)]);post=t>=150e-6
  comparison=dict(full_trace_max_by_column=np.max(delta,axis=1).tolist(),post_startup_max_by_column=np.max(delta[:,post],axis=1).tolist(),full_trace_rail_screen_pass=bool(np.max(delta[:2])<1e-5),post_startup_rail_screen_pass=bool(np.max(delta[:2,post])<1e-5),current_scope='Source-current differences recorded; not a full multiport-equivalence check')
 except Exception as e:
  err=repr(e)
  if (d/'ngspice.log').exists():
   failures=re.findall(r'^.*(?:Timestep too small|trouble with node|aborted).*$',(d/'ngspice.log').read_text(),re.I|re.M)
   if failures: err+=': '+'; '.join(failures)
 row=dict(mode=mode,completed=err is None,error=err,seconds=time.monotonic()-start,timeout_s=1200,comparison=comparison,model_sha256=hashlib.sha256(model).hexdigest(),deck_sha256=hashlib.sha256(text.encode()).hexdigest());print(json.dumps(row),flush=True);return row
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,['nominal','remote']))
r=dict(runs=rows,voltage_screen_pass=all(x['completed'] and x['comparison']['full_trace_rail_screen_pass'] and x['comparison']['post_startup_rail_screen_pass'] for x in rows),accepted_full_chip_fix=False,scope='Combined maximum timestep 50→25 ns and reltol/abstol refinement; two corner placements, typical/27 C only',stop_rule='Two runs only; any failed/incomplete gate prevents promotion.')
(B/'result.json').write_text(json.dumps(r,indent=2)+'\n');(R/'simulations/corner-scaled-refinement.json').write_text(json.dumps(r,indent=2)+'\n')
