"""Preserve staged integration evidence; verify archives and split at 40 MiB."""
from pathlib import Path
import hashlib,json,tarfile
R=Path(__file__).resolve().parents[1];out=R/'checkpoints/staged-integration';out.mkdir(parents=True,exist_ok=False)
summary=json.loads((R/'simulations/staged-integration.json').read_text())
dirs=[R/'build'/n for n in ['staged-readout-20260921','staged-protection-20260921','staged-protection-controls-20260921','shared-circuit/staged-full-reset-norton-20260921','shared-circuit/staged-full-reset-norton-1us-20260921']]
files=[p for d in dirs for p in d.rglob('*') if p.is_file()]
files += [R/p for p in ['scripts/stage-array-readout.py','scripts/stage-array-protection.py','scripts/report-staged-integration.py','scripts/checkpoint-staged-integration.py','scripts/diagnose-shared-circuit.py','scripts/diagnose-standalone-row.py','scripts/diagnose-functional-camera.py','simulations/staged-integration.json','docs/staged-integration.md','docs/assets/staged-integration.png','PICK_UP_HERE.md']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'scope':summary['scope'],'files':{str(p.relative_to(R)):sha(p) for p in sorted(set(files))},'dependencies':{p:sha(R/p) for p in ['checkpoints/array-extension/evidence.tar.gz','simulations/final-chip-pixel-map.json']}}
archive=R/'build/staged-readout-20260921/evidence.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz') as t:
 for name in manifest['files']:t.add(R/name,arcname=name,recursive=False)
with tarfile.open(archive) as t:
 assert {x.name for x in t.getmembers()}==set(manifest['files'])
 for name,digest in manifest['files'].items():assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==digest
manifest['archive_sha256']=sha(archive);manifest['archive_bytes']=archive.stat().st_size;manifest['parts']=[]
with archive.open('rb') as f:
 i=0
 while chunk:=f.read(40*1024*1024):
  p=out/f'evidence.tar.gz.part-{i:03d}';p.write_bytes(chunk);manifest['parts'].append({'name':p.name,'bytes':len(chunk),'sha256':sha(p)});i+=1
h=hashlib.sha256()
for x in manifest['parts']:h.update((out/x['name']).read_bytes())
assert h.hexdigest()==manifest['archive_sha256']
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'README.md').write_text('# Staged integration checkpoint\n\nConcatenate `evidence.tar.gz.part-*` in filename order to recover the archive. The manifest records individual file, part and combined archive hashes. All archived members were read back and verified.\n\nThese are staged diagnostics, not full-camera qualification. Read `docs/staged-integration.md` for outcomes and model boundaries.\n')
print(f'Verified {len(manifest["files"])} files; {manifest["archive_bytes"]} bytes in {len(manifest["parts"])} parts')
