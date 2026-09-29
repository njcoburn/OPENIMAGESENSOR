"""Verify the portable layout package, including its exact decompressed GDS."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'checkpoints/compact-bank-64-matrix'


def digest(stream):
    hasher, size = hashlib.sha256(), 0
    while chunk := stream.read(1024 * 1024):
        hasher.update(chunk)
        size += len(chunk)
    return hasher.hexdigest(), size


def main():
    manifest = json.loads((PACKAGE / 'manifest.json').read_text())
    for relative, record in manifest['files'].items():
        path = (ROOT / relative).resolve()
        assert path.is_relative_to(ROOT), f'Path outside repository: {relative}'
        with path.open('rb') as stream:
            actual_hash, actual_size = digest(stream)
        assert (actual_hash, actual_size) == (record['sha256'], record['bytes']), relative
    with gzip.open(PACKAGE / 'bank.gds.gz', 'rb') as stream:
        actual_hash, actual_size = digest(stream)
    verification = json.loads((PACKAGE / 'verification.json').read_text())
    assert actual_hash == manifest['gds']['sha256'] == verification['gds_sha256']
    assert actual_size == manifest['gds']['uncompressed_bytes']
    for filename, expected in verification['hashes'].items():
        path = PACKAGE / filename
        if path.is_file():
            with path.open('rb') as stream:
                assert digest(stream)[0] == expected, filename
    print(f"Verified {len(manifest['files'])} files and exact GDS ({actual_size:,} bytes).")


if __name__ == '__main__':
    main()
