# Complete the bank's alternating/inverse temperature matrix

**Completed; reviewed 29 September.** Both new cases pass all five independent
checks. All four transients completed 128 reads each, with all 384 matched
references audited. All simulations and the watcher exited with code 0, without
audit or rendering failures. The batch plus audits took about 4.1 hours.

| New case | Worst total error | Worst tracking | Saved-sample refinement |
|---|---:|---:|---:|
| 27 °C inverse | 387.179 µV | 17.529 µV | 0.134 µV |
| 125 °C alternating | 430.383 µV | 81.527 µV | 0.150 µV |
| Limit | 500 µV | 500 µV | 10 µV |

Physical-event refinement is 0.135/0.099 µV. Worst total errors occur in the
27 °C late scan at column 0 and the 125 °C first scan at column 1.
Both new plots were reviewed, and **1,707 distinct evidence files** from the
909-entry manifests were verified without mismatches. All 10 launch source
hashes match, and the earlier reviewed reports remain unchanged.

Together with the earlier pair, alternating and inverse patterns pass at both
temperatures: eight full transients and 768 references. The matrix maximum total
error remains 438.213 µV, leaving 61.8 µV of margin to 500 µV. Uniform illumination,
other operating/placement conditions and full-chip qualification remain open.
No further simulations were launched during this review.

[27 °C inverse audit](../simulations/compact-bank-64-inverse27.json) ·
[125 °C alternating audit](../simulations/compact-bank-64-alternating125.json) ·
[Review evidence](../simulations/compact-bank-cross-review-20260929.json) ·
[Matrix and plots](overview.html#compact-bank-64-cross)

## Scope and retained jobs

| Case | 100 ns run | 50 ns run |
|---|---|---|
| 27 °C inverse | `build/compact-bank-c64-cross-inverse27-100-20260928` | `build/compact-bank-c64-cross-inverse27-50-20260928` |
| 125 °C alternating | `build/compact-bank-c64-cross-alternating125-100-20260928` | `build/compact-bank-c64-cross-alternating125-50-20260928` |

All four are fresh full transients through 3.98 ms, with 128 readouts per run.
Each 100 ns run requests 64 capture and 128 output references: **384 new references**
total. The 50 ns runs compare numerical refinement without their own references.
The physical layout remains `build/compact-bank-c64-ground-grid-20260927`.
Acquisition remains 12 µs inside 20 µs slots, with KLU, current-form drivers,
trapezoidal integration, strict tolerances and physical MIM terminal saves.
Accuracy limits stay 500 µV and refinement limits stay 10 µV.

The exact commands and image identity are recorded in
`build/compact-bank-cross-plan-20260928.json`. Progress and independent audit
outcomes are in `build/compact-bank-cross-watch-20260928/status.json`.
Check Docker state alongside the dated status. The four containers are named
`ois-bank-cross-{inverse27,alternating125}-{100,50}-20260928`, with watcher
`ois-bank-cross-watcher-20260928`. Preserve these completed runs; no job from this batch remains active.

Each transient has a four-hour watchdog, each reference has a 30-minute bound,
and four reference workers are used. The watcher waits seven hours and does not
stop simulators if it expires. These are bounds, not predicted durations. The
preceding batch and audits took about 3.1 hours under different concurrent work.

## Validation and reporting

The unchanged v3 simulator and v2 independent full-bank auditor already support
both cases. The new launcher checks the inherited runner, auditor, layout/model
hashes and fresh outputs before starting work. Six preflight/regression checks
pass: batch counts/unique paths, invalid tags, all four generated decks, wrong
renderer temperature, accuracy-failure reporting, and continued watching after
a rendering failure. Each deck matches its earlier same-temperature/timestep
control except for exactly 64 reversed illumination-source values. Models,
controls, saved nodes, timing and tolerances match.

`finish-bank-cross.py` independently audits each completed pair before publishing
`simulations/compact-bank-64-inverse27.json` or
`simulations/compact-bank-64-alternating125.json`. Measured accuracy failures are
retained as completed audits. `render-bank-cross.py` shows all four combinations
in one table and plots each new pair after audit. Pending cells have no pass claim.
The earlier report, renderer and simulation sources are preserved.

The Windows notification was delivered and dismissed. Its retained PID/state is
`build/compact-bank-cross-notification-20260928.json`. The local popup reported successful completion. The monitor exits after
dismissal; it is not watching a new batch.

For a deliberately new experiment, first inspect existing outputs and use a fresh
tag and test directory. The launcher refuses existing output/report/container
names. These preflight tests assume the new case reports have not been published:

```sh
bash scripts/run-tools.sh python3 scripts/test-bank-cross.py \
  --out build/compact-bank-cross-tests-new
python3 scripts/launch-bank-cross.py --tag new-tag
```

## Next gate

Uniform dark/middle/bright illumination at both temperatures is next. The current
auditor only accepts alternating/inverse, so preserve it and verify a new uniform
reporting path before launching the six new cases (12 transients and 1,152
references with the same refinement scheme). Operating corners, parasitic
placement and local supply/reference checks also remain open. The prior hot case had 61.8 µV of margin to the total-error
limit. After broader bank coverage passes, move to 4×64 repeated rows with real
decoders/drivers and full-column loading, then the full 4096-pixel chip and
manufacturing checks. Full-bank/corner and full-chip qualification flags remain
false. Preserve all passing and failing controls.
