"""Archive successful column matrices, routing iterations and isolation controls."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def streamhash(stream):
    value=hashlib.sha256()
    for block in iter(lambda:stream.read(4*1024*1024),b''):value.update(block)
    return value.hexdigest()


def sha(path):
    with path.open('rb') as stream:return streamhash(stream)


def main():
    out=ROOT/'checkpoints/capture-column-qualification';out.mkdir(exist_ok=False)
    files=set()
    patterns=['capture-isolation*','capture-column-matrix*','capture-column-power-*',
              'capture-column-routed-*','capture-column-qualified*','capture-column-v2-20260925']
    for pattern in patterns:
        for path in (ROOT/'build').glob(pattern):
            if path.is_dir():files.update(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
            elif path.is_file():files.add(path)
    source=ROOT/'build/capture-column-screen-v2-singlethread-20260925'
    files.add(source/'27-1.6-100/test.spice')
    files.update(source/name for name in ['rc.spice','rcfar.spice','physical.spice','ideal.spice'])
    files.update(ROOT/name for name in [
        'scripts/diagnose-capture-transient.py','scripts/qualify-capture-column.py',
        'scripts/audit-capture-column-matrix.py','scripts/report-capture-column-qualification.py',
        'scripts/checkpoint-capture-column-qualification.py','scripts/build-capture-column.py',
        'scripts/verify-capture-column.py','scripts/check-capture-capacitance.py',
        'scripts/run-tools.sh','scripts/build-overview.py','layout/capture-primitives.tcl',
        'checkpoints/capture-column-preparation/capture-column.spice',
        'docs/capture-column-qualification.md','docs/capture-column-qualification-section.html',
        'docs/assets/capture-column-qualification.png','docs/capture-tile-plan.md',
        'docs/physical-capture-column.md','docs/README.md','README.md',
        'docs/completion-dashboard.html',
        'PICK_UP_HERE.md','NEXT_STEPS.md','COMPLETION_PLAN.md','CHANGELOG.md',
        'simulations/capture-column-qualification.json'])
    previous=ROOT/'build/capture-capacitance-v3-20260925'
    files.update(p for p in previous.rglob('*') if p.is_file())
    selected=json.loads((ROOT/'simulations/capture-column-qualification.json').read_text())
    build=json.loads((ROOT/selected['selected_layout']/'build.json').read_text())
    files.update(ROOT/name for name in build['source_sha256'])
    records={str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)}
    archive=ROOT/'build/capture-column-qualification-evidence.tar.gz'
    assert not archive.exists()
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for name in records:tar.add(ROOT/name,arcname=name,recursive=False)
    seen={}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            assert member.name in records and member.name not in seen
            if member.islnk():result=seen[member.linkname]
            else:
                assert member.isfile()
                with tar.extractfile(member) as stream:result={'bytes':member.size,'sha256':streamhash(stream)}
            assert result==records[member.name],member.name
            seen[member.name]=result
    assert seen==records
    manifest=dict(files=records,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,read_back_verified=True,parts=[])
    combined=hashlib.sha256()
    with archive.open('rb') as stream:
        for i,block in enumerate(iter(lambda:stream.read(40*1024*1024),b'')):
            path=out/f'evidence.tar.gz.part-{i:04d}';path.write_bytes(block)
            digest=sha(path);assert digest==hashlib.sha256(block).hexdigest()
            combined.update(path.read_bytes());manifest['parts'].append(dict(name=path.name,bytes=len(block),sha256=digest))
    assert combined.hexdigest()==manifest['archive_sha256']
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.md').write_text('# Capture-column qualification\n\n'
        'Passing isolated-column tracking/refinement/placement checks, physical\n'
        'routing iterations, independent references and excluded isolation attempts.\n'
        'See [the report](../../docs/capture-column-qualification.md). This is not\n'
        'a full bank, full array or manufacturing qualification.\n\n'
        'The manifest verifies every archive member and all split parts. Concatenate\n'
        'the numbered parts in order and restore into an empty scratch directory.\n'
        'Earlier checkpoints remain unchanged. No simulation was left running.\n')
    print(json.dumps({key:manifest[key] for key in ['archive_bytes','read_back_verified','parts']}),flush=True)


if __name__=='__main__':main()
