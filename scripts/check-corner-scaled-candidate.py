"""Two complete corner-coupon placement tests after isolated-clamp refinement.
Preserve all extracted R/C and device terminals; candidate MOS-cap helper only.
Fixed 600 s watchdog/case; no retries and no full-chip promotion.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,re,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'checkpoints/clamp-review/package';D=R/'build/corner-scaled-candidate';D.mkdir(exist_ok=True)
assert json.loads((R/'simulations/clamp-scaled-refinement.json').read_text())['refinement_screen_pass']
source=R/'build/clamp-control-breakpoints/clamp-scaled-50ns/test.spice';s=source.read_text();sub=s[s.index('.subckt review_cap_nmos_06v0'):s.index('.ends review_cap_nmos_06v0')+len('.ends review_cap_nmos_06v0')]
model=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice');assert hashlib.sha256(model.read_bytes()).hexdigest()==json.loads((P/'pdk-provenance.json').read_text())['sha256']
def run(mode):
 d=D/mode;d.mkdir(exist_ok=True);src=R/'build/charge-reduced/corner-full'/('practical-'+mode)/'model.spice';raw=src.read_text();candidate,n=re.subn(r'(?im)^(X[^\n]*?)\bcap_nmos_06v0\b',r'\1review_cap_nmos_06v0',raw);assert n>0
 # Every non-MOS-cap record and every retained MOS-cap terminal/value is unchanged.
 assert candidate.replace('review_cap_nmos_06v0','cap_nmos_06v0')==raw
 (d/'model.spice').write_text(candidate+'\n'+sub+'\n')
 base=(R/'build/charge-reduced/corner-full'/('startup-'+mode)/'test.spice').read_text();text=base.replace(f'.include ../practical-{mode}/model.spice','.include model.spice').replace('method=gear','method=trap').replace('tran 100n 153u 0 100n uic','tran 50n 153u 0 50n uic').replace('set numdgt=12','set numdgt=15').replace('wrdata tran.dat v(vb,gb) v(db,dg)','wrdata tran.dat v(vb,gb) v(db,dg) i(Vsrc)')
 (d/'test.spice').write_text(text);(d/'tran.dat').unlink(missing_ok=True);start=time.monotonic();err=None;stats=None
 try:
  with (d/'ngspice.log').open('w') as f:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=600,env={**os.environ,'SPICE_USERINIT_DIR':str(P/'init')})
  log=(d/'ngspice.log').read_text();assert p.returncode==0 and not re.search(r'aborted|timestep too small|^Error',log,re.I|re.M)
  z=np.loadtxt(d/'tran.dat',skiprows=1);assert np.isfinite(z).all() and z[-1,0]>=152.99e-6
  stats=dict(rows=len(z),end_s=float(z[-1,0]),last_values=z[-1,1:].tolist())
 except Exception as e:err=repr(e)
 row=dict(mode=mode,completed=err is None,error=err,seconds=time.monotonic()-start,timeout_s=600,stats=stats,replaced_moscap_instances=n,source_model_sha256=hashlib.sha256(raw.encode()).hexdigest(),candidate_model_sha256=hashlib.sha256((d/'model.spice').read_bytes()).hexdigest(),deck_sha256=hashlib.sha256(text.encode()).hexdigest());print(json.dumps(row),flush=True);return row
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,['nominal','remote']))
r=dict(runs=rows,both_complete=all(x['completed'] for x in rows),accepted_full_chip_fix=False,scope='Complete extracted corner coupon, two lumped-cap placements, typical/27 C; not complete chip; refinement required if complete',stop_rule='Exactly two placement runs, 600 s each; no retries.')
(D/'result.json').write_text(json.dumps(r,indent=2)+'\n');(R/'simulations/corner-scaled-candidate.json').write_text(json.dumps(r,indent=2)+'\n')
