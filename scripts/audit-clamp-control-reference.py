"""Independent terminal-ODE audit of saved controls; runs no SPICE simulations."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/clamp-model-review';O=R/'checkpoints/clamp-control-reference';O.mkdir(exist_ok=True)
# Values confirmed by the archived expanded ngspice listing: typical corner = 1.
AREA=25e-6*10e-6;RES=1000.;END=100.;STOP=153.;SLOPE=.033
C=lambda v:AREA*(.001107+.00107*np.tanh(6.25*v-4.1875))
def solve(rtol,atol):
 # State is the resistor drop, avoiding subtraction of nearly equal 3.3 V nodes.
 def ramp(t,z):return [SLOPE-1e-6*z[0]/(RES*C(SLOPE*t-z[0]))]
 a=solve_ivp(ramp,(0,END),[0.],method='Radau',rtol=rtol,atol=atol,dense_output=True)
 def hold(t,z):return [-1e-6*z[0]/(RES*C(3.3-z[0]))]
 b=solve_ivp(hold,(END,STOP),a.y[:,-1],method='Radau',rtol=rtol,atol=atol,dense_output=True)
 assert a.success and b.success
 def sample(t):
  t=np.asarray(t)*1e6;drop=np.empty_like(t);mask=t<=END
  drop[mask]=a.sol(t[mask])[0];drop[~mask]=b.sol(t[~mask])[0]
  return np.minimum(t*SLOPE,3.3)-drop,-drop/RES
 return sample,dict(rtol=rtol,atol_V=atol,ramp_steps=len(a.t),hold_steps=len(b.t))
f,meta=solve(1e-8,1e-14);g,refined=solve(1e-10,1e-16)
data={n:np.loadtxt(B/n/'tran.dat',skiprows=1) for n in ['control-original','control-scaled']}
for a in data.values():assert np.isfinite(a).all() and np.all(np.diff(a[:,0])>0)
t=np.unique(np.r_[*[a[:,0] for a in data.values()],np.linspace(99.99e-6,100.06e-6,2001)])
v,i=f(t);vv,ii=g(t)
result=dict(scope='Saved isolated 1 kohm / nonlinear MOS capacitor control only; no clamp or full-chip qualification',equation='C(Vg) dVg/dt=(Vs-Vg)/1000; C(V)=25u*10u*(0.001107+0.00107*tanh(6.25V-4.1875)); Vs=min(33000*t,3.3)',reference=meta,refined_reference=refined,reference_refinement_max_V=float(np.max(abs(v-vv))),reference_refinement_max_A=float(np.max(abs(i-ii))),high_voltage_time_constant_s=float(RES*C(3.3)),cases={})
assert result['reference_refinement_max_A']<1e-12 and result['reference_refinement_max_V']<1e-8
for name,a in data.items():
 vr,ir=g(a[:,0]);delta=abs(a[:,2]-ir);k=int(np.argmax(delta));away=abs(a[:,0]-100e-6)>1e-6
 result['cases'][name]=dict(rows=len(a),max_native_current_error_A=float(delta[k]),max_error_time_s=float(a[k,0]),max_native_voltage_error_V=float(np.max(abs(a[:,1]-vr))),max_current_error_away_from_ramp_stop_A=float(np.max(delta[away])),wave_sha256=hashlib.sha256((B/name/'tran.dat').read_bytes()).hexdigest(),deck_sha256=hashlib.sha256((B/name/'test.spice').read_bytes()).hexdigest())
# Retain original pairwise union-grid comparison; no edge exclusion used for acceptance.
a,b=data.values();tt=np.unique(np.r_[a[:,0],b[:,0]]);dd=abs(np.interp(tt,a[:,0],a[:,2])-np.interp(tt,b[:,0],b[:,2]));k=int(np.argmax(dd))
result['saved_pairwise_comparison']=dict(max_A=float(dd[k]),time_s=float(tt[k]),unchanged_limit_A=1e-10,passes=bool(dd[k]<1e-10))
result['accepted_fix']=False
(O/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(R/'simulations/clamp-control-reference.json').write_text(json.dumps(result,indent=2)+'\n')
fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for name,a in data.items():
 axs[0].plot(a[:,0]*1e6,-a[:,2]*1e9,label=name.replace('control-',''),alpha=.8)
 mask=(a[:,0]>=99.99e-6)&(a[:,0]<=100.06e-6)
 axs[1].plot((a[mask,0]-100e-6)*1e9,-a[mask,2]*1e9,'o-',label=name.replace('control-',''),markersize=4)
zz=np.linspace(99.99e-6,100.06e-6,2001);_,zi=g(zz);axs[1].plot((zz-100e-6)*1e9,-zi*1e9,'k--',label='Independent terminal ODE')
axs[0].set(xlabel='Time (µs)',ylabel='Capacitor current (nA)',title='Saved standalone controls')
axs[1].set(xlabel='Time after ramp stops (ns)',ylabel='Capacitor current (nA)',title='Native saved points and refined reference')
for ax in axs:ax.grid(alpha=.2);ax.legend()
fig.suptitle('Diagnostic only — original equivalence gate still fails; full chip remains unqualified')
fig.savefig(R/'docs/assets/clamp-control-reference.png',dpi=160)
print(json.dumps(result,indent=2))
