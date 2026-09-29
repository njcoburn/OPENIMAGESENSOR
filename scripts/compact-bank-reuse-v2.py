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
    assert old['phase']=='full', 'Reuse requires a full transient'
    execution=old['transient']
    assert execution['completed'] and not execution['timed_out'] and execution['returncode']==0 and not execution['errors']
    assert execution==json.loads((directory/'transient/execution.json').read_text())
    for key,value in expected.items():
        default={'driver_form':'current','method':'trap','acquisition_us':10,'sample_offset_s':11.999e-6}.get(key)
        assert old.get(key,default)==value, f'Reuse setting mismatch: {key}'
    assert execution['deck_sha256']==verified['transient/test.spice']
    assert old['model_sha256']==verified['tile.spice']==hashlib.sha256(model.encode()).hexdigest()
    assert (directory/'.spiceinit').read_text()==spiceinit
    assert (directory/'trace-reader.py').read_bytes()==reader.read_bytes()
    original_tile = recorded_tile((directory/'transient/test.spice').read_text())
    assert normalized_deck((directory/'transient/test.spice').read_text(),original_tile)==normalized_deck(deck,tile), 'Regenerated transient fixture differs'
    return old,dict(source_directory=str(directory.relative_to(root)),
        evidence_manifest=str(manifest.relative_to(root)),evidence_manifest_sha256=sha(manifest),
        source_hashes=verified,regenerated_fixture_matches=True,
        source_run_completed=old['completed'],
        scope='Complete transient reused after identity checks; overall source run may have interrupted references. Reference reuse, if requested, is audited separately.')


def recorded_tile(deck):
    """Retained decks use the tool-container path, including when read on host."""
    paths=[line.split(maxsplit=1)[1] for line in deck.splitlines()
           if line.startswith('.include ') and line.endswith('/tile.spice')]
    assert len(paths)==1, 'Expected exactly one tile include'
    return paths[0]


def audit_reference(directory, name, manifest, root, deck, reader):
    """Return a verified finished DC solve, or None for interrupted/missing work."""
    d=directory/name
    if not (d/'execution.json').exists():return None
    execution=json.loads((d/'execution.json').read_text())
    if not execution['completed']:return None
    hashes=json.loads(manifest.read_text())['evidence_hashes'];verified={}
    for filename in ['test.spice','execution.json','ngspice.log','op.raw']:
        path=d/filename;key=str(path.relative_to(root))
        assert key in hashes, f'Missing previously recorded hash: {key}'
        verified[filename]=sha(path)
        assert verified[filename]==hashes[key], f'Changed reuse artifact: {key}'
    assert not execution['timed_out'] and execution['returncode']==0 and not execution['errors']
    assert execution['deck_sha256']==verified['test.spice'] and execution['points']==1
    original=(d/'test.spice').read_text()
    assert normalized_deck(original,recorded_tile(original))==normalized_deck(deck,recorded_tile(deck)), 'Regenerated reference fixture differs'
    ix,data=reader.trace(d/'op.raw')
    import numpy as np
    assert data is not None and len(data)==1 and np.isfinite(data).all(), 'Incomplete reference trace'
    return execution,ix,data,verified
