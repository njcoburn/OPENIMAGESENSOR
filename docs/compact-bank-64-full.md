# Complete 64-column readout with distributed ground return

**Completed and reviewed on 28 September: both selected screens pass.** All
four transients finish the 3.98 ms schedule with 128 reads each. Each 100 ns case
has 64 capture and 128 output references, independently audited: 384 references
total. All five checks pass for both temperature/pattern pairs.

| Case | Worst total error | Worst tracking error | Maximum saved-sample 100/50 ns difference |
|---|---:|---:|---:|
| 27 °C alternating | 372.606 µV | 17.486 µV | 0.133 µV |
| 125 °C inverse | 438.213 µV | 57.086 µV | 0.129 µV |
| Limit | 500 µV | 500 µV | 10 µV |

Physical-event refinement is 0.135/0.099 µV, also below 10 µV. Worst total error
occurs at column 1 in the nominal late scan and column 0 in the hot first scan.
The hot case has 61.8 µV of remaining total-error margin. This establishes these
selected cases; untested patterns and operating corners remain open.

All four simulation containers and the completion watcher exited with code 0.
No audit or rendering failure occurred. Both plots were reviewed, and all
**1,711 distinct evidence files** in the nominal/hot manifests (913/909 entries)
were rehashed without mismatches. The batch completed about 3.1 hours after
launch. The nominal 100 ns transient and 64 capture references were reused;
the other three transients and 320 references were newly simulated.

[Nominal audit](../simulations/compact-bank-64-full.json) ·
[Hot audit](../simulations/compact-bank-64-full-hot.json) ·
[Completion review](../simulations/compact-bank-completion-review-20260928.json) ·
[Plots and all samples](overview.html#compact-bank-64-full)

**Next:** run 27 °C inverse and 125 °C alternating, each at 100/50 ns with 192
references at 100 ns. Then add uniform dark/middle/bright at both temperatures,
placement and process/wire/supply checks, and local supply/reference measurements.
Use fresh directories. No new batch was launched during this review.

The 27 September attempts remain unchanged. At the historical stop, nominal
100 ns had all 128 sample instants and 64/192 references; nominal 50 ns had 124
sample instants, and hot 100/50 ns had 120/114. Partial traces are diagnostic
evidence and cannot resume a SPICE solve.

The 100 ns runs supply the independent references; the 50 ns runs check
numerical refinement without additional references. All four read every column
twice. The two pairs cover two temperature/pattern combinations, not their full
cross-product or complete bank qualification.

The layout is `build/compact-bank-c64-ground-grid-20260927`, unchanged from
the [selected diagnostic](compact-bank-64-read-probes.md). Acquisition is
12 µs within the same 20 µs slots. Physical MIM terminals are saved in both
runs. Real parasitics, physical devices and strict tolerances are retained.

## Versioned runner and compatibility checks

`scripts/simulate-compact-bank-v2.py` preserves the original runner, whose
hash is an immutable dependency of earlier reports. Its default is still
10 µs acquisition. The new `--acquisition-us 12` changes only ACQ falling
edges and sample offsets; it does not move selection or reset controls.
`--deck-only` emits an explicitly unqualified diagnostic deck.
`--reference-timeout` bounds each reference separately; up to eight workers
are supported. That original v2 runner still rejects 12 µs reuse. The new
`scripts/simulate-compact-bank-v3.py` preserves its decks and adds an explicit
timing-aware path through `compact-bank-reuse-v2.py`. It checks acquisition and
sample offsets, schedule, settings, model and normalized fixture equality,
source hashes, execution completion, finite/monotonic/full-duration binary
records and every sample control window. Overall source-run completion is
separate from transient completion, so interrupted references do not discard a
finished transient.

`--reuse-references` accepts only independently completed references whose
recorded hashes and regenerated frozen-state decks match. It copies those files
and solves missing/interrupted references in the fresh run. The new independent
`report-bank-full-v2.py` checks provenance as well as every waveform sample,
reference and error, accepting the expected output-directory include difference.
The original auditor and all prior hash-pinned runners remain unchanged.

Sixteen new resume/deck tests, eight auditor/adversarial tests and two watcher
regressions pass. Rendering failures cannot skip a pending pair, and measured
accuracy failures remain completed audits. A real
16-column control reuses all 32 samples and 48 references and passes an independent
binary/deck audit, with exactly zero change in sampled/reference voltages and
reported errors. [Control evidence](../simulations/compact-bank-resume-control.json).
The [snapshot](../simulations/compact-bank-resume-snapshot-20260928.json) records
268 hashes before reuse and verifies the original plan hashes. Newly recorded
hashes protect subsequent reuse; they are not retrospective proof of unrecorded
27 September bytes.

Four tests cover original-default deck equality at 2/16/64 columns, exact
reproduction of the archived passing 12 µs selected deck, the single intended
full-deck waveform change and all 128 sample windows, and disjoint windows for
all supported widths. The full-bank result still needs independent waveform
and reference auditing.

```sh
bash scripts/run-tools.sh python3 scripts/test-bank-v2-timing.py \
  --out build/compact-bank-v2-deck-regression-new
```

## Reproduction

Use fresh directories. The completed launch configuration is
`build/compact-bank-resume-plan-20260928.json`; preserve its completed runs.
`launch-bank-resume.py` creates explicitly named detached containers and a new
plan, refusing existing output paths. `finish-bank-resume.py` reads that plan
instead of the old watcher's fixed paths. Completed audits retain accuracy
failures and keep full-bank/full-chip qualification flags false.

The resumed transient watchdog is 14,400 s, each reference is bounded at 1,800 s,
and four reference workers are used. The watcher stops waiting after seven hours
without stopping simulators, so an expired watcher requires a direct process
check. The retained nominal transient took 152.45 minutes with earlier concurrent
work; this is a measurement of that attempt, not a deadline for the fresh ones.

Run the tests before starting another long simulation:

```sh
bank_full_lights=$(python3 -c "print(','.join(['0','240']*32))")
bash scripts/run-tools.sh python3 scripts/simulate-compact-bank-v3.py \
  --layout build/compact-bank-c64-ground-grid-20260927 \
  --out build/compact-bank-c64-grid-full100-new \
  --lights-pa "$bank_full_lights" --temperature 27 --step-ns 100 \
  --solver klu --acquisition-us 12 --timeout 14400 \
  --reference-timeout 1800 --reference-workers 4 --save-mim-terminals
bash scripts/run-tools.sh python3 scripts/simulate-compact-bank-v3.py \
  --layout build/compact-bank-c64-ground-grid-20260927 \
  --out build/compact-bank-c64-grid-full50-new \
  --lights-pa "$bank_full_lights" --temperature 27 --step-ns 50 \
  --solver klu --acquisition-us 12 --timeout 14400 \
  --transient-only --save-mim-terminals
```

The previous 99-minute full-transient extrapolation is a planning estimate,
not a measured runtime for this grid. References add wall time. Raw evidence
is local under `build/`, ignored by Git, and must be copied separately or
reproduced on a fresh clone.

## Limits

This is one capture and two scans with behavioral drivers and an external ADC
fixture. The 50 ns run is a waveform comparison without its own DC references.
Hot and other illumination patterns, process/wire/supply corners, shunt
placements, local supply/bias checks, repeated rows, real decoding/drivers and
exact-chip optical/manufacturing checks remain open.

The hot pair uses `--temperature 125`, reversed illumination `240,0` repeated
32 times, four reference workers and separate `hot-inverse100`/`hot-inverse50`
output directories. The completion watcher audits each finished pair and
refreshes the overview; it never promotes partial traces to a pass.
