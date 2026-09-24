"""Archive completed shared-circuit investigations, including failed controls."""
from pathlib import Path
import hashlib
import json
import tarfile

R = Path(__file__).resolve().parents[1]
B = R/'build/shared-circuit'
O = R/'checkpoints/shared-circuit'
O.mkdir(parents=True, exist_ok=True)
archive = B/'evidence.tar.gz'
assert not archive.exists() and not list(O.glob('evidence.tar.gz.part-*')), 'Refuse to overwrite preserved evidence'
summary = json.loads((R/'simulations/shared-circuit.json').read_text())
assert len(summary['cases']) == 10
files = []
for case in summary['cases']:
    directory = B/case['name']
    assert (directory/'result.json').exists()
    files += [p for p in directory.rglob('*') if p.is_file()]
files += [p for p in (B/'full-restoration-audit-20260920').rglob('*') if p.is_file()]
extra = ['build/shared-circuit/driver-equivalence-baseline.json',
         'scripts/diagnose-shared-circuit.py', 'scripts/report-shared-circuit.py', 'scripts/checkpoint-shared-circuit.py',
         'scripts/diagnose-standalone-row.py', 'scripts/diagnose-functional-camera.py',
         'scripts/build-ngspice-comparison.sh', 'simulations/shared-circuit.json', 'simulations/final-chip-pixel-map.json',
         'docs/shared-circuit.md', 'docs/shared-circuit-section.html',
         'docs/assets/shared-circuit.png', 'docs/assets/shared-circuit-reset-source.png',
         'PICK_UP_HERE.md', 'checkpoints/shared-circuit/README.md',
         'build/ngspice-version-comparison/ngspice-46.tar.gz',
         'build/ngspice-version-comparison/install-46/bin/ngspice',
         'build/ngspice-version-comparison/build-46/config.log',
         'build/ngspice-version-comparison/build-hashes.txt',
         'build/ngspice-version-comparison/ngspice-46/src/maths/ni/niconv.c',
         'build/ngspice-version-comparison/ngspice-46/src/spicelib/analysis/ckttroub.c',
         'build/ngspice-version-comparison/ngspice-46/src/spicelib/analysis/dctran.c']
files += [R/p for p in extra]
files = sorted(set(files))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = dict(scope='Ten bounded diagnostics and full-model reconstruction audit. Fast ideal-supply pair is a different event from the unresolved original third-row failure.',
    accepted_full_chip=False,
    dependencies={name: sha(R/name) for name in ['checkpoints/standalone-row/evidence.tar.gz',
                  'checkpoints/ngspice-version-comparison/evidence.tar.gz', 'scripts/run-tools.sh']},
    files={str(p.relative_to(R)): sha(p) for p in files})
with tarfile.open(archive, 'w:gz') as tar:
    for p in files:
        tar.add(p, arcname=str(p.relative_to(R)), recursive=False)
manifest['archive_sha256'] = sha(archive)
with tarfile.open(archive) as tar:
    assert {m.name for m in tar.getmembers()} == set(manifest['files'])
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(tar.extractfile(name).read()).hexdigest() == digest
manifest['parts'] = {}
reassembled = hashlib.sha256()
with archive.open('rb') as stream:
    index = 0
    while block := stream.read(40*1024*1024):
        part = O/f'evidence.tar.gz.part-{index:03d}'
        with part.open('xb') as output:
            output.write(block)
        manifest['parts'][part.name] = dict(bytes=part.stat().st_size, sha256=sha(part))
        reassembled.update(part.read_bytes())
        index += 1
assert reassembled.hexdigest() == manifest['archive_sha256']
(O/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'Archived and verified {len(files)} files, {archive.stat().st_size} bytes in {len(manifest["parts"])} parts')
