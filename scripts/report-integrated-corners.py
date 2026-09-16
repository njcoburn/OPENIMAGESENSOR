"""Plot, render and archive the connected-layout corner matrix."""
from pathlib import Path
import json,base64,hashlib,tarfile
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];p=root/'simulations/integrated-corners.json';d=json.loads(p.read_text());rows=list(d['cases'].values())
assert len(rows)==24,'Matrix incomplete'
for name,digest in d['source_sha256'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,('Source changed after simulation',name)
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for corner in ['typical','ff','ss','fs','sf']:
 r=sorted((v for v in rows if v['status']=='complete' and v['corner']==corner and v['diode']=='diode_typical'),key=lambda v:v['temp_C'])
 ax[0].plot([v['temp_C'] for v in r],[v['max_hold_error_mV'] for v in r],'o-',label=corner)
 ax[1].plot([v['temp_C'] for v in r],[v['max_output_shift_vs_separate_blocks_mV'] for v in r],'o-',label=corner)
for diode,marker in [('diode_ff','^'),('diode_ss','s')]:
 r=sorted((v for v in rows if v['status']=='complete' and v['diode']==diode),key=lambda v:v['temp_C'])
 for a,key in zip(ax,['max_hold_error_mV','max_output_shift_vs_separate_blocks_mV']):a.scatter([v['temp_C'] for v in r],[v[key] for v in r],marker=marker,s=65,facecolors='none',edgecolors='black',label='typical MOS / '+diode)
ax[0].axhline(.5,color='red',ls='--',label='0.5 mV screen');ax[0].set(title='Connected RC: sampling error',ylabel='Maximum HOLD error (mV)')
ax[1].set(title='Change from separately extracted blocks',ylabel='Maximum sampled-output change (mV)')
for a in ax:a.set_xlabel('Temperature (°C)');a.grid(alpha=.2);a.legend(fontsize=8)
fig.savefig(root/'docs/assets/integrated-corners.png',dpi=160)
files={p,root/'simulations/integrated-verification.json'}
for name,r in d['cases'].items():
 folder=root/'build/integrated-pex/sim'/name
 files.update(f for f in folder.rglob('*') if f.is_file() and f.name in {'testbench.spice','run.log','result.json'})
for name,r in d.get('checks',{}).items():
 folder=root/'build/integrated-pex/sim'/name
 files.update(f for f in folder.rglob('*') if f.is_file() and f.name in {'testbench.spice','run.log','result.json'})
files.update(root/f for f in ['scripts/integrated-corners.py','scripts/check-integrated-corners.py','scripts/simulate-integrated.py','scripts/report-integrated-corners.py'])
files=sorted(files);manifest={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
dest=root/'checkpoints/integrated'
with tarfile.open(dest/'corners-evidence.tar.gz','w:gz') as archive:
 for f in files:archive.add(f,arcname=str(f.relative_to(root)))
(dest/'corners-evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Archived',len(files),'full-matrix evidence files')
