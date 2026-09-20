"""Final bounded solver-only comparison: two existing 50 ns failing decks.
No automatic retries or parameter search. Export a review package afterward.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,os,json,re,hashlib,time
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/bounded-solver';B.mkdir(exist_ok=True)
def run(name):
 source=R/'build/moscap-branch'/name/'test.spice';original=source.read_text()
 assert original.count('set klu\n')==1
 deck=original.replace('set klu\n','unset klu\n')
 d=B/name;d.mkdir(exist_ok=True);(d/'test.spice').write_text(deck)
 # A stale waveform can never count as a completed rerun.
 (d/'tran.dat').unlink(missing_ok=True)
 row=dict(case=name,changed='KLU to SPARSE only',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),completed=False,timeout_s=120)
 start=time.monotonic()
 try:
  with (d/'ngspice.log').open('w') as f:
   p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=120,env={**os.environ,'SPICE_USERINIT_DIR':str(R/'checkpoints/pad-closure/ngspice-init')})
  log=(d/'ngspice.log').read_text();row['errors']=[x for x in log.splitlines() if re.search('aborted|timestep too small|^Error',x,re.I)]
  assert 'Using SPARSE' in log,'SPARSE solver selection not confirmed'
  assert p.returncode==0 and not row['errors']
  a=np.loadtxt(d/'tran.dat',skiprows=1,ndmin=2)
  assert np.isfinite(a).all() and len(a)>1 and a[-1,0]>=152.99e-6
  row.update(completed=True,points=len(a),last_time_s=float(a[-1,0]))
 except Exception as e:row['failure']=str(e)
 row['runtime_s']=time.monotonic()-start
 print(row,flush=True);return row
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,['trap-halfstep','trap-halfstep-strict']))
result=dict(runs=rows,stop_rule='Exactly these two solver-only trials; no automatic retries. Any incomplete case stops this investigation and triggers expert-review preparation.',accepted=False)
if all(x['completed'] for x in rows):
 a,b=[np.loadtxt(B/n/'tran.dat',skiprows=1,ndmin=2) for n in ['trap-halfstep','trap-halfstep-strict']]
 t=np.unique(np.r_[a[a[:,0]>=150e-6,0],b[b[:,0]>=150e-6,0]])
 error=max(float(np.max(abs(np.interp(t,a[:,0],a[:,i])-np.interp(t,b[:,0],b[:,i])))) for i in [1,2])
 result.update(max_post_startup_rail_difference_V=error,numerical_screen_pass=error<10e-6)
 result['next_gate']='Independent timestep comparison still required before any full-corner promotion.'
else:result['next_gate']='Stop local solver experimentation; send prepared reproducer for expert review when explicitly authorized.'
(B/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
