# Compact shared two-column bank — 2026-09-26

Contains the joined two-column GDS, physical audits, raw/audited models,
100 matrix transients and 240 references, input geometry, source snapshots
and handoff. Every archive member was read back and SHA-256 checked.
Read [the report](../../docs/compact-bank.md) for scope and limitations.
This is one capture/two reads per column, not a full bank or tapeout pass.

The numbered 40 MiB parts reconstruct the verified archive. From this directory:

```sh
cat evidence.tar.gz.part-* > /tmp/checkpoint-evidence.tar.gz
```

Check its SHA-256 against `archive_sha256` in `manifest.json` before extracting
into an empty scratch directory. Part hashes and lengths are also recorded.
