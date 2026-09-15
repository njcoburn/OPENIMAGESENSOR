"""Archive generated design evidence, excluding desktop sessions and credentials."""
from pathlib import Path
import tarfile,json,hashlib
root=Path(__file__).resolve().parents[1]
paths=['build/array_3x3.gds','build/array-functional.gds','build/pixel_physical.gds','build/array_schematic.spice','build/array-check','build/array-sim','build/layout-probe-verified','build/array-primitives']
for n in (5,10,20):
 for d in ('build','layout','xschem','simulations','docs/assets'):paths.append(f'build/size-study/{n}um/{d}')
paths += [f'simulations/cycles_{x}' for x in ('0','1p','5p')]
paths += [f'simulations/reset_candidate_{x}' for x in ('0','1p','5p')]
files=[]
for name in paths:
 p=root/name
 assert p.exists(),p
 files.extend(sorted(p.rglob('*')) if p.is_dir() else [p])
files=sorted(set(p for p in files if p.is_file() and '__pycache__' not in p.parts))
out=root/'checkpoints/gf180-3x3-size-study.tar.gz'
manifest={'description':'Verified baseline and 5/10/20 um array electrical study; no extracted wiring/fill parasitics.','docker_image':'hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a','files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
with tarfile.open(out,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
manifest['archive_sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
(root/'checkpoints/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'{len(files)} files; {out.stat().st_size/1024**2:.1f} MiB')
