"""Archive only this power-feed stage and read back every archived member."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parents[1]
out = ROOT/'checkpoints/row-power'
assert not out.exists(), 'Preserve checkpoints; never overwrite evidence'
files = set()
for d in sorted((ROOT/'build').glob('row-power-*')):
    if not d.is_dir():
        continue
    for result in d.glob('*/result.json'):
        r = json.loads(result.read_text())
        assert 'returncode' in r, f'Run still active: {result}'
    files.update(p for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.update(ROOT/p for p in [
    'scripts/diagnose-row-power.py','scripts/prepare-array-strips.py',
    'scripts/audit-array-strip-rc.py','scripts/audit-row-power-geometry.py',
    'scripts/reduce-strip-resistors.py','scripts/verify-strip-resistor-models.py',
    'scripts/report-row-power.py','scripts/checkpoint-row-power.py',
    'scripts/check-column-capture-reference.py','scripts/build-overview.py',
    'scripts/extend-row-power-watchdog.py',
    'docs/row-power-section.html',
    'README.md','docs/README.md','CHANGELOG.md','COMPLETION_PLAN.md','NEXT_STEPS.md',
    'docs/completion-dashboard.html',
    'docs/row-power.md','docs/assets/row-power.png','simulations/row-power.json',
    'PICK_UP_HERE.md','build/size-study/20um/build/pixel_physical.gds',
    'build/array-strip-power2um-20260924/r1c64/strip.gds',
    'build/array-strip-power2um-20260924/r1c64/rc-port.spice',
    'build/array-strip-power2um-20260924/r1c64/rc-audit.json',
    'build/array-strip-power2um-20260924/r1c64/extraction.json',
    'build/array-strip-capture40-klu-27-100-20260924/r1c64-rc-port/transient/test.spice',
    'build/array-strip-capture40-klu-27-100-20260924/r1c64-rc-port/buffer.spice'])
def digest_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()
manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':digest_file(p)}
          for p in sorted(files)}
archive=ROOT/'build/row-power-evidence.tar.gz'
assert not archive.exists()
with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
    for p in sorted(files):
        tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
seen=set()
with tarfile.open(archive,'r|gz') as tar:
    for member in tar:
        assert member.isfile() and member.name in manifest
        h=hashlib.sha256();size=0
        with tar.extractfile(member) as f:
            for block in iter(lambda:f.read(1024*1024),b''):
                h.update(block);size+=len(block)
        assert {'bytes':size,'sha256':h.hexdigest()}==manifest[member.name],member.name
        seen.add(member.name)
assert seen==set(manifest)
out.mkdir(parents=True)
parts=[]
with archive.open('rb') as f:
    for i,block in enumerate(iter(lambda:f.read(40*1024*1024),b'')):
        part=out/f'evidence.tar.gz.part-{i:04d}'
        part.write_bytes(block)
        parts.append({'name':part.name,'bytes':len(block),'sha256':digest_file(part)})
report={'files':manifest,'archive_bytes':archive.stat().st_size,'archive_sha256':digest_file(archive),
        'parts':parts,'read_back_verified':True,
        'dependency':'Pinned tools/PDK container used by checkpoints/array-recovery; previous checkpoint unchanged.'}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'README.md').write_text(f'''# Row power-feed checkpoint

{len(manifest)} files; every archive member was read back and checked against its size and SHA-256. Partial and deliberately stopped runs are included with explicit classifications. Read `docs/row-power.md` for accepted evidence and remaining gates.

Archive SHA-256: `{report['archive_sha256']}`.

Concatenate the numbered parts in order, verify the archive checksum, and extract into an empty scratch directory. Do not overwrite existing evidence. Use the pinned tools/PDK container from the earlier array-recovery stage. SPICE include paths use its `/foss/designs` mount. The earlier 17.7 GB array-recovery archive remains unchanged; it is not duplicated here.
''')
print(json.dumps({k:report[k] for k in ['archive_bytes','archive_sha256','read_back_verified']}),flush=True)
