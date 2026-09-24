"""Archive extension decks, layouts, logs and waveforms with verified hashes."""
from pathlib import Path
import hashlib,json,tarfile
root=Path(__file__).resolve().parents[1]
out=root/'checkpoints/array-extension';out.mkdir(parents=True,exist_ok=False)
files=[]
for name in ['build/array-extension-20260920','build/array-extension-finite-20260920']:
 files += [p for p in (root/name).rglob('*') if p.is_file()]
files += [root/p for p in ['scripts/check-array-extension.py','scripts/checkpoint-array-extension.py','docs/array-extension.md','simulations/array-extension.json','build/size-study/20um/build/pixel_physical.gds','build/size-study/20um/build/array-functional.gds']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'scope':'Unfilled array-core scaling only; full camera failure remains unresolved.','files':{str(p.relative_to(root)):sha(p) for p in sorted(set(files))}}
archive=out/'evidence.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for name in manifest['files']:t.add(root/name,arcname=name,recursive=False)
with tarfile.open(archive) as t:
 assert {m.name for m in t.getmembers()}==set(manifest['files'])
 for name,digest in manifest['files'].items():assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==digest
manifest['archive_sha256']=sha(archive);manifest['archive_bytes']=archive.stat().st_size
assert archive.stat().st_size<40*1024*1024,'Split archive before staging'
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Verified {len(manifest["files"])} files, {archive.stat().st_size} compressed bytes')
