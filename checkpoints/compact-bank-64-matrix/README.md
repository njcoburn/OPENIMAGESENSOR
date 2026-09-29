# 64-column bank checkpoint — 29 September 2026

This package preserves the **exact implemented ground-grid GDS** used by the
completed alternating/inverse temperature matrix. It contains one row of 64
pixels and its 64-column readout bank, **not the assembled 64×64 chip**.

- Top cell: `compact_bank`; bounds: (−102, −117.8) to (2565.87, 952) µm.
- Overall size: 2667.87 × 1069.80 µm; column pitch: 40 µm.
- Extracted census: 642 MOS, 512 MIM plates, 64 diodes.
- Main Magic/KLayout DRC: zero errors; direct and resistor-collapsed LVS: pass.
- GDS SHA-256: `adb3f6afb6f6f5ac202c9097daf2c93adda1d99f515bcba69d35b1a91ecade8d`.

The original source is `build/compact-bank-c64-ground-grid-20260927/bank.gds`.
`bank.gds.gz` is deterministic, lossless gzip compression of that file and is
tracked in Git. The original build/verification metadata, reference and selected
extracted netlists, DRC/LVS records and frozen extraction/build helpers are copied
without alteration. `manifest.json` records included file hashes and sizes.
Paths inside the original reports retain their original workspace meaning.

## Inspect or reproduce the pictures

From the repository root, verify the package and the decompressed GDS:

```sh
python3 scripts/verify-current-bank-checkpoint.py
```

KLayout can open the compressed GDS directly. To inspect an uncompressed copy,
create a fresh directory and decompress there; the file expands to about 148 MB:

```sh
mkdir build/inspect-bank-checkpoint
gzip -dc checkpoints/compact-bank-64-matrix/bank.gds.gz > build/inspect-bank-checkpoint/bank.gds
```

With Docker and the repository's pinned tool image available:

```sh
bash scripts/run-tools.sh klayout -b -r scripts/render-current-bank-layout.py
bash scripts/run-tools.sh python3 scripts/annotate-current-bank-layout.py
python3 scripts/update-overview-sections.py
```

Rendering authenticates the decompressed GDS against `verification.json`, checks
its dimensions and uses the GF180 layer display palette. The annotations only
explain the rendered view; they do not alter the design. The HTML fragment is
in `docs/64x64-first-silicon-section.html`, loaded by both overview builders.
See the [labeled overview](../../docs/overview.html#current-device-layout).

## Evidence boundary

This is a portable layout checkpoint and selected physical evidence, not a
complete simulation archive or fabrication release. It does not include the
large raw waveforms, all alternate parasitic-placement netlists, upstream GDS
inputs or the PDK. Those dependencies must be recovered separately to rerun
the full electrical audits; their hashes in older reports do not imply that
their contents are available from a fresh clone. Large raw traces remain local
under `build/`; no external backup of those traces is created by this checkpoint.

The [completed matrix](../../docs/compact-bank-64-cross.md) contains eight
100/50 ns transients and 768 independently audited references, at 27/125 °C.
Maximum total error is 438.213 µV (500 µV limit); maximum saved-sample refinement
is 0.150 µV (10 µV limit). Uniform illumination, remaining corner/placement
coverage, real drivers, repeated rows and final-chip manufacturing checks remain
open. The layout is unfilled, and scoped DRC/LVS does not establish full-chip
manufacturing qualification.
