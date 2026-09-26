# Physically joined compact tile — 2026-09-26

Contains the joined GDS and physical checks, raw/audited RC models, all 54
matrix transients and 72 references, initial dark controls, source snapshots,
input geometry and handoff. Every archive member was read back and SHA-256
checked. Read [the report](../../docs/compact-tile.md) for scope and limitations.
This is one capture/two reads on one tile, not a full bank or tapeout pass.

The numbered 40 MiB parts reconstruct the verified archive. From this directory:

```sh
cat evidence.tar.gz.part-* > /tmp/checkpoint-evidence.tar.gz
```

Check its SHA-256 against `archive_sha256` in `manifest.json` before extracting
into an empty scratch directory. Part hashes and lengths are also recorded.
