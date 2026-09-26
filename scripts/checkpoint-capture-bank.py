"""Archive shared-bank physical checks and all coupled-row diagnostics."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def streamhash(stream):
    digest=hashlib.sha256()
    for block in iter(lambda:stream.read(4*1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def sha(path):
    with path.open('rb') as stream:return streamhash(stream)


def main():
    out=ROOT/'checkpoints/capture-bank';out.mkdir(exist_ok=False)
    files=set()
    for directory in (ROOT/'build').glob('capture-bank-*'):
        if directory.is_dir():
            files.update(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.update(ROOT/name for name in [
        'scripts/build-capture-bank.py','scripts/verify-capture-bank.py',
        'scripts/simulate-capture-bank.py','scripts/report-capture-bank.py',
        'scripts/screen-capture-bank-dc.py',
        'scripts/audit-capture-bank.py',
        'scripts/checkpoint-capture-bank.py','scripts/diagnose-capture-transient.py',
        'scripts/run-tools.sh','scripts/build-overview.py',
        'checkpoints/capture-column-preparation/capture-column.spice',
        'build/capture-column-routed-v8-20260925/column.gds',
        'build/capture-column-routed-v8-20260925/verification.json',
        'build/grid-readout-20260924/27-100/r1c64-rc-port/array.spice',
        'build/grid-readout-20260924/27-100/r1c64-rc-port/buffer.spice',
        'build/grid-readout-20260924/27-100/r1c64-rc-port/transient/test.spice',
        'docs/capture-bank.md','docs/capture-bank-section.html',
        'docs/assets/capture-bank.png','simulations/capture-bank.json',
        'docs/capture-tile-plan.md','docs/README.md','README.md',
        'PICK_UP_HERE.md','NEXT_STEPS.md','COMPLETION_PLAN.md','CHANGELOG.md',
        'docs/completion-dashboard.html'])
    records={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)}
    archive=ROOT/'build/capture-bank-evidence.tar.gz';assert not archive.exists()
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for name in records:tar.add(ROOT/name,arcname=name,recursive=False)
    seen={}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            assert member.name in records and member.name not in seen
            if member.islnk():result=seen[member.linkname]
            else:
                assert member.isfile()
                with tar.extractfile(member) as stream:result=dict(bytes=member.size,sha256=streamhash(stream))
            assert result==records[member.name],member.name
            seen[member.name]=result
    assert seen==records
    manifest=dict(files=records,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
                  read_back_verified=True,parts=[])
    combined=hashlib.sha256()
    with archive.open('rb') as stream:
        for i,block in enumerate(iter(lambda:stream.read(40*1024*1024),b'')):
            path=out/f'evidence.tar.gz.part-{i:04d}';path.write_bytes(block)
            digest=sha(path);assert digest==hashlib.sha256(block).hexdigest()
            combined.update(path.read_bytes())
            manifest['parts'].append(dict(name=path.name,bytes=len(block),sha256=digest))
    assert combined.hexdigest()==manifest['archive_sha256']
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.md').write_text('# Shared physical capture bank\n\n'
        '64-column and two-column physical verification, rejected wide-strap control,\n'
        'raw extraction, diagnostic capacitance approximations and coupled-row runs.\n'
        'See [the report](../../docs/capture-bank.md) for precise qualification limits.\n\n'
        'Every archive member and split part has been read back and hash-verified.\n'
        'Concatenate numbered parts in order and restore into an empty scratch\n'
        'directory. Earlier checkpoints remain unchanged. The pinned EDA image\n'
        'supplies the PDK and tools; no manufacturing or full-array pass is implied.\n')
    print(json.dumps({key:manifest[key] for key in ['archive_bytes','read_back_verified','parts']}),flush=True)


if __name__=='__main__':main()
