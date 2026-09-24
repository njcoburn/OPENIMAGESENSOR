"""Archive a streamed nominal frame, matched references and scoped reports."""
from pathlib import Path
import hashlib
import json
import tarfile

R = Path(__file__).resolve().parents[1]
summary = json.loads((R/'simulations/streamed-frame.json').read_text())
run = summary['run']
frame_dir = R/'build/functional-camera-diagnostic'/run
assert (frame_dir/'result.json').exists()
out = R/'checkpoints/streamed-frame'
out.mkdir(parents=True, exist_ok=True)
archive = out/'evidence.tar.gz'
assert not archive.exists(), 'Refuse to overwrite a saved frame checkpoint'
files = [p for p in frame_dir.rglob('*') if p.is_file() and p.suffix != '.npz']
reference_root = R/'build/functional-dc-reference'
for name in ['reference-probe-r0c0', 'reference-probe-bright', 'nominal-frame-dc']:
    directory = reference_root/name
    if directory.exists():
        assert (directory/'result.json').exists(), f'Reference still pending: {name}'
        assert 'completed' in json.loads((directory/'result.json').read_text()), f'Reference still running: {name}'
        files += [p for p in directory.rglob('*') if p.is_file()]
for relative in ['scripts/diagnose-functional-camera.py', 'scripts/report-functional-diagnostic.py',
                 'scripts/reference-streamed-frame.py', 'scripts/analyze-streamed-frame.py',
                 'scripts/report-streamed-frame.py', 'scripts/inspect-streamed-frame.py', 'scripts/checkpoint-streamed-frame.py',
                 'docs/streamed-frame.md', 'docs/streamed-frame-section.html',
                 'simulations/streamed-frame.json', 'simulations/final-chip-pixel-map.json',
                 'build/filled-electrical-baseline/audit.json', 'PICK_UP_HERE.md']:
    files.append(R/relative)
files += list((R/'docs/assets').glob('streamed-frame*.png'))
files = sorted(set(files))
manifest = dict(scope='Incomplete nominal-frame attempt and static-reference probes; no full-chip qualification.',
                frame_completed=summary['frame_completed'], accepted_full_chip=False,
                dependencies={name: hashlib.sha256((R/name).read_bytes()).hexdigest() for name in [
                    'checkpoints/functional-camera/evidence.tar.gz',
                    'checkpoints/functional-camera-diagnostic/evidence.tar.gz']},
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
