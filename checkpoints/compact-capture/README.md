# Compact capture-column checkpoint — 2026-09-26

Includes accepted isolated-column and abutment GDS/DRC/LVS, all 60 completed
transients and 36 references, capacitor controls, raw and audited extraction,
the excluded first layout, default-generator regression, source snapshots,
primitive inputs and handoff. Every archive member was read back and SHA-256
checked. Extract into an empty scratch directory.

[Report and scope](../../docs/compact-capture.md). No physical pixel join,
shared bank, startup or full-chip qualification is implied.

The numbered 40 MiB parts reconstruct the verified archive. From this directory:

```sh
cat evidence.tar.gz.part-* > /tmp/checkpoint-evidence.tar.gz
```

Check its SHA-256 against `archive_sha256` in `manifest.json` before extracting
into an empty scratch directory. Part hashes and lengths are also recorded.
