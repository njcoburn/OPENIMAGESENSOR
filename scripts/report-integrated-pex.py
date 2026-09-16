"""Plot and archive the connected-layout simulation checkpoint."""
from pathlib import Path
import json,gzip,shutil,tarfile,hashlib,re
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];p=root/'simulations/integrated-pex.json';d=json.loads(p.read_text());pex=root/'build/integrated-pex'
def signatures(paths):
 rows=[]
 for path in paths:
  for line in path.read_text().splitlines():
   if not line or line[0] not in 'XD':continue
   t=line.split();index=5 if line[0]=='X' else 3;props=[]
   for param in t[index+1:]:
    key,v=param.split('=');m=re.fullmatch(r'([+-]?[\d.]+(?:[eE][+-]?\d+)?)([a-zA-Z]*)',v)
    value=float(m[1])*{'':1,'u':1e-6,'p':1e-12,'n':1e-9,'f':1e-15}[m[2].lower()];props.append((key.lower(),round(value,24)))
   rows.append((t[index],tuple(sorted(props))))
 return Counter(rows)
assert signatures([pex/'sensor_reduced.spice'])==signatures([root/'simulations/extracted-20um/rc-filled/array_reduced.spice',root/'checkpoints/readout/pex/readout_reduced.spice',root/'checkpoints/output-buffer/pex/buffer_reduced.spice'])
d['device_geometry_matches_separate_blocks']=True;p.write_text(json.dumps(d,indent=2)+'\n')
rows=[r for r in d['cases'].values() if r['status']=='complete']
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained');x=np.arange(len(rows))
labels=[f'{r["model"]}\n{r["corner"]} / {r["temp_C"]}°C'+('\nfast diode' if r['diode']=='diode_ff' else '') for r in rows]
ax[0].bar(x,[r['max_hold_error_mV'] for r in rows]);ax[0].axhline(.5,color='red',ls='--',label='0.5 mV screen');ax[0].legend();ax[0].set(title='Connected-layout sampling error',ylabel='Maximum HOLD error (mV)')
ax[1].bar(x,[r['max_output_shift_vs_separate_blocks_mV'] for r in rows]);ax[1].set(title='Calibration change from separate blocks',ylabel='Maximum sampled-output change (mV)')
for a in ax:a.set_xticks(x,labels);a.grid(axis='y',alpha=.2);a.set_axisbelow(True)
fig.savefig(root/'docs/assets/integrated-comparison.png',dpi=160)
dest=root/'checkpoints/integrated/pex';dest.mkdir(exist_ok=True)
for name in ['sensor_reduced.spice','sensor_devices.spice','sensor_c.spice','sensor_alternate.spice','sensor_lowr.spice','reduction.json','extraction.log','lvs.log']:shutil.copyfile(pex/name,dest/name)
with gzip.open(dest/'sensor_raw.spice.gz','wb') as f:f.write((pex/'sensor_rc.spice').read_bytes())
files=sorted(f for folder in ['sim','diagnostics'] for f in (pex/folder).rglob('*') if f.is_file() and f.name in {'testbench.spice','run.log','result.json'})+[p,root/'simulations/integrated-verification.json']
manifest={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
with tarfile.open(root/'checkpoints/integrated/evidence.tar.gz','w:gz') as archive:
 for f in files:archive.add(f,arcname=str(f.relative_to(root)))
(root/'checkpoints/integrated/evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Archived integrated checkpoint:',len(files),'evidence files')
