"""Archive the new isolated-column evidence and verify every archived file."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out=ROOT/'checkpoints/physical-capture-column'
    out.mkdir(exist_ok=False)
    files=set()
    for path in (ROOT/'build').glob('capture-*'):
        if path.is_dir():files.update(p for p in path.rglob('*') if p.is_file())
        elif path.is_file():files.add(path)
    files={p for p in files if '__pycache__' not in p.parts}
    files.update(ROOT/name for name in [
        'layout/capture-primitives.tcl','scripts/build-capture-column.py',
        'scripts/verify-capture-column.py','scripts/simulate-capture-column.py',
        'scripts/check-capture-capacitance.py','scripts/report-physical-capture-column.py',
        'scripts/checkpoint-physical-capture-column.py','scripts/run-tools.sh',
        'docs/physical-capture-column.md','docs/capture-tile-plan.md',
        'docs/capture-column-preparation.md','PICK_UP_HERE.md','NEXT_STEPS.md',
        'CHANGELOG.md','README.md','docs/README.md','COMPLETION_PLAN.md',
        'simulations/physical-capture-column.json',
        'checkpoints/capture-column-preparation/capture-column.spice'])
    build=json.loads((ROOT/'build/capture-column-v2-20260925/build.json').read_text())
    files.update(ROOT/name for name in build['source_sha256'])
    records={str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)}
    archive=out/'evidence.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for name in records:tar.add(ROOT/name,arcname=name,recursive=False)
    seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in records and member.name not in seen
            data=tar.extractfile(member).read()
            assert {'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}==records[member.name]
            seen.add(member.name)
    assert seen==set(records)
    manifest=dict(files=records,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,read_back_verified=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.md').write_text('# First physical capture column\n\n'
        'Physical DRC/LVS and capacitor AC/leakage checks pass. Transient accuracy and\n'
        'capacitance-placement sensitivity remain unqualified. See\n'
        '[the report](../../docs/physical-capture-column.md).\n\n'
        'The archive retains accepted geometry, extracted models, tool logs, source\n'
        'primitives, runner snapshots and all failed/incomplete development attempts.\n'
        'Every member was read back and checked against manifest.json.\n'
        'Restore into an empty scratch directory; preserve older checkpoints.\n')
    print(json.dumps({'files':len(records),'archive_bytes':manifest['archive_bytes'],'read_back_verified':True}))


if __name__=='__main__':main()
