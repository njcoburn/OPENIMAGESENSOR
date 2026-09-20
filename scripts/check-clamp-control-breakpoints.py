"""Bounded hypothesis test: resolve ramp-stop transient without changing its waveform.
Exactly two matched resolutions (50/25 ps), then at most one gated clamp run.
No retry, tolerance sweep, PDK edit or full-chip qualification claim.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess,time
import numpy as np
from scipy.integrate import solve_ivp
R=Path(__file__).resolve().parents[1];old=R/'build/clamp-model-review';B=R/'build/clamp-control-breakpoints';B.mkdir(exist_ok=True)
P=R/'checkpoints/clamp-review/package';model=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice')
assert hashlib.sha256(model.read_bytes()).hexdigest()==json.loads((P/'pdk-provenance.json').read_text())['sha256']
C=lambda v:25e-6*10e-6*(.001107+.00107*np.tanh(6.25*v-4.1875))
a=solve_ivp(lambda t,z:[.033-1e-6*z[0]/(1000*C(.033*t-z[0]))],(0,100),[0.],method='Radau',rtol=1e-10,atol=1e-16,dense_output=True)
b=solve_ivp(lambda t,z:[-1e-6*z[0]/(1000*C(3.3-z[0]))],(100,153),a.y[:,-1],method='Radau',rtol=1e-10,atol=1e-16,dense_output=True)
assert a.success and b.success
def ref(t):
 t=np.asarray(t)*1e6;z=np.empty_like(t);m=t<=100;z[m]=a.sol(t[m])[0];z[~m]=b.sol(t[~m])[0];return -z/1000
runs=[];arrays={}
def run(name,s):
 d=B/name;d.mkdir(exist_ok=True);(d/'test.spice').write_text(s);(d/'tran.dat').unlink(missing_ok=True);start=time.monotonic();err=None
 try:
  with (d/'ngspice.log').open('w') as f:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=120,env={**os.environ,'SPICE_USERINIT_DIR':str(P/'init')})
  log=(d/'ngspice.log').read_text();assert p.returncode==0 and not re.search(r'aborted|timestep too small|^Error',log,re.I|re.M)
  z=np.loadtxt(d/'tran.dat',skiprows=1);assert np.isfinite(z).all() and z[-1,0]>=152.99e-6;arrays[name]=z
 except Exception as e:err=repr(e)
 out=dict(case=name,completed=err is None,error=err,seconds=time.monotonic()-start,deck_sha256=hashlib.sha256(s.encode()).hexdigest());runs.append(out);print(out,flush=True)
for ps in [50,25]:
 for kind in ['original','scaled']:
  s=(old/('control-'+kind)/'test.spice').read_text()
  # Integer picoseconds ensure both resolutions include the exact 100 us corner.
  ticks=np.arange(99995000,100030000+ps,ps,dtype=np.int64);tt=np.r_[0.,ticks*1e-12,153e-6];vv=np.minimum(tt*33000,3.3)
  pairs=' '.join(f'{t:.17g} {v:.17g}' for t,v in zip(tt,vv));line='Vsrc drive 0 PWL('+pairs+')'
  s,n=re.subn(r'(?m)^Vsrc drive 0 PWL\(0 0 100u 3.3\)$',line,s);assert n==1
  run(f'{kind}-{ps}ps',s)
comparisons={};passed=all(x['completed'] for x in runs)
if passed:
 for ps in [50,25]:
  x=arrays[f'original-{ps}ps'];y=arrays[f'scaled-{ps}ps'];t=np.unique(np.r_[x[:,0],y[:,0]])
  dv=float(np.max(abs(np.interp(t,x[:,0],x[:,1])-np.interp(t,y[:,0],y[:,1]))));di=float(np.max(abs(np.interp(t,x[:,0],x[:,2])-np.interp(t,y[:,0],y[:,2]))))
  er={k:float(np.max(abs(arrays[f'{k}-{ps}ps'][:,2]-ref(arrays[f'{k}-{ps}ps'][:,0])))) for k in ['original','scaled']}
  comparisons[str(ps)]=dict(max_pair_V=dv,max_pair_A=di,max_native_reference_A=er,passes=dv<1e-5 and di<1e-10 and max(er.values())<1e-10)
  passed &= comparisons[str(ps)]['passes']
 for kind in ['original','scaled']:
  x=arrays[kind+'-50ps'];y=arrays[kind+'-25ps'];t=np.unique(np.r_[x[:,0],y[:,0]]);di=float(np.max(abs(np.interp(t,x[:,0],x[:,2])-np.interp(t,y[:,0],y[:,2]))))
  comparisons[kind+'-refinement']=dict(max_A=di,passes=di<1e-10);passed &= di<1e-10
print('Comparisons',json.dumps(comparisons),flush=True)
if passed:
 # Exact previously proposed scaled model, unchanged 50 ns extracted-clamp deck.
 original=(old/'control-original/test.spice').read_text();scaled=(old/'control-scaled/test.spice').read_text();sub=scaled[scaled.index('.subckt review_cap_nmos_06v0'):scaled.index('.ends review_cap_nmos_06v0')+len('.ends review_cap_nmos_06v0')]
 s=(P/'cases/klu-trap-50ns/test.spice').read_text();s=re.sub(r'(?im)^(X[^\n]*?)\bcap_nmos_06v0\b',r'\1review_cap_nmos_06v0',s);s=s.replace('.control',sub+'\n.control',1);run('clamp-scaled-50ns',s)
result=dict(hypothesis='Native waveform/reference audit found unresolved sub-ns ramp-stop settling. Insert collinear PWL knots at two fixed local resolutions; physical source unchanged.',runs=runs,comparisons=comparisons,control_gate_passed=bool(passed),accepted_full_chip_fix=False,stop_rule='Four controls and at most one gated clamp run; stop after this batch. Full-chip and charge/PVT qualification remain open.')
(B/'result.json').write_text(json.dumps(result,indent=2)+'\n');(R/'simulations/clamp-control-breakpoints.json').write_text(json.dumps(result,indent=2)+'\n')
