# Standalone row checkpoint — 2026-09-20

The archive preserves twelve completed standalone reset diagnostics, the
instrumented full-chip failure and short capture smoke run, exact decks/models,
raw traces, topology audits, scripts, report and plot. It is not a full-chip
qualification pass. Shared feedback is omitted from the standalone controls.

All three rows have identical local device records after renaming; extracted
capacitances differ. The isolated tests do not reproduce the failure. Next:
restore shared readout and supply/clamp circuitry in explicit stages.

Paths inside `evidence.tar.gz` are repository-relative. Restore into an empty
scratch directory, verify files using the SHA-256 values in `manifest.json`,
then selectively copy only missing build artifacts. Do not overwrite current
source files. The pinned Docker/PDK toolchain is required to run the decks;
container-local PDK installations are not included. The previous streamed-frame
archive is a recorded dependency for the original full-chip baseline comparison.

```sh
mkdir /tmp/ois-standalone-row-restore
tar -xzf checkpoints/standalone-row/evidence.tar.gz -C /tmp/ois-standalone-row-restore
```

See [the report](../../docs/standalone-row.md) for the exact boundary substitutions
and reproduction commands. Raw waveforms suffice to regenerate plots; duplicate
NPZ caches are omitted. `scripts/checkpoint-standalone-row.py` refuses to overwrite
an existing archive and verifies every archived member after writing it.
