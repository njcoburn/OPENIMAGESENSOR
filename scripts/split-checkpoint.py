"""Split a verified evidence.tar.gz into the repository's 40 MiB parts.

Requires the checkpoint's existing archive SHA-256 manifest. Reads every part
back and checks the concatenated hash before removing the original archive.
"""
from pathlib import Path
import argparse
import hashlib
import json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('checkpoint',type=Path)
    a=p.parse_args();d=a.checkpoint.resolve()
    archive=d/'evidence.tar.gz';manifest_path=d/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    assert not list(d.glob('evidence.tar.gz.part-*')), 'Parts already exist'
    with archive.open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==manifest['archive_sha256']
    combined=hashlib.sha256();parts=[]
    with archive.open('rb') as f:
        for i,block in enumerate(iter(lambda:f.read(40*1024*1024),b'')):
            part=d/f'evidence.tar.gz.part-{i:04d}'
            with part.open('xb') as output:output.write(block)
            checked=part.read_bytes();assert checked==block
            combined.update(checked)
            parts.append(dict(name=part.name,bytes=len(checked),sha256=hashlib.sha256(checked).hexdigest()))
    assert combined.hexdigest()==manifest['archive_sha256']
    manifest.update(parts=parts,archive_bytes=archive.stat().st_size,parts_read_back_verified=True)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    readme=d/'README.md'
    readme.write_text(readme.read_text()+'''\nThe numbered 40 MiB parts reconstruct the verified archive. From this directory:

```sh
cat evidence.tar.gz.part-* > /tmp/checkpoint-evidence.tar.gz
```

Check its SHA-256 against `archive_sha256` in `manifest.json` before extracting
into an empty scratch directory. Part hashes and lengths are also recorded.
''')
    archive.unlink()
    print(f'Verified {len(parts)} parts; concatenated archive hash matches')


if __name__=='__main__':main()
