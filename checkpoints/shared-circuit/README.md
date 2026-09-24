# Shared-circuit checkpoint — 2026-09-20

Ten bounded diagnostic results, including explicit solver aborts and watchdog
stops, plus the prepare-only full-model reconstruction audit. The original
third-row failure remains unresolved. No circuit/model correction is accepted.

The useful fast pair is:

- `build/shared-circuit/no-clamps-ideal-short-20260920`: early ideal-supply abort.
- `build/shared-circuit/no-clamps-ideal-norton-reset-20260920`: same reset-source
  terminal equation in Norton form, completes its short diagnostic window.

This is a different event from the original finite-supply full-chip failure.
Do not conflate the two. See [the report](../../docs/shared-circuit.md).

The archive is split into `evidence.tar.gz.part-*` files, each at most 40 MiB.
The manifest records each part's size/hash, the concatenated archive hash and
every archived member's hash. The archive includes exact decks, models, raw traces, logs, partition/substitution
audits, result comparisons, scripts and plots. It also preserves the ngspice 46
release-source archive, unmodified local executable, configure log and the three
inspected solver source files. The executable requires the pinned OSIC container
libraries. Installed simulator/PDK files and working source builds were unchanged.
Original full-chip input/capture dependencies are in the recorded standalone-row
archive; prior version-comparison provenance is a separate recorded dependency.

Restore to an empty scratch directory, verify each member against `manifest.json`,
then selectively restore missing build inputs. Paths are repository-relative;
never unpack over current source files. Do not overwrite earlier results.

```sh
mkdir /tmp/ois-shared-circuit-restore
cat checkpoints/shared-circuit/evidence.tar.gz.part-* | tar -xz -C /tmp/ois-shared-circuit-restore
```

`scripts/checkpoint-shared-circuit.py` refuses to overwrite existing parts or its
build-directory archive. It verifies all members and the concatenated parts.
No simulation is running at
this checkpoint. Next: instrument a matched local build on the fast control,
then validate any supported change on the original event and full-frame gates.
