"""Archive the routing revisions, rejected control, DC evidence and reset diagnostic."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def digest(stream):
    h=hashlib.sha256()
    for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def sha(path):
    with path.open('rb') as f:return digest(f)


def main():
    out=ROOT/'checkpoints/bank-reinforcement';out.mkdir(exist_ok=False)
    directories=['capture-bank-c2-v3-20260925','capture-bank-c2-v4-20260925',
                 'capture-bank-c2-v5-20260925','capture-bank-c64-v4-20260925',
                 'capture-bank-c64-v5-20260925','capture-bank-v4-dc-20260925',
                 'capture-bank-v5-dc-20260925','capture-bank-local-controls-20260925',
                 'capture-bank-v5-reset-20260925']
    files=set()
    for name in directories:
        d=ROOT/'build'/name;assert d.is_dir(),d
        files.update(p for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.update(ROOT/name for name in [
        'scripts/build-capture-bank.py','scripts/verify-capture-bank.py',
        'scripts/diagnose-bank-routing.py','scripts/screen-capture-bank-dc.py',
        'scripts/simulate-capture-bank.py','scripts/diagnose-capture-transient.py',
        'scripts/report-bank-reinforcement.py','scripts/checkpoint-bank-reinforcement.py',
        'scripts/run-tools.sh','scripts/build-overview.py',
        'docs/bank-reinforcement.md','docs/bank-reinforcement-section.html',
        'docs/bank-routing.md','docs/capture-bank.md',
        'docs/assets/bank-reinforcement.png','simulations/bank-reinforcement.json',
        'docs/overview.html','docs/completion-dashboard.html','docs/README.md','README.md',
        'PICK_UP_HERE.md','NEXT_STEPS.md','COMPLETION_PLAN.md','CHANGELOG.md'])
    records={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)}
    archive=ROOT/'build/bank-reinforcement-evidence.tar.gz';assert not archive.exists()
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for name in records:tar.add(ROOT/name,arcname=name,recursive=False)
    seen={}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            assert member.name in records and member.name not in seen
            if member.islnk():item=seen[member.linkname]
            else:
                assert member.isfile()
                with tar.extractfile(member) as f:item=dict(bytes=member.size,sha256=digest(f))
            assert item==records[member.name],member.name
            seen[member.name]=item
    assert seen==records
    manifest=dict(files=records,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
                  read_back_verified=True,parts=[],dependencies={
                      name:sha(ROOT/name/'manifest.json') for name in ['checkpoints/capture-bank','checkpoints/bank-routing']})
    combined=hashlib.sha256()
    with archive.open('rb') as f:
        for i,block in enumerate(iter(lambda:f.read(40*1024*1024),b'')):
            p=out/f'evidence.tar.gz.part-{i:04d}';p.write_bytes(block)
            assert sha(p)==hashlib.sha256(block).hexdigest()
            combined.update(p.read_bytes())
            manifest['parts'].append(dict(name=p.name,bytes=len(block),sha256=sha(p)))
    assert combined.hexdigest()==manifest['archive_sha256']
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.md').write_text('''# Physical bank routing reinforcement

Verified two- and 64-column routing revisions, rejected spacing control,
48 audited DC records across original/intermediate/selected designs (original
records are in the dependency checkpoint), 13 local-wire controls and a bounded
coupled reset diagnostic. No full-readout accuracy pass is claimed.

Every archive member and numbered part has been read back and hash-verified.
Concatenate parts in order and restore into an empty scratch directory. Do not
unpack archived source snapshots over current work. The manifests of the prior
capture-bank and bank-routing checkpoints are recorded as dependencies.

See [measurements and reproduction](../../docs/bank-reinforcement.md).
''')
    print(json.dumps(dict(files=len(records),archive_bytes=manifest['archive_bytes'],read_back_verified=True)))


if __name__=='__main__':main()
