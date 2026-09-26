"""Archive full grid-readout evidence with hard-link-aware read-back checks."""
from pathlib import Path
import argparse
import hashlib
import json
import tarfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--runs',type=Path,required=True)
a=p.parse_args();runs=a.runs.resolve()
out=ROOT/'checkpoints/grid-readout';assert not out.exists()
workflow=json.loads((runs/'manifest.json').read_text())
assert len(workflow['runs'])==4
assert all('seconds' in r for r in workflow['runs'].values())
files={p for d in [runs,ROOT/'build/row-power-grid-20260924'] for p in d.rglob('*')
       if p.is_file() and '__pycache__' not in p.parts}
files.update(ROOT/p for p in [
    'scripts/qualify-grid-readout.py','scripts/status-grid-readout.py',
    'scripts/audit-grid-readout-fixtures.py',
    'scripts/report-grid-readout.py','scripts/verify-grid-readout-references.py',
    'scripts/checkpoint-grid-readout.py','scripts/simulate-array-strips.py',
    'scripts/finish-column-capture.py','scripts/check-column-capture-reference.py',
    'scripts/analyze-strip-recovery.py','scripts/diagnose-functional-camera.py',
    'scripts/build-overview.py','docs/grid-readout.md','docs/grid-readout-section.html',
    'docs/assets/grid-readout.png','simulations/grid-readout.json','PICK_UP_HERE.md',
    'README.md','docs/README.md','CHANGELOG.md','NEXT_STEPS.md','COMPLETION_PLAN.md',
    'docs/completion-dashboard.html','circuits/output-buffer.spice'])
files.add(ROOT/'docs/capture-tile-plan.md')
files.add(ROOT/'docs/row-power.md')
files.add(ROOT/'scripts/resume-grid-readout-references.py')
def streamhash(f):
    h=hashlib.sha256()
    for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def sha(p):
    with p.open('rb') as f:return streamhash(f)
manifest={'scope':json.loads((ROOT/'simulations/grid-readout.json').read_text())['scope'],
          'files':{str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)}}
archive=ROOT/'build/grid-readout-evidence.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
    for name in manifest['files']:tar.add(ROOT/name,arcname=name,recursive=False)
verified={}
with tarfile.open(archive,'r|gz') as tar:
    for member in tar:
        assert member.name in manifest['files'] and member.name not in verified
        if member.islnk():
            assert member.linkname in verified
            record=verified[member.linkname]
        else:
            assert member.isfile()
            with tar.extractfile(member) as f:record={'bytes':member.size,'sha256':streamhash(f)}
        assert record==manifest['files'][member.name],member.name
        verified[member.name]=record
assert verified==manifest['files']
manifest.update(archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),parts=[],read_back_verified=True)
out.mkdir(parents=True)
combined=hashlib.sha256()
with archive.open('rb') as f:
    for i,block in enumerate(iter(lambda:f.read(40*1024*1024),b'')):
        part=out/f'evidence.tar.gz.part-{i:04d}';part.write_bytes(block)
        digest=sha(part);assert digest==hashlib.sha256(block).hexdigest()
        combined.update(part.read_bytes())
        manifest['parts'].append({'name':part.name,'bytes':len(block),'sha256':digest})
assert combined.hexdigest()==manifest['archive_sha256']
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'README.md').write_text(f'''# Full grid-readout checkpoint

{len(files)} files, {manifest['archive_bytes']} compressed bytes, {len(manifest['parts'])} parts. Every archive member, hard-link target, split part and concatenated archive was read back and verified.

Archive SHA-256: `{manifest['archive_sha256']}`.

Concatenate the numbered parts in filename order, verify the hash, and restore into an empty scratch directory. Preserve earlier checkpoints. Use the same pinned tools/PDK container with the restored repository at `/foss/designs`. Read `docs/grid-readout.md` and `simulations/grid-readout.json` for results, limits and scope; this is not a full-camera or tapeout qualification.
''')
print(json.dumps({k:manifest[k] for k in ['archive_bytes','archive_sha256','read_back_verified']}),flush=True)
