"""Preserve bounded switching diagnostics, including incomplete attempts."""
from pathlib import Path
import hashlib
import json
import tarfile

R = Path(__file__).resolve().parents[1]
out = R/'checkpoints/functional-camera-diagnostic'
out.mkdir(parents=True, exist_ok=True)
archive = out/'evidence.tar.gz'
assert not archive.exists(), 'Refuse to overwrite diagnostic checkpoint'
files = sorted(p for p in (R/'build/functional-camera-diagnostic').rglob('*') if p.is_file() and p.suffix != '.npz')
assert files
for name in ['scripts/diagnose-functional-camera.py', 'scripts/report-functional-diagnostic.py',
             'scripts/checkpoint-functional-diagnostic.py', 'docs/functional-camera-diagnostic.md',
             'simulations/functional-camera-diagnostic.json']:
    files.append(R/name)
for run in (R/'build/functional-camera-diagnostic').iterdir():
    if run.is_dir() and (run/'run.json').exists():
        assert (run/'result.json').exists(), f'Run still pending: {run.name}'
manifest = dict(scope='Bounded diagnostics only; retain watchdog/setup failures; no full-chip qualification.',
                dependencies={'checkpoints/functional-camera/evidence.tar.gz': hashlib.sha256((R/'checkpoints/functional-camera/evidence.tar.gz').read_bytes()).hexdigest()},
                files={str(p.relative_to(R)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
with tarfile.open(archive, 'w:gz') as tar:
    for path in files:
        tar.add(path, arcname=str(path.relative_to(R)), recursive=False)
manifest['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
with tarfile.open(archive) as tar:
    assert {m.name for m in tar.getmembers()} == set(manifest['files'])
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(tar.extractfile(name).read()).hexdigest() == digest
(out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'Wrote and verified {len(files)} files; archive {archive.stat().st_size} bytes')
