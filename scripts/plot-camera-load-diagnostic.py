"""Compare retained nominal/heavy-load first-row acquisition waveforms."""
from pathlib import Path
import json,runpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
read=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
nom=R/'build/shared-circuit/three-frame-reset-norton-extended-20260924'
heavy=R/'build/camera-operating-corners/first-frame-20260924/heavy-cap'
fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained',sharex=True)
metrics={}
for root,label,raw in [(nom,'100 pF board / 20 pF sample',nom/'stream.raw'),(heavy,'470 pF board / 100 pF sample',heavy/'transient/stream.raw')]:
 names,d=read(raw);mask=(d[:,0]>=.002173)&(d[:,0]<=.002224);t=d[mask,0]
 for ax,node in zip(axes,['ADCIN','HOLD']):ax.plot((t-.00217)*1e6,d[mask,names.index('v('+node.lower()+')')],label=label)
 hold=d[:,names.index('v(hold)')];adc=d[:,names.index('v(adcin)')]
 metrics[label]=dict(hold_at_4us_V=float(np.interp(.002184,d[:,0],hold)),hold_at_5us_V=float(np.interp(.002185,d[:,0],hold)),adc_at_4us_V=float(np.interp(.002184,d[:,0],adc)),adc_at_5us_V=float(np.interp(.002185,d[:,0],adc)))
meta=json.loads((heavy/'result.json').read_text())
for ax in axes:
 for s in meta['samples'][:3]:
  t=(s['time_s']-.00217)*1e6;ax.plot([t-5,t],[s['dc']['v(HOLD)']]*2,'k:',label='Matched DC target' if s['column']==0 else None);ax.axvline(t,color='gray',alpha=.3)
 ax.legend();ax.grid(alpha=.2);ax.set_ylabel('Voltage (V)')
axes[0].set_title('First-row readout: external capacitive load sensitivity');axes[1].set_xlabel('Time after row-select starts (µs)')
fig.savefig(R/'docs/assets/camera-load-diagnostic.png',dpi=150);plt.close(fig)
(heavy/'settling-checkpoints.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
