"""Check version-comparison controls against independent terminal ODE and charge."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.integrate import solve_ivp
R=Path(__file__).resolve().parents[1];B=R/'build/ngspice-version-comparison'
area=25e-6*10e-6
C=lambda v:area*(.001107+.00107*np.tanh(6.25*v-4.1875))
def solve(rtol,atol):
 a=solve_ivp(lambda t,z:[.033-1e-6*z[0]/(1000*C(.033*t-z[0]))],(0,100),[0.],method='Radau',rtol=rtol,atol=atol,dense_output=True)
 b=solve_ivp(lambda t,z:[-1e-6*z[0]/(1000*C(3.3-z[0]))],(100,153),a.y[:,-1],method='Radau',rtol=rtol,atol=atol,dense_output=True)
 assert a.success and b.success
 def sample(t):
  t=np.asarray(t)*1e6;drop=np.empty_like(t);m=t<=100;drop[m]=a.sol(t[m])[0];drop[~m]=b.sol(t[~m])[0];return np.minimum(t*.033,3.3)-drop,-drop/1000
 return sample
f=solve(1e-8,1e-14);g=solve(1e-10,1e-16);results=[]
def Q(v):return area*(.001107*v+.00107/6.25*np.log(np.cosh(6.25*v-4.1875)))
for version in ['46','47']:
 d=B/'runs'/f'capacitor-control-{version}';r=json.loads((d/'result.json').read_text());assert r['completed'];a=np.loadtxt(d/'tran.dat',skiprows=1);v,i=g(a[:,0]);v0,i0=f(a[:,0]);refinement=float(np.max(abs(i-i0)));assert refinement<1e-12
 charge=float(np.trapezoid(-a[:,2],a[:,0]));expected=float(Q(a[-1,1])-Q(a[0,1]));err=float(np.max(abs(a[:,2]-i)));verr=float(np.max(abs(a[:,1]-v)));qerr=abs(charge-expected)/abs(expected)
 results.append(dict(version=version,reference_refinement_A=refinement,max_native_current_error_A=err,max_native_voltage_error_V=verr,integrated_charge_C=charge,expected_charge_C=expected,charge_relative_error=qerr,pass_screen=err<1e-10 and verr<1e-5 and qerr<1e-5,wave_sha256=hashlib.sha256((d/'tran.dat').read_bytes()).hexdigest()))
r=dict(cases=results,control_screen_pass=all(x['pass_screen'] for x in results),current_limit_A=1e-10,voltage_limit_V=1e-5,charge_relative_limit=1e-5,scope='One 25x10 um typical capacitor at 27 C; resolved ramp stop. Not general model or full-chip qualification.');(B/'control-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
