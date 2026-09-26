"""Resume verification of an already-written strip archive in one streaming pass.
Regular members are hashed against source files; hard links resolve to previously
verified archive members. No archive is rewritten and no prior parts may exist.
"""
from pathlib import Path
import hashlib,json,tarfile
R=Path(__file__).resolve().parents[1]
summary=json.loads((R/'simulations/array-strips.json').read_text())
out=R/'checkpoints/array-strips';assert out.is_dir() and not list(out.iterdir())
roots=sorted(p for p in (R/'build').glob('array-strip*20260924') if p.is_dir())
files={p for root in roots for p in root.rglob('*') if p.is_file()}
files.update(R/p for p in ['scripts/prepare-array-strips.py','scripts/check-strip-dc-solver.py','scripts/audit-array-strip-rc.py','scripts/simulate-array-strips.py','scripts/report-array-strips.py','scripts/checkpoint-array-strips.py','scripts/diagnose-functional-camera.py','circuits/output-buffer.spice','build/size-study/20um/build/pixel_physical.gds','simulations/array-strips.json','docs/array-strips.md','docs/tapeout-readiness.md','docs/assets/array-strips.png','PICK_UP_HERE.md'])
def streamhash(f):
 h=hashlib.sha256()
 while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def sha(p):
 with p.open('rb') as f:return streamhash(f)
manifest={'scope':summary['scope'],'files':{str(p.relative_to(R)):sha(p) for p in sorted(files)}}
archive=R/'build/array-strips-evidence.tar.gz';assert archive.is_file()
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
manifest['verification']={'method':'Single streaming read-back: every regular member hashed and every hard link resolved to an earlier verified member; sources independently hashed.', 'verifier_sha256':sha(Path(__file__))}
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
(out/'README.md').write_text('# Extracted 64-pixel strips checkpoint\n\nConcatenate `evidence.tar.gz.part-*` in filename order and restore into an empty scratch directory. Every archive member, split part and combined archive was read back and verified.\n\nIncludes GDS, direct and RC-collapsed LVS, extraction, raw and adjusted RC models, audit, complete traces, matched DC references, exact runner snapshots and excluded fixture-development attempts. Read docs/array-strips.md and build/array-strips-20260924/attempts.json before interpreting results. This is unfilled-strip evidence, not full 64×64 or fabrication qualification.\n')
print(f'Verified {len(files)} files, {manifest["archive_bytes"]} archive bytes, {len(manifest["parts"])} parts',flush=True)
