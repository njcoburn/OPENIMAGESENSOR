from pathlib import Path
import json
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];d=json.loads((root/'simulations/buffer-pex.json').read_text());fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for corner in ['typical','ff','ss','fs','sf']:
 r=[v for v in d['cases'].values() if v['status']=='complete' and v['buffer_model']=='RC' and v['corner']==corner and v['diode']=='diode_typical']
 ax[0].plot([v['temp_C'] for v in r],[v['max_hold_error_mV'] for v in r],'o-',label=corner)
 ax[1].plot([v['temp_C'] for v in r],[v['max_output_shift_vs_schematic_mV'] for v in r],'o-',label=corner)
ax[0].axhline(.5,color='black',linestyle='--',label='0.5 mV screen');ax[0].set(xlabel='Temperature (°C)',ylabel='Worst sampling error (mV)',title='Extracted buffer · typical diode')
ax[1].set(xlabel='Temperature (°C)',ylabel='Largest sampled-voltage change (mV)',title='Extracted versus schematic buffer')
for a in ax:a.grid(alpha=.2);a.legend()
fig.savefig(root/'docs/assets/buffer-pex.png',dpi=160)
