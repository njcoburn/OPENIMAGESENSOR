"""Step 1: nominal transistor column-bias sweep on the saved extracted array."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,re,json,hashlib
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];out=root/'build/column-bias';out.mkdir(parents=True,exist_ok=True)
net=root/'simulations/extracted-20um/rc-filled/array_reduced.spice'
manifest=json.loads((net.parent.parent/'manifest.json').read_text())
assert hashlib.sha256(net.read_bytes()).hexdigest()==manifest['rc-filled/array_reduced.spice']
base=(root/'circuits/column-bias-template.spice').read_text()
base=base.replace('/foss/designs/build/parasitics/rc-filled/array_reduced.spice',str(net))
# 2um x 2um long-channel mirror; explicit assumed diffusion geometry, not extracted.
mos='nfet_03v3 w=2u l=2u ad=0.88p as=0.88p pd=4.88u ps=4.88u'
def simulate(ua):
 name='resistor' if ua is None else f'mirror_{ua:g}uA';dest=out/name;dest.mkdir(exist_ok=True);s=base
 if ua is not None:
  circuit=f'Iref VDD BIAS {ua}u\nXref BIAS BIAS 0 0 {mos}\n'
  for c in range(3):
   s=re.sub(rf'(?m)^Rload{c} .*$',f'Vmeasure{c} COL{c} drain{c} 0\nXbias{c} drain{c} BIAS 0 0 {mos}',s)
  s=s.replace('.control',circuit+'.control')
 extra=' i(Vdd)'+(' v(BIAS) i(Vmeasure0) i(Vmeasure1) i(Vmeasure2)' if ua is not None else '')
 s=re.sub(r'(?m)^wrdata .*$',f'wrdata {dest}/wave.txt v(ROW0) v(ROW1) v(ROW2) v(COL0) v(COL1) v(COL2)'+extra,s)
 (dest/'testbench.spice').write_text(s)
 r=subprocess.run(['ngspice','-b',str(dest/'testbench.spice')],capture_output=True,text=True);(dest/'run.log').write_text(r.stdout+r.stderr)
 assert r.returncode==0 and not re.search('aborted|timestep too small|^Error',r.stdout+r.stderr,re.I|re.M),name
 d=np.loadtxt(dest/'wave.txt',skiprows=1);assert np.isfinite(d).all() and d[-1,0]>=.00905
 at=lambda t,col:float(np.interp(t,d[:,0],d[:,col]))
 samples=np.array([[at(.00702+r*.001,4+c) for c in range(3)] for r in range(3)])
 pattern=np.array([[0,80,240],[240,0,80],[80,240,0]])
 ordered=all(np.all(np.diff(samples[r,np.argsort(pattern[r])])<0) for r in range(3))
 assert ordered, name
 mask=(d[:,0]>=.006)&(d[:,0]<=.009)
 result={'reference_uA':ua,'samples_V':samples.tolist(),'row0_signal_mV':((samples[0,0]-samples[0])*1000).tolist(),'brightness_order_ok':bool(ordered),'min_column_V':float(d[:,4:7].min()),'late_window_change_mV':max(abs(at(.00702+r*.001,4+c)-at(.006995+r*.001,4+c))*1000 for r in range(3) for c in range(3)),'dark_late_window_change_mV':max(abs(at(.00702+r*.001,4+r)-at(.006995+r*.001,4+r))*1000 for r in range(3)),'average_VDD_power_uW':float(-3.3*np.trapezoid(d[mask,7],d[mask,0])/(d[mask,0][-1]-d[mask,0][0])*1e6),'testbench_sha256':hashlib.sha256(s.encode()).hexdigest()}
 if ua is not None:
  currents=[at(.00702+r*.001,9+c)*1e6 for r in range(3) for c in range(3)]
  result.update(sampled_sink_current_range_uA=[min(currents),max(currents)],bias_V=at(.00702,8))
 print(name,json.dumps(result),flush=True)
 return name,result,d
runs=list(ThreadPoolExecutor(max_workers=4).map(simulate,[None,.25,.5,1.]))
fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for name,r,d in runs:
 axes[0].plot([0,80,240],r['row0_signal_mV'],'o-',label=name)
 mask=(d[:,0]>=.006965)&(d[:,0]<=.00703)
 axes[1].plot((d[mask,0]-.00697)*1e6,d[mask,4],label=name)
axes[0].set(xlabel='Assumed photocurrent (pA)',ylabel='Dark-subtracted signal (mV)',title='Third-frame row 0')
axes[1].set(xlabel='Time after row selection (µs)',ylabel='Dark column voltage (V)',title='Readout settling, 1 pF external load')
for a in axes:a.grid(alpha=.2);a.legend()
fig.savefig(root/'docs/assets/column-bias.png',dpi=150)
summary={'scope':'Typical corner, 27 C; extracted array with schematic-only bias devices; ideal reference current; no mismatch/noise or pad/ADC loads. Power includes VDD and ideal reference branch, excludes reset/row drivers. Late-window change includes continuing integration, not a step-settling specification.','array_sha256':hashlib.sha256(net.read_bytes()).hexdigest(),'cases':{n:r for n,r,d in runs}}
(root/'simulations/column-bias.json').write_text(json.dumps(summary,indent=2)+'\n')
