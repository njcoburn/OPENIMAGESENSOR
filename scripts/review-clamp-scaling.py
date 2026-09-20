"""Bounded audit of ngspice behavioral-capacitor internal scaling; no PDK edits."""
from pathlib import Path
import json,os,subprocess,re,time,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/clamp-model-review';B.mkdir(exist_ok=True)
P=R/'checkpoints/clamp-review/package';model=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice')
expected=json.loads((P/'pdk-provenance.json').read_text())['sha256'];assert hashlib.sha256(model.read_bytes()).hexdigest()==expected
sub='''
* Algebraic rescaling of observed E/C/B expansion; C(v) is unchanged.
.subckt review_cap_nmos_06v0 1 2 c_length=10u c_width=25u dtemp=0
Ehelper helper 0 2 1 1
Chelper helper 0 1p
Bphysical 1 2 I=i(Ehelper)*(cap_nmos_06v0_corner*c_length*c_width*(0.001107+0.00107*tanh(6.25*v(1,2)-4.1875))/1p)
.ends review_cap_nmos_06v0
'''
def altered(s):
 s=re.sub(r'(?im)^(X[^\n]*?)\bcap_nmos_06v0\b',r'\1review_cap_nmos_06v0',s)
 return s.replace('.control',sub+'\n.control',1)
def run(name,s):
 d=B/name;d.mkdir(exist_ok=True);(d/'test.spice').write_text(s);(d/'tran.dat').unlink(missing_ok=True);start=time.monotonic();err=None
 try:
  with (d/'ngspice.log').open('w') as log:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=120,env={**os.environ,'SPICE_USERINIT_DIR':str(P/'init')})
  text=(d/'ngspice.log').read_text();assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',text,re.I|re.M)
  data=np.loadtxt(d/'tran.dat',skiprows=1);assert np.isfinite(data).all() and data[-1,0]>=152.99e-6
 except Exception as e:err=repr(e)
 out=dict(case=name,completed=err is None,error=err,seconds=time.monotonic()-start,deck_sha256=hashlib.sha256(s.encode()).hexdigest());print(out,flush=True);return out
s=(P/'cases/capacitor-control/test.spice').read_text();runs=[run('control-original',s),run('control-scaled',altered(s))];comparison=None
if all(x['completed'] for x in runs):
 a=np.loadtxt(B/'control-original/tran.dat',skiprows=1);b=np.loadtxt(B/'control-scaled/tran.dat',skiprows=1);t=np.unique(np.r_[a[:,0],b[:,0]])
 delta=[float(np.max(np.abs(np.interp(t,a[:,0],a[:,j])-np.interp(t,b[:,0],b[:,j])))) for j in range(1,a.shape[1])]
 comparison={'max_absolute_column_differences':delta,'header':(B/'control-original/tran.dat').read_text().splitlines()[0]}
 # Control records terminal voltage and source current; require agreement before clamp test.
 if delta[0]<1e-5 and delta[1]<1e-10:
  s=(P/'cases/klu-trap-50ns/test.spice').read_text();runs.append(run('clamp-scaled-50ns',altered(s)))
result=dict(hypothesis='Rescale ngspice internal helper capacitance 1 F to 1 pF and inversely rescale behavioral current gain; unchanged terminal C(V).',runs=runs,control_comparison=comparison,accepted_full_chip_fix=False,scope='One standalone pair and at most one 50 ns clamp diagnostic; no solver/tolerance sweep, no foundry file edit; 27 C typical only.')
(B/'review.json').write_text(json.dumps(result,indent=2)+'\n')
