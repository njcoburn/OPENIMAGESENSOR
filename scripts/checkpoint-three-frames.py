"""Archive three-frame evidence; stream hashes and split at 40 MiB."""
from pathlib import Path
import hashlib,json,tarfile
R=Path(__file__).resolve().parents[1];out=R/'checkpoints/three-frames';out.mkdir(parents=True,exist_ok=False)
summary=json.loads((R/'simulations/three-frames.json').read_text());run=R/'build/shared-circuit'/summary['run'];dirs=[run]
if 'dc_reference' in summary:dirs.append(R/'build/functional-dc-reference'/summary['dc_reference']['run'])
prior=R/'build/shared-circuit/three-frame-reset-norton-20260923'
seed=R/'build/functional-dc-reference/two-frame-dc-20260924'
if prior!=run and prior.exists():dirs.append(prior)
if seed.exists() and seed not in dirs:dirs.append(seed)
reconstruction=None
if prior!=run and (prior/'stream.raw').exists():
 def header(f):
  rows=[]
  while line:=f.readline():
   rows.append(line)
   if line==b'Binary:\n':return b''.join(rows)
  raise ValueError('Raw header has no Binary delimiter')
 with (prior/'stream.raw').open('rb') as old, (run/'stream.raw').open('rb') as new:
  oldheader=header(old);header(new);count=0;identical=True
  while chunk:=old.read(4*1024*1024):
   count+=len(chunk)
   if new.read(len(chunk))!=chunk:identical=False;break
 if identical:
  hp=prior/'stream.raw.header';hp.write_bytes(oldheader)
  reconstruction={'path':str((prior/'stream.raw').relative_to(R)),'header':str(hp.relative_to(R)),'canonical':str((run/'stream.raw').relative_to(R)),'body_prefix_bytes':count,'rule':'Original header bytes followed by this many bytes from the canonical Binary section; exact prefix comparison passed.'}
files=[p for d in dirs for p in d.rglob('*') if p.is_file() and not (reconstruction and str(p.relative_to(R))==reconstruction['path'])]
files += [R/p for p in ['scripts/report-three-frames.py','scripts/reference-three-frames.py','scripts/checkpoint-three-frames.py','scripts/diagnose-shared-circuit.py','scripts/diagnose-standalone-row.py','scripts/diagnose-functional-camera.py','simulations/final-chip-pixel-map.json','simulations/three-frames.json','docs/three-frames.md','docs/assets/three-frames.png','PICK_UP_HERE.md']]
def streamhash(f):
 h=hashlib.sha256()
 while block:=f.read(4*1024*1024):h.update(block)
 return h.hexdigest()
def sha(p):
 with p.open('rb') as f:return streamhash(f)
manifest={'scope':summary['scope'],'files':{str(p.relative_to(R)):sha(p) for p in sorted(set(files))},'dependencies':{'checkpoints/staged-integration/manifest.json':sha(R/'checkpoints/staged-integration/manifest.json')}}
if reconstruction:
 reconstruction['sha256']=sha(R/reconstruction['path']);manifest['reconstructed_files']=[reconstruction]
archive=R/'build/three-frames-evidence.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz',compresslevel=6) as t:
 for name in manifest['files']:t.add(R/name,arcname=name,recursive=False)
with tarfile.open(archive) as t:
 assert {x.name for x in t.getmembers()}==set(manifest['files'])
 for name,digest in manifest['files'].items():
  with t.extractfile(name) as f:assert streamhash(f)==digest
 if reconstruction:
  with t.extractfile(reconstruction['header']) as f:h=hashlib.sha256(f.read())
  with t.extractfile(reconstruction['canonical']) as f:
   header(f);left=reconstruction['body_prefix_bytes']
   while left:
    block=f.read(min(left,4*1024*1024));assert block;h.update(block);left-=len(block)
  assert h.hexdigest()==reconstruction['sha256']
manifest['archive_sha256']=sha(archive);manifest['archive_bytes']=archive.stat().st_size;manifest['parts']=[]
h=hashlib.sha256()
with archive.open('rb') as f:
 i=0
 while chunk:=f.read(40*1024*1024):
  p=out/f'evidence.tar.gz.part-{i:03d}';p.write_bytes(chunk);h.update(chunk);manifest['parts'].append({'name':p.name,'bytes':len(chunk),'sha256':sha(p)});i+=1
assert h.hexdigest()==manifest['archive_sha256']
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'README.md').write_text('# Three-frame checkpoint\n\nConcatenate `evidence.tar.gz.part-*` in filename order. Member, part and combined archive hashes are recorded in the manifest and were verified. Exact transient and conditional DC-reference decks, waveforms and logs are included.\n\nThe initial timed-out raw trace may be represented by its archived exact header plus a verified prefix of the completed trace Binary section; the manifest records reconstruction length and the original complete-file SHA-256, which was verified from archive members. No trace samples are discarded.\n\nRead `docs/three-frames.md` for measured outcomes and model limitations. This is normal-operation evidence, not startup, RC, corner or fabrication qualification.\n')
print(f'Verified {len(manifest["files"])} files; {manifest["archive_bytes"]} bytes in {len(manifest["parts"])} parts')
