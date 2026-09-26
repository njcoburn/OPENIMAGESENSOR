"""Archive the routing follow-up without overwriting the prior physical checkpoint."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda:stream.read(1024*1024), b''):
        h.update(block)
    return h.hexdigest()


def sha(path):
    with path.open('rb') as f:
        return digest(f)


def main():
    out = ROOT/'checkpoints/bank-routing'
    out.mkdir(exist_ok=False)
    files = set()
    for name in ['capture-bank-routing-analysis-20260925','capture-bank-routing-controls-20260925',
                 'capture-bank-reset-gear-20260925','capture-bank-reset-reference-20260925']:
        files.update(p for p in (ROOT/'build'/name).rglob('*') if p.is_file())
    for name in ['scripts/diagnose-bank-routing.py','scripts/report-bank-routing.py',
                 'scripts/checkpoint-bank-routing.py','scripts/simulate-capture-bank.py',
                 'scripts/diagnose-capture-transient.py','scripts/run-tools.sh','scripts/build-overview.py',
                 'simulations/bank-routing.json','docs/bank-routing.md','docs/bank-routing-section.html',
                 'docs/assets/bank-routing.png','docs/overview.html','docs/completion-dashboard.html',
                 'docs/README.md','docs/capture-bank.md','README.md','PICK_UP_HERE.md',
                 'NEXT_STEPS.md','COMPLETION_PLAN.md','CHANGELOG.md']:
        files.add(ROOT/name)
    records = {str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)}
    archive = out/'evidence.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for name in records:
            tar.add(ROOT/name,arcname=name,recursive=False)
    seen = {}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            assert member.name in records and member.name not in seen
            if member.islnk():
                item = seen[member.linkname]
            else:
                assert member.isfile()
                with tar.extractfile(member) as f:
                    item = dict(bytes=member.size,sha256=digest(f))
            assert item == records[member.name]
            seen[member.name] = item
    assert seen == records
    manifest = dict(files=records,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
                    read_back_verified=True, prior_checkpoint='checkpoints/capture-bank',
                    prior_manifest_sha256=sha(ROOT/'checkpoints/capture-bank/manifest.json'))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.md').write_text('''# Shared-bank routing diagnosis

Eight direct-DC resistance controls, saved-result audit, bounded reset controls,
exact runners/decks/models/raw outputs, report and handoff. Every archive member
has been read back and hash-verified. No full-readout pass is claimed.

Restore `evidence.tar.gz` into an empty scratch directory. The unchanged prior
`checkpoints/capture-bank` supplies the original physical bank and 16 static
controls used by the analysis; its manifest hash is recorded here. Review
archived source snapshots before copying any over current work.

See [the measured report](../../docs/bank-routing.md).
''')
    print(json.dumps(dict(files=len(records),archive_bytes=manifest['archive_bytes'],read_back_verified=True)))


if __name__ == '__main__':
    main()
