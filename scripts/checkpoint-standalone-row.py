"""Preserve row isolation evidence and the instrumented full-chip failure."""
from pathlib import Path
import hashlib
import json
import tarfile

R = Path(__file__).resolve().parents[1]
out = R/'checkpoints/standalone-row'
out.mkdir(parents=True, exist_ok=True)
archive = out/'evidence.tar.gz'
assert not archive.exists(), 'Refuse to overwrite preserved evidence'
summary = json.loads((R/'simulations/standalone-row.json').read_text())
assert len(summary['cases']) == 12 and all(x['completed'] for x in summary['cases'])
directories = [R/'build/standalone-row'/name for name in sorted({x['run'] for x in summary['cases']})]
directories += [R/'build/functional-camera-diagnostic'/name for name in
                ['reset-edge-internal-20260920', 'internal-capture-smoke-20260920']]
files = []
for directory in directories:
    assert (directory/'result.json').exists()
    files += [p for p in directory.rglob('*') if p.is_file() and p.suffix != '.npz']
for name in ['scripts/diagnose-functional-camera.py', 'scripts/diagnose-standalone-row.py',
             'scripts/report-standalone-row.py', 'scripts/checkpoint-standalone-row.py',
             'simulations/final-chip-pixel-map.json', 'simulations/standalone-row.json',
             'docs/standalone-row.md', 'docs/standalone-row-section.html', 'docs/assets/standalone-row.png',
             'PICK_UP_HERE.md', 'checkpoints/standalone-row/README.md']:
    files.append(R/name)
files = sorted(set(files))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = dict(scope='Twelve completed standalone reset diagnostics and an unchanged instrumented full-chip failure; no full-chip qualification.',
    accepted_full_chip=False, full_chip_completed=False,
    dependencies={name: sha(R/name) for name in ['checkpoints/streamed-frame/evidence.tar.gz', 'scripts/run-tools.sh']},
    files={str(p.relative_to(R)): sha(p) for p in files})
with tarfile.open(archive, 'w:gz') as tar:
    for p in files:
        tar.add(p, arcname=str(p.relative_to(R)), recursive=False)
manifest['archive_sha256'] = sha(archive)
with tarfile.open(archive) as tar:
    assert {m.name for m in tar.getmembers()} == set(manifest['files'])
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(tar.extractfile(name).read()).hexdigest() == digest
(out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'Archived and verified {len(files)} files, {archive.stat().st_size} bytes')
