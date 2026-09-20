"""Check measured MOS-cap validity and report nominal final-chip scan diagnostics."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('run');args=p.parse_args();D=R/'build/functional-camera'/args.run
r=json.loads((D/'result.json').read_text());assert r['completed'] and r['stage']!='op'
a=np.loadtxt(D/'tran.dat',skiprows=1);t=a[:,0];v=a[:,1:]
meta=json.loads((R/'build/functional-pad-model/frozen-model.json').read_text());info=json.loads((R/'build/functional-pad-model/caps.json').read_text())
assert hashlib.sha256((D/'model.spice').read_bytes()).hexdigest()==meta['frozen_sha256']
op=json.loads((R/'build/functional-camera/op-100ns/result.json').read_text())
assert hashlib.sha256((R/'build/functional-camera/op-100ns/result.json').read_bytes()).hexdigest()==meta['op_sha256']
cv=lambda x:.001107+.00107*np.tanh(6.25*x-4.1875)
cap_checks=[]
for j,pair in enumerate(info['pairs']):
 x=v[:,17+j];b=op['summary']['last_values'][17+j]
 cap_checks.append(dict(pair=pair,min_V=float(x.min()),max_V=float(x.max()),bias_V=b,max_relative_C_error=float(np.max(abs(cv(x)/cv(b)-1)))))
samples=[];pattern=np.array([[0,80,240],[240,0,80],[80,240,0]])
nframes=3 if r['stage']=='three-frames' else 1
for f in range(nframes):
 for row in range(3):
  for col in range(3):
   tm=.0012+f*.003+.000985+row*.001+col*18e-6
   assert t[0]<=tm<=t[-1]
   z=np.array([np.interp(tm,t,v[:,j]) for j in range(v.shape[1])])
   samples.append(dict(frame=f,row=row,col=col,time_s=tm,light_pA=int(pattern[row,col]),sense_V=float(z[8+3*row+col]),mux_V=float(z[3]),adc_V=float(z[5]),hold_V=float(z[6]),hold_minus_adc_mV=float(1000*(z[6]-z[5]))))
mat=np.array([s['hold_V'] for s in samples]).reshape(nframes,3,3)
order=all(np.all(np.diff(mat[f,row,np.argsort(pattern[row])])<0) for f in range(nframes) for row in range(3))
result=dict(run=args.run,scope=r['scope'],completed=True,accepted_full_chip=False,cap_checks=cap_checks,cap_range_pass=all(c['max_relative_C_error']<1e-6 for c in cap_checks),cap_relative_error_limit=1e-6,stock_op_max_voltage_difference_V=float(np.max(abs(v[0,:7]-np.array(op['summary']['last_values'][:7])))),samples=samples,brightness_order_ok=bool(order),max_hold_minus_adc_mV=max(abs(s['hold_minus_adc_mV']) for s in samples),note='Hold-minus-ADC is an acquisition diagnostic, not DC-transfer settling error or ADC accuracy.',step_ns=r['step_ns'])
(D/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
fig,axs=plt.subplots(2,1,figsize=(11,7),layout='constrained')
axs[0].plot(t*1e3,v[:,5],label='ADC input');axs[0].plot(t*1e3,v[:,6],label='Sample/hold',alpha=.7)
axs[0].scatter([s['time_s']*1e3 for s in samples],[s['hold_V'] for s in samples],color='black',s=15,label='Nine samples/frame');axs[0].set(xlabel='Time (ms)',ylabel='Voltage (V)');axs[0].legend()
for j,c in enumerate(cap_checks):axs[1].plot(t*1e3,v[:,17+j],alpha=.6)
axs[1].set(xlabel='Time (ms)',ylabel='MOS-cap terminal voltage (V)')
fig.suptitle(f'Final filled 3×3 — nominal functional candidate ({r["step_ns"]:g} ns maximum step)\nBias-frozen MOS capacitance; startup and full qualification remain open')
fig.savefig(D/'response.png',dpi=150);plt.close(fig)
print(json.dumps({k:result[k] for k in ['run','cap_range_pass','brightness_order_ok','max_hold_minus_adc_mV','stock_op_max_voltage_difference_V']}))
