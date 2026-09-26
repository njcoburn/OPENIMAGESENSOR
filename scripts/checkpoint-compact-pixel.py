"""Preserve and read back the compact pixel and bounded bank experiments."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def streamhash(handle):
    digest = hashlib.sha256()
    while block := handle.read(4*1024*1024):
        digest.update(block)
    return digest.hexdigest()


def sha(path):
    with path.open('rb') as handle:
        return streamhash(handle)


def main():
    out = ROOT/'checkpoints/compact-pixel'
    out.mkdir(parents=True,exist_ok=False)
    roots = [ROOT/'build/compact-pixel-v1-20260926', ROOT/'build/bank-equivalent-20260926',
             ROOT/'build/strip-default-regression-20260926']
    roots += list((ROOT/'build').glob('compact-pixel-imaging-*-20260926'))
    roots += [ROOT/f'build/bank-{model}-{kind}-20260926'
              for model in ['raw','equivalent'] for kind in ['op','reset']]
    files = {p for root in roots for p in root.rglob('*') if p.is_file()}
    for name in ['scripts/build-compact-pixel.py','scripts/prepare-array-strips.py',
                 'scripts/report-compact-pixel.py','scripts/checkpoint-compact-pixel.py',
                 'scripts/simulate-array-strips.py','scripts/diagnose-functional-camera.py',
                 'scripts/simulate-capture-bank.py','scripts/compact-bank-resistors.py',
                 'scripts/run-tools.sh','circuits/output-buffer.spice',
                 'build/layout-probe-verified/nfet_probe.gds',
                 'build/size-study/20um/build/array-primitives/photodiode.gds',
                 'simulations/compact-pixel.json','docs/compact-pixel.md',
                 'PICK_UP_HERE.md','NEXT_STEPS.md','COMPLETION_PLAN.md']:
        files.add(ROOT/name)
    manifest = dict(scope='Compact unfilled pixel development and failed bounded full-bank controls.',
                    files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)})
    archive = out/'evidence.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for name in manifest['files']:
            tar.add(ROOT/name,arcname=name,recursive=False)
    verified = {}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            assert member.name in manifest['files'] and member.name not in verified
            if member.islnk():
                digest = verified[member.linkname]
            else:
                assert member.isfile()
                with tar.extractfile(member) as handle:
                    digest = streamhash(handle)
            assert digest == manifest['files'][member.name]
            verified[member.name] = digest
    assert verified == manifest['files']
    manifest.update(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.md').write_text('''# Compact pixel checkpoint — 2026-09-26

Extract `evidence.tar.gz` into an empty scratch directory. Every archive member
was read back and checked against the SHA-256 manifest.

Includes 40 µm-pitch pixel and 2×2 GDS, extraction, both LVS paths, main DRC,
eight nominal/hot imaging attempts (seven complete) and matched references, the isolated negative
RST capacitance diagnostic, original-strip regression and four failed bounded
bank controls. Exact runner snapshots and primitive inputs are retained.

Read [the report](../../docs/compact-pixel.md) before interpreting results.
This is small unfilled development geometry, not a complete camera or tapeout pass.
''')
    print(f'Verified {len(files)} files; {archive.stat().st_size} archive bytes')


if __name__ == '__main__':
    main()
