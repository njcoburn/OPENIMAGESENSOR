from pathlib import Path
import json,hashlib
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];d=json.loads((root/'simulations/buffer-hardened-corners.json').read_text());initial=json.loads((root/'simulations/buffer-hardening.json').read_text())['initial_tests']
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
a=[initial[f'fs_125C_{ua}uA_0.1us'] for ua in [20,30,40,60]]
ax[0].plot([20,30,40,60],[r['max_hold_error_mV'] for r in a],'o-');ax[0].set(xlabel='Buffer reference (µA)',ylabel='Sample error (mV)',title='Hot mixed corner · original startup sequence')
for corner in ['typical','ff','ss','fs','sf']:
 rows=[r for r in d['cases'].values() if r['status']=='complete' and r['corner']==corner and r['diode']=='diode_typical']
 ax[1].plot([r['temp_C'] for r in rows],[r['max_hold_error_mV'] for r in rows],'o-',label=corner)
ax[1].set(xlabel='Temperature (°C)',ylabel='Worst sample error (mV)',title='40 µA + all-row startup reset');ax[1].legend()
for a in ax:a.axhline(.5,color='black',linestyle='--',label='0.5 mV target');a.grid(alpha=.2)
fig.savefig(root/'docs/assets/buffer-hardening.png',dpi=160)
files=[root/'circuits/output-buffer.spice',root/'checkpoints/output-buffer/output_buffer.gds',root/'checkpoints/readout/pex/readout_reduced.spice',root/'simulations/extracted-20um/rc-filled/array_reduced.spice']
d['source_sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(root/'simulations/buffer-hardened-corners.json').write_text(json.dumps(d,indent=2)+'\n')
