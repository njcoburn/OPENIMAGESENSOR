"""Validate a completed bank transient against previously recorded evidence hashes.

Only the output-directory-dependent tile include may differ in the regenerated
deck. Trace contents, fixture settings and model identity must match the source.
The caller independently rechecks trace completeness and sampled controls.
"""
import hashlib
import json
from pathlib import Path

ARTIFACTS=('result.json','tile.spice','.spiceinit','runner.py','trace-reader.py',
           'transient/test.spice','transient/execution.json','transient/ngspice.log',
           'transient/stream.raw')


def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def normalized_deck(text,tile):
    include=f'.include {tile}'
    lines=text.splitlines()
    assert lines.count(include)==1, 'Expected exactly one tile include'
    return '\n'.join('.include __AUDITED_TILE__' if line==include else line for line in lines)


def audit(directory,manifest,root,expected,deck,tile,model,spiceinit,reader):
    directory=directory.resolve();root=root.resolve();manifest=manifest.resolve()
    hashes=json.loads(manifest.read_text())['evidence_hashes']
    verified={}
    for name in ARTIFACTS:
        path=directory/name;key=str(path.relative_to(root))
        assert key in hashes, f'Missing previously recorded hash: {key}'
        verified[name]=sha(path)
        assert verified[name]==hashes[key], f'Changed reuse artifact: {key}'
    old=json.loads((directory/'result.json').read_text())
    assert old['completed'] and old['phase']=='full', 'Reuse requires a complete full transient'
    execution=old['transient']
    assert execution['completed'] and not execution['timed_out'] and execution['returncode']==0 and not execution['errors']
    assert execution==json.loads((directory/'transient/execution.json').read_text())
    for key,value in expected.items():
        default={'driver_form':'current','method':'trap'}.get(key)
        assert old.get(key,default)==value, f'Reuse setting mismatch: {key}'
    assert execution['deck_sha256']==verified['transient/test.spice']
    assert old['model_sha256']==verified['tile.spice']==hashlib.sha256(model.encode()).hexdigest()
    assert (directory/'.spiceinit').read_text()==spiceinit
    assert (directory/'trace-reader.py').read_bytes()==reader.read_bytes()
    assert normalized_deck((directory/'transient/test.spice').read_text(),directory/'tile.spice')==normalized_deck(deck,tile), 'Regenerated transient fixture differs'
    return old,dict(source_directory=str(directory.relative_to(root)),
        evidence_manifest=str(manifest.relative_to(root)),evidence_manifest_sha256=sha(manifest),
        source_hashes=verified,regenerated_fixture_matches=True,
        scope='Reused complete transient only; all requested independent references are newly simulated.')
