# Uniform illumination — bounded 64-column bank screens

Uniform dark, middle and bright illumination (**0, 80 and 240 pA per pixel**) now
pass at **27 °C and 125 °C**, reviewed through 30 September. All six cases are
complete: **12 transients and 1,152 independent references**. Together with
alternating/inverse, the five-pattern matrix contains 20 transients and 1,920
references. No simulations remain active. Remaining operating corners, individual
parasitic placements and full-chip qualification remain open.

| Dark case | Worst total error | Worst tracking | Sample refinement |
|---|---:|---:|---:|
| 27 °C | 248.852 µV | 14.965 µV | 0.133 µV |
| 125 °C | 411.912 µV | 81.559 µV | 0.149 µV |

All four independent checks pass; the total/tracking limit is 500 µV and both
refinement limits are 10 µV. Four transients finish 128 reads each, with all 384
references audited. The batch finished in **4.04 hours**, including audits;
all five containers exited with code 0 and the desktop alert was dismissed.
Both plots were visually reviewed. See the [review record](../simulations/compact-bank-uniform-dark-review-20260929.json).
No new simulations were launched during this review.

Integrity review verified all 1,709 distinct evidence files (911 manifest entries
per case), 18 launch dependencies and unchanged earlier matrix reports.

Each pattern uses four fresh transients: 100/50 ns at each temperature. Each
100 ns run solves 64 capture and 128 output references; the 50 ns run provides
refinement only. That is **384 independent references per batch**, or 12
transients and 1,152 references across all six uniform cases.

The physical layout, runner, strict tolerances, KLU solver, current-form drivers,
12 µs acquisition and 20 µs slots match the completed alternating/inverse matrix.
All twelve planned decks are checked against matching retained decks: only
illumination-source values change. Original runners, auditors and completed
reports remain unchanged.

## Independent audit

`scripts/report-bank-full-v3.py` is a separately versioned extension of v2. It
explicitly accepts the three uniform vectors, rejects mislabeled illumination,
regenerates and compares decks, and rechecks binary traces, saved samples, all
192 references and physical MIM event refinement. Accuracy limits remain
500 µV; saved-sample and physical-event refinement limits remain 10 µV.

A uniform image has no dark/bright neighbor contrast. That check is **not
applicable**, explicitly recorded as `contrast_order_applicable: false`, and
omitted from the uniform check dictionary. It is still required for alternating
and inverse cases. Uniform results retain four independent acceptance checks;
full-bank/corner and full-chip qualification flags remain false.

The 19 regression/adversarial tests cover all planned decks, illumination
validation, refinement thresholds, the retained 16-column audit, invalid reuse
provenance and watcher behavior after rendering or measured accuracy failures.
A separate complete 64-column control re-audit reproduced the existing
27 °C alternating result exactly before these runs were launched.

## Completed middle batch — 29 September

Both middle cases pass all four checks. Worst total error is 340.408/391.739 µV
at 27/125 °C against 500 µV; tracking is 30.395/72.481 µV. Saved-sample refinement
is 0.135/0.132 µV and physical-event refinement is 0.123/0.086 µV, against 10 µV.
Four transients finish 128 reads each; all 384 references are independently audited.
The batch finished in **3.65 hours**, including audits, with all five containers
exiting code 0. Both plots were reviewed; all 1,709 evidence files, 18 launch
dependencies and unchanged earlier artifacts verify.
[Review evidence](../simulations/compact-bank-uniform-middle-review-20260929.json).

## Completed bright batch — reviewed 30 September

Tag: `20260929-bright`. The user authorized moving on after middle completed.
All sources and reviewed results verified unchanged; the existing 19-test suite
covers the bright fixtures. No geometry, timing or tolerance change was needed.

- Plan: `build/compact-bank-uniform-plan-20260929-bright.json`.
- Live status: `build/compact-bank-uniform-watch-20260929-bright/status.json`.
- Watcher: `ois-bank-uniform-watcher-20260929-bright`.
- Desktop alert: `build/compact-bank-uniform-notification-20260929-bright.json`.

Both bright cases pass all four checks. Total error is 359.158/402.995 µV and
tracking is 3.028/15.919 µV at 27/125 °C, against 500 µV. Saved-sample refinement
is 0.065/0.061 µV; physical-event refinement is 0.065/0.044 µV, against 10 µV.
Four transients and 384 references finished in **3.97 hours**, including audits.
All five containers exited successfully. Both plots and saved evidence were
reviewed together with the completed automatic placement follow-on.
[Completion review](../simulations/compact-bank-overnight-review-20260930.json).

## Completed dark batch and reproduction

The launch tag is `20260929-dark`. Its exact commands, source hashes and
container IDs are recorded in:

`build/compact-bank-uniform-plan-20260929-dark.json`

Live status:

`build/compact-bank-uniform-watch-20260929-dark/status.json`

The watcher independently audits each completed pair, publishes the measured
pass or failure, and updates the uniform table and plots in the
[HTML overview](overview.html#compact-bank-64-uniform). A plot failure does not
prevent the other pair from being audited. A local desktop notification uses
the watcher status; see the current handoff for whether it is running.

The previous crossed batch took about **4.1 hours including audits**. Allow
roughly **4–6 hours for this first batch**, subject to convergence and machine
load. This is an estimate, not a completion guarantee. The four-hour transient,
30-minute per-reference and seven-hour watcher timeouts are diagnostic limits,
not predicted runtimes. Keep the workstation awake and Docker running.

Do not relaunch an existing tag or overwrite its output directories. Reproduction
uses fresh names:

```sh
bash scripts/run-tools.sh python3 scripts/test-bank-uniform.py --out build/uniform-tests-NEW
python3 scripts/launch-bank-uniform.py --pattern dark --tag NEW
bash scripts/run-tools.sh python3 scripts/render-bank-uniform.py --plan build/compact-bank-uniform-plan-NEW.json
```

Use a lowercase unique tag in place of `NEW`. The launcher starts detached Docker
containers and a watcher; it does not require this chat to remain open. Published
report filenames are intentionally unique per pattern/temperature, so a completed
case must not be silently overwritten by a repeat launch. Raw traces remain
local under `build/`.

All six uniform cases are reviewed and passing. See the [verification journal](verification-journal.html) for the complete matrix and rerun dependencies. Remaining corners, individual parasitic placements, real drivers,
4×64 repeated rows and the full 64×64 chip remain subsequent work.
