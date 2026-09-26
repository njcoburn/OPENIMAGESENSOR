"""Archive and read-back verify the bounded camera load/PVT screen evidence."""
from pathlib import Path
import hashlib,json,tarfile
R=Path(__file__).resolve().parents[1]
summary=json.loads((R/'simulations/camera-operating-corners.json').read_text())
out=R/'checkpoints/camera-operating-corners';out.mkdir(parents=True,exist_ok=False)
roots=[R/'build/camera-operating-corners'/b['run'] for b in summary['batches']]
roots.append(R/'build/camera-operating-corners/cold-pad-diagnostic-20260924')
files={p for root in roots for p in root.rglob('*') if p.is_file()}
files.update(R/p for p in ['scripts/screen-camera-operating-corners.py','scripts/report-camera-operating-corners.py','scripts/plot-camera-load-diagnostic.py','scripts/diagnose-camera-cold-pad.py','scripts/checkpoint-camera-operating-corners.py','scripts/diagnose-functional-camera.py','simulations/camera-operating-corners.json','simulations/final-chip-pixel-map.json','docs/camera-operating-corners.md','docs/assets/camera-operating-corners.png','docs/assets/camera-load-diagnostic.png','PICK_UP_HERE.md','build/functional-pad-model/caps.json','build/functional-pad-model/stock-model.spice','build/functional-pad-model/frozen-model.json'])
def streamhash(f):
 h=hashlib.sha256()
 while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def sha(p):
 with p.open('rb') as f:return streamhash(f)
manifest=dict(scope=summary['scope'],files={str(p.relative_to(R)):sha(p) for p in sorted(files)},dependencies={'checkpoints/three-frames/manifest.json':sha(R/'checkpoints/three-frames/manifest.json')})
archive=R/'build/camera-operating-corners-evidence.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
 for name in manifest['files']:tar.add(R/name,arcname=name,recursive=False)
with tarfile.open(archive) as tar:
 assert {m.name for m in tar.getmembers()}==set(manifest['files'])
 for name,digest in manifest['files'].items():
  with tar.extractfile(name) as f:assert streamhash(f)==digest,name
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
(out/'README.md').write_text('# Camera load and operating-corner checkpoint\n\nConcatenate `evidence.tar.gz.part-*` in filename order and restore to an empty scratch directory. The manifest records every member, part and combined archive hash; all were read back and verified. Includes exact stock/frozen models, capacitor recalculations, decks, full waveforms, matched DC references and failed or timed-out attempts.\n\nRead `docs/camera-operating-corners.md` for measured results, selected coverage and limitations. Startup, full distributed R+C and fabrication qualification remain open.\n')
print(f'Verified {len(files)} files, {manifest["archive_bytes"]} archive bytes, {len(manifest["parts"])} parts',flush=True)
