"""Restore checkpoint to a clean checkout; refuse to overwrite existing artifacts."""
from pathlib import Path
import tarfile,json,hashlib,io
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'checkpoints/manifest.json').read_text())
a=root/'checkpoints/gf180-3x3-size-study.tar.gz'
assert hashlib.sha256(a.read_bytes()).hexdigest()==m['archive_sha256'],'Archive checksum mismatch'
with tarfile.open(a,'r:gz') as tar:
 members=tar.getmembers()
 assert {t.name for t in members}==set(m['files'])
 for t in members:
  dest=root/t.name
  assert t.isfile() and not Path(t.name).is_absolute() and '..' not in Path(t.name).parts
  assert not dest.exists(),f'Refusing to overwrite {dest}; restore into a clean checkout.'
  assert hashlib.sha256(tar.extractfile(t).read()).hexdigest()==m['files'][t.name],t.name
 for t in members:
  dest=root/t.name;dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_bytes(tar.extractfile(t).read())
print(f'Restored and verified {len(members)} checkpoint files.')
