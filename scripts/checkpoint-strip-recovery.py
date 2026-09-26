"""Archive the follow-up routing, numerical and column-capture experiments."""
from pathlib import Path
import hashlib,json,tarfile
R=Path(__file__).resolve().parents[1]
summary=json.loads((R/'simulations/array-recovery.json').read_text())
out=R/'checkpoints/array-recovery';out.mkdir(parents=True,exist_ok=False)
roots=[R/name for name in summary['evidence_roots']]
assert all(p.is_dir() for p in roots)
files={p for root in roots for p in root.rglob('*') if p.is_file()}
files.update(R/p for p in ['scripts/prepare-array-strips.py','scripts/audit-array-strip-rc.py','scripts/simulate-array-strips.py','scripts/analyze-strip-recovery.py','scripts/reduce-strip-resistors.py','scripts/verify-strip-resistor-models.py','scripts/check-column-capture-reference.py','scripts/finish-column-capture.py','scripts/budget-column-storage.py','scripts/status-strip-runs.py','scripts/report-strip-recovery.py','scripts/checkpoint-strip-recovery.py','scripts/diagnose-functional-camera.py','circuits/output-buffer.spice','build/size-study/20um/build/pixel_physical.gds','simulations/array-recovery.json','docs/array-recovery.md','docs/assets/array-recovery.png','PICK_UP_HERE.md'])
def streamhash(f):
 h=hashlib.sha256()
 while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def sha(p):
 with p.open('rb') as f:return streamhash(f)
manifest={'scope':summary['scope'],'files':{str(p.relative_to(R)):sha(p) for p in sorted(files)}}
archive=R/'build/array-recovery-evidence.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
 for name in manifest['files']:tar.add(R/name,arcname=name,recursive=False)
verified={}
with tarfile.open(archive,'r|gz') as tar:
 for member in tar:
  name=member.name;assert name in manifest['files'] and name not in verified,name
  if member.islnk():
   assert member.linkname in verified,(name,member.linkname)
   digest=verified[member.linkname]
  else:
   assert member.isfile(),name
   with tar.extractfile(member) as f:digest=streamhash(f)
  assert digest==manifest['files'][name],name
  verified[name]=digest
assert verified==manifest['files']
manifest['verification']={'method':'Streaming read-back of every tar member, resolving hard links; independently checked part and combined SHA256 hashes.'}
manifest.update(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,parts=[])
h=hashlib.sha256()
with archive.open('rb') as f:
 i=0
 while block:=f.read(40*1024*1024):
  part=out/f'evidence.tar.gz.part-{i:03d}';part.write_bytes(block)
  assert sha(part)==hashlib.sha256(block).hexdigest();h.update(part.read_bytes())
  manifest['parts'].append(dict(name=part.name,bytes=len(block),sha256=sha(part)));i+=1
assert h.hexdigest()==manifest['archive_sha256']
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'README.md').write_text('# Array recovery checkpoint\n\nConcatenate `evidence.tar.gz.part-*` in filename order and restore into an empty scratch directory. Every archive member, split part and combined archive was read back and verified.\n\nIncludes GDS, direct and RC-collapsed LVS, extraction, raw and adjusted RC models, audit, complete traces, matched DC references, exact runner snapshots and excluded fixture-development attempts. Read docs/array-recovery.md and simulations/array-recovery.json before interpreting results. This is unfilled-strip evidence, not full 64×64 or fabrication qualification.\n')
print(f'Verified {len(files)} files, {manifest["archive_bytes"]} archive bytes, {len(manifest["parts"])} parts',flush=True)
