# Changelog

## 2026-10-04 — Checkpoint completed five-device bank verification

Preserve all 18 independently passing reports from the sequence completed on
2 October: 36 transients, 3,456 references, no failures/timeouts, controller exit 0.
Worst total error is 456.591 µV and tracking is 215.322 µV (500 µV limits);
maximum sampled timestep difference is 0.465218 µV (10 µV limit).
Check completed runner/reference counts, report identity and pinned launch
sources; save a tracked final status and completion record. This checkpoint
uses the completed independent raw audits rather than rerunning simulations.

Update the overview/journal, current status and PICK_UP_HERE.md with exact
sources, local/raw versus committed evidence, replay instructions and next
supply/wiring/placement checks. Full-chip and exhaustive-bank qualification
remain open. No new verification batch is launched.

## 2026-09-30 — Five-device correction and overnight process queue

Review the extended-age model comparison: fast-corner total error falls from
604.318 µV with three capture devices to 396.116 µV with five. Build a separate
five-device physical column and 64-column bank (898 MOS / 512 MIM / 64 diodes).
Physical DRC/LVS, all capture chains, unchanged storage geometry and 40 µm
abutment pass. Retain four failed routing attempts and preserve old evidence.

Twelve extracted port/far transients and 72 fresh references pass independent
raw audits; worst total is 192.269 µV and placement sensitivity is 0.053 µV.
Version the simulation and audits for 13 µs acquisition and 15.5 µs ADC reset.
Check ten full-bank decks, twenty reference corner selections, legacy timing
compatibility and continuation guards. Preserve a portable physical checkpoint.

Start a detached, gated queue of 18 cases / 36 transients / 3,456 references.
Use three workers, an eight-hour transient watchdog and a twelve-hour job limit;
new stages stop launching after 48 hours. Preserve failed results and stop later
stages unless all independent audits pass. Update overview/journal, add a fixed-
candidate one-command replay, and enable a local completion/review alert.
Full-bank electrical results are pending. Windows automatic idle sleep is disabled.

## 2026-09-30 — Review interrupted full-bank candidate batch

Audit all three completed coarse runs and 576 references. Preserve all three
fine traces that hit the four-hour transient timeout near the end. Check only
available prefix samples; no incomplete pair is qualified. Typical/SS coarse
total errors are 391.959/445.375 µV; FF remains above limit at 602.413 µV.
Available fine FF samples also exceed 500 µV. Keep the process queue stopped,
record the distinction between timeout and electrical failure, and add the
review, plot, journal entry and handoff. No simulator batch was restarted.

## 2026-09-30 — Launch gated full-bank candidate verification

Push the reviewed checkpoint first as `06889e5`. Build a separate 64-column
three-NMOS capture candidate: 770 MOS, 512 MIM plates, 64 diodes, with unchanged
ground-grid geometry. Magic/KLayout DRC and direct/collapsed LVS pass; audit
all 64 capture chains. Retain a portable physical checkpoint with electrical
qualification explicitly pending.

Version the runner/auditor for 12.5 µs acquisition and both internal stack nodes.
Six fresh small-bank controls reproduce the retained sampled HOLD and coarse
reference errors exactly. Check ten full-bank decks, twenty reference-corner
selections, transition guards and frozen dependencies. Start six detached
125 °C typical/SS/FF jobs. Queue mixed corners, room-temperature cases and the
remaining typical-process patterns behind audited passes: 18 cases, 36 transients,
3,456 references in total. Preserve failed stages and stop further progression.
Add live overview/journal status, a durable controller and local desktop alert.

## 2026-09-30 — Build and verify the physical three-device capture switch

Combined switch/timing controls pass, then a separate physical column and
small bank pass Magic/KLayout DRC, direct/collapsed LVS and 40 µm abutment.
Keep the original footprint and upper capacitor geometry. Extracted typical,
SS and FF total errors stay below 259 µV across port/far placement; placement
sensitivity stays below 0.044 µV. Complete 18 transients and 108 references,
independent raw audits and topology rejection tests. Preserve failed attempts.
Add the candidate GDS view, one-command fixed-candidate electrical rerun,
versioned profile, overview/journal results and next full-bank handoff.
The original full-bank checkpoint and process-failure evidence remain unchanged.

## 2026-09-30 — Screen capture-switch candidates through complete cycles

Complete and independently review 20 two-column transients and 120 matched
references. Three series NMOS capture devices pass selected typical/SS/FF checks;
FF total error improves from 1240.756 to 410.653 µV. Two devices still fail at
596.505 µV. A separate original-switch 12.5 µs acquisition screen improves SS
tracking from 281.789 to 206.737 µV while preserving ADC-reset nonoverlap.
Add exact parent-fixture regeneration, raw-result review, four rejection tests,
versioned rerun profile, overview plot/table, journal history and handoff.
These are model-only results; existing physical GDS and full-bank failures remain.

## 2026-09-30 — Review process failures and investigate storage leakage

Both 125 °C inverse MOS corners finish but fail total error: SS 512.924 µV and
FF 2000.323 µV vs 500 µV. All other selected checks pass. Four transients and
384 references are independently audited in 2.92 hours; both plots and 1,740
unique evidence files are reviewed. Simulator exits are 0; watcher exit 1 reports
the measured failures.

Retained-data decomposition separates SS tracking from FF storage-drift behavior.
Five balanced direct-current probes identify the NMOS capture switch as the
main selected FF storage-discharge path. The first voltage-subtraction clamp
check failed at pA precision and is retained; direct clamp/MIM probes restore
current balance within 0.00254 pA without material DC voltage change.

Six model-only switch-length and four series-stack DC cases complete. Three
series devices reduce tested net leakage by about 70%, but no physical layout
or capture/readout correction is qualified. Add comparison plots, evidence,
journal history and a handoff for candidate transients plus SS acquisition timing.
No new hours-long batch is running; all existing pinned evidence remains intact.

## 2026-09-30 — Embed the journal and launch MOS process variations

Place an expandable full verification journal first in the overview, with its
own navigation link; refreshing the journal updates both views. Add a separate
process catalogue and pending-result table.

Version the runner and auditor for explicit typical/SS/FF/FS/SF MOS selection.
Diode/MIM and supply/wire remain nominal. All installed ngspice model files are
hashed; transient and independently regenerated reference decks must use the
same corner. Fourteen regression/adversarial/watcher tests pass; the retained
full-bank typical hot audit reproduces exactly.

Four two-column process-control transients and 12 references complete. SS passes;
FF fails late-scan total accuracy at 1240.756 µV against 500 µV, while tracking
is 3.057 µV and sample/event refinement is 0.096/0.098 µV. Storage drops
1.348/1.540 mV between scans, consistent with retention sensitivity, not a proven
root cause. Preserve the initial assertion failure and the subsequent independent
review; no tolerance or accuracy threshold is relaxed.

Launch the bounded current-layout SS/FF 125 °C inverse batch: four fresh
100/50 ns transients and 384 references, with independent auditing and durable
exit/status records. Results remain pending; no next batch auto-starts. Update
the handoff, profile and journal with this scoped failure and launch evidence.

## 2026-09-30 — Explain verification and establish a running rerun record

Add `docs/verification-journal.html` with physical/electrical/software test
explanations, acceptance criteria, the 12-case selected bank matrix, milestone
history, remaining gates and pixel-change dependencies. Add a machine-readable
baseline catalogue and a standard-library refresh/check command that validates
retained report hashes, fixture identity, counts and reported limit consistency.
The command does not launch simulations or re-audit raw evidence.

Document the fixed pitch/pin/device assumptions, dated auditor dependencies,
output-name collisions and local-only build artifacts that must be addressed for
a general single-command rerun. Link the journal from the overview and handoff;
propose a baseline-tested controller before the next corner profile. Preserve
all pinned simulation/audit sources and existing results. No long runs launched.

## 2026-09-30 — Review completed bright and overnight placement batches

Uniform bright passes at 27/125 °C with 359.158/402.995 µV total error against
500 µV. All five illumination patterns now pass at both temperatures: 20
transients and 1,920 independent references, at typical process and nominal
supply/wire conditions.

The authorized automatic follow-on jointly relocates 67 conserved shunt totals
and passes at 27 °C alternating / 125 °C inverse. Total error is
372.235/437.952 µV; maximum HOLD/STORE change is 1.527 µV against 10 µV.
It adds four transients and 384 references. Bright and placement batches took
3.97 and 3.87 hours respectively, including independent audits.

All ten simulation/audit containers exited successfully. Visually reviewed all
four new plots and verified 3,347 distinct evidence files, including the frozen
42-dependency continuation configuration and prior review records, without hash
failures. Recorded the final review in
`simulations/compact-bank-overnight-review-20260930.json`; preserved the original
automated bright review and frozen simulation/audit sources. Updated the overview,
handoff and plans; 101 unique overview anchors validate. No new batch was launched.

Next are bounded process/wire/supply-corner preparation, remaining individual
placements and local supply/reference checks before real drivers and repeated
rows. Full-bank corner coverage and full-chip qualification remain open.

## 2026-09-29 — Queue an audited overnight continuation

At the user's request, prepare one automatic follow-on batch after bright passes:
full-bank joint shunt placement at 27 °C alternating and 125 °C inverse, four
transients and 384 references. A new auditor verifies exact conserved-total
endpoint changes, the existing accuracy/refinement checks, and HOLD/STORE
sensitivity to matching retained baselines. Fifteen placement tests and five
continuation guard tests pass; the full-bank control reproduces exactly.

The detached controller waits for passing bright audits, verifies every new
evidence hash, checks clean predecessor exits and frozen dependencies, then
launches one fresh placement batch with its independent watcher. It records
failures and stops progression, updates the handoff, and supports a desktop alert.
The automated bright review does not claim visual inspection of plots. No broader
corner, individual-placement or full-chip qualification is implied.


## 2026-09-29 — Review middle illumination and launch bright

Both middle cases pass all four checks: 340.408/391.739 µV total error and
30.395/72.481 µV tracking at 27/125 °C, against 500 µV. Saved-sample refinement
is 0.135/0.132 µV and physical-event refinement is 0.123/0.086 µV, against 10 µV.
Four transients and 384 references are complete; the batch finished in 3.65 hours.
All five containers exited with code 0. Reviewed both plots and verified 1,709
distinct evidence files (911 entries per report), 18 launch dependencies and
unchanged earlier artifacts.

Started the authorized bright batch (240 pA/pixel) at both temperatures, with
four fresh transients, 384 planned references, the independent watcher and
desktop alert. Sources, timing, tolerances and layout remain unchanged; existing
19-test coverage includes these decks. Bright results are pending. Updated the
overview and handoffs; broader corner/placement and full-chip checks remain open.


## 2026-09-29 — Launch uniform middle illumination

Started 80 pA/pixel at 27/125 °C with fresh 100/50 ns runs: four transients and
384 planned independent references. The independent watcher and desktop alert
are enabled. Verified prior launch dependencies and reviewed dark artifacts
unchanged; the existing 19 passing tests cover these middle decks. Runner,
auditor, physical layout, timing and strict tolerances are unchanged.

Updated the uniform matrix and current handoffs. Middle results remain pending;
bright illumination will follow after review. Full-bank/corner and full-chip
qualification remain open.


## 2026-09-29 — Review the completed uniform-dark batch

Both 27/125 °C cases pass all four independent accuracy/refinement checks.
Worst total error is 248.852/411.912 µV against 500 µV, and tracking is
14.965/81.559 µV. Saved-sample refinement is 0.133/0.149 µV and physical-event
refinement is 0.134/0.100 µV, against 10 µV. Four transients finish 128 reads
each and all 384 matched references are audited.

The batch plus audits finished in 4.04 hours; all five containers exited with
code 0, with no audit/render failure. Reviewed both plots and verified all
1,709 distinct evidence files (911 manifest entries per case), 18 launch
dependencies, and unchanged earlier matrix reports. Updated the overview and
handoffs to middle illumination next, then bright. No new runs were launched
during this review. Full-bank/corner and full-chip qualification remain open.

[Dark results](docs/compact-bank-64-uniform.md) ·
[Review evidence](simulations/compact-bank-uniform-dark-review-20260929.json).

## 2026-09-29 — Start the first uniform-illumination batch

Added a separately versioned full-bank auditor accepting explicit uniform dark,
middle and bright patterns. It rejects mislabeled illumination and marks neighbor
contrast as not applicable for uniform scenes; accuracy and refinement limits
remain unchanged. Nineteen regressions pass, and all twelve planned decks change
only illumination-source values. The new auditor reproduces every sample,
reference summary, physical event and acceptance result of the completed nominal
64-column control exactly. The original evidence and source versions are preserved.

Launched uniform dark at 27/125 °C with 100/50 ns comparisons: four fresh
transients and 384 planned references, an independent completion watcher and
desktop alert. Middle and bright remain unstarted. Added the uniform coverage
table and updated handoffs; no new accuracy result is claimed at launch.

Also added a labeled exact-GDS single-pixel close-up to the overview, identifying
the three transistors, photodiode, clear aperture and wiring, and opened it in
the browser. The prior bank checkpoint is unchanged.

[Uniform coverage and reproduction](docs/compact-bank-64-uniform.md).

## 2026-09-29 — Checkpoint the completed matrix and show the actual device layout

Added a labeled exact-GDS view and pixel/readout close-up to the HTML overview,
with the 2,667.87 × 1,069.80 µm dimensions, functional callouts and a clear
distinction between the implemented 64-column bank/one pixel row and the planned
64×64 chip. The images are rendered from the authenticated ground-grid GDS.

Preserved the exact compressed GDS, reference/extracted netlists, scoped DRC/LVS
records and hash manifest in a portable Git-tracked checkpoint. Added rendering
and integrity-check instructions. Large raw simulation traces remain local.

This checkpoint collects the source, reports and documentation from the ground
return and acquisition fixes through the completed alternating/inverse matrix:
eight transients, 768 references, 438.213 µV maximum total error and 0.150 µV
maximum saved-sample refinement. Full-bank/corner and full-chip qualification
remain open. No new simulations were launched.

[Device layout](docs/overview.html#current-device-layout) ·
[Checkpoint and reproduction](checkpoints/compact-bank-64-matrix/README.md).

Checkpoint validation: 35 reuse, auditor, timing and resistor regressions pass;
all 363 Python scripts compile; the overview's 98 anchors and current layout
links resolve. All 27 packaged files and the exact decompressed GDS verify.
The rendered full view, close-up and labeled figure were visually inspected.

## 2026-09-29 — Review the completed alternating/inverse temperature matrix

Both new cases pass all five independent checks. The 27 °C inverse case has
387.179 µV worst total error and 17.529 µV tracking; 125 °C alternating has
430.383 µV total error and 81.527 µV tracking, against 500 µV. Saved-sample
refinement is 0.134/0.150 µV and physical-event refinement is 0.135/0.099 µV,
against 10 µV. All four new transients complete 128 reads each and both 100 ns
cases have all 192 matched references (384 total).

The new batch and its independent audits completed in about 4.1 hours. All five
containers exited with code 0; no audit/render failure occurred. Reviewed the
plots, verified all 1,707 distinct evidence files (909 entries per report), the
10 launch source hashes, and unchanged earlier reviewed reports.

Across both batches, all four alternating/inverse temperature combinations pass:
eight transients and 768 references, with 438.213 µV maximum total error and
0.150 µV maximum saved-sample refinement. Updated handoffs to uniform-illumination
coverage next; its auditor must be extended and checked before long runs. No new
simulations were launched. Full-bank/corner and full-chip qualification remain
open. [Results](docs/compact-bank-64-cross.md).

## 2026-09-28 — Launch the remaining alternating/inverse temperature cases

Started 27 °C inverse and 125 °C alternating at 100/50 ns in four fresh
containers, with 384 planned independent references. New launch, completion
watching and matrix rendering preserve the original runner/auditor and the
completed nominal/hot reports. Six checks pass; all four generated decks differ
from matched prior decks only in the 64 reversed illumination-source values.
No physical devices, parasitics, tolerances, timing or probes change.

The configured auditor will publish each measured pass/failure and update the
matrix/plots. Re-enabled the user's desktop notification for this batch. Results
remain pending. [Current handoff](PICK_UP_HERE.md) ·
[Reproduction](docs/compact-bank-64-cross.md).

## 2026-09-28 — Complete and review both full-bank selected screens

Both complete-bank cases pass their selected checks: 27 °C alternating and
125 °C inverse illumination, with 100/50 ns comparisons. All four transients
finish 128 reads each; both 100 ns cases have 192 independently audited references
(384 total). Worst total errors are 372.606/438.213 µV and output tracking is
17.486/57.086 µV, against 500 µV. Saved-sample refinement is 0.133/0.129 µV
and physical-event refinement is 0.135/0.099 µV, against 10 µV.

All simulation/auditor containers exited successfully, with no rendering failure.
Reviewed both plots and verified all 1,711 distinct files in the two manifests
(913 nominal and 909 hot entries). The completion notification was delivered.
Updated current handoffs and the next batch: 27 °C inverse and 125 °C alternating,
followed by uniform illumination and corner/placement coverage. No new runs were
launched during this review; full-bank/corner and full-chip qualification remain
open. [Results](docs/compact-bank-64-full.md).

## 2026-09-28 — Resume complete-bank qualification with audited reuse

Added a separately versioned runner and reuse auditor for 10/12 µs acquisition.
A completed transient can be reused when its overall source run was stopped
during references; partial transients remain rejected. Completed references
require matching frozen-state decks, execution records, binary values and
recorded hashes. The original runners and evidence remain unchanged.

The 16-column reuse control independently reproduces all 32 samples and 48
references exactly. Sixteen reuse/deck tests, eight auditor tests and four
original timing tests plus two watcher regressions pass. Rendering errors cannot
end the watcher before the remaining pair is audited. The pre-reuse snapshot contains 268 hashes and
explicitly distinguishes newly recorded hashes from the prior plan baseline.

Restored Docker/VNC and launched nominal/hot inverse 100/50 ns continuation
cases in fresh directories, with a configured independent completion watcher.
The nominal case reuses its complete transient and 64 capture references;
three fresh transients and 320 new references are planned. Full-bank accuracy
and refinement results remain pending. See [the handoff](PICK_UP_HERE.md).

## 2026-09-27 — Extend 16-column checks and diagnose 64-column ground return

The [16-column extension](docs/overview.html#compact-bank-16-extension) passes
its selected checks across **46 transients and 1,152 references**. Worst total
error is 433.171 µV and tracking is 301.667 µV
(500 µV limits). All five patterns at 27/125 °C have 100/50 ns comparisons;
the largest saved-terminal difference is 0.450 µV. All 19 individual
shunts plus their joint placement pass for the hot inverse pattern, with
0.105/0.137 µV maximum HOLD/STORE changes (10 µV limit). The separate
inverse-pattern layout–schematic response reaches 10.062 mV and has
no assigned acceptance threshold.

The 8 µm bus alone does not solve 64-column scaling: a matched column-62
readout fails at 1,994.440 µV total error. A new physical distributed ground
return **fails with 10 µs acquisition** at 547.178 µV total error and
340.253 µV tracking. Both main DRC checks and both LVS paths pass, and
a geometry audit restricts the change to ground metal/vias. The new bank is
2667.87 × 1069.80 µm, within the 2700 × 1100 µm budget. See the
[selected readout comparison](docs/overview.html#compact-bank-64-read-probes)
and [capture/ground diagnosis](docs/compact-bank-64-ground8.md).

Extending acquisition from 10 to 12 µs on that same grid **passes the selected
diagnostic** at 269.281 µV total error and 62.529 µV tracking. Only the
ACQ falling edges and sample times move; selection/reset and the 20 µs slot
budget stay unchanged. Three new matched references and an unchanged-prefix
comparison are audited. The separately versioned full-bank runner now supports
this timing. The nominal and hot inverse-pattern attempts were stopped at user
request before completing the full audit; see PICK_UP_HERE.md for retained
progress and the resume plan.

These are bounded development screens. Full 16-column corner/placement
coverage, the full 64-column schedule and its 192 references, real drivers,
repeated rows and exact 64×64 manufacturing qualification remain open.

Added bounded orchestration, independent binary/DC audits, seven adversarial
regressions, 96 exact reference-deck comparisons, ground-network diagnostics,
physical MIM probes, a verified distributed-return layout and geometry audits.
The overview includes plots, limits, reproduction and a dated provider PDK
comparison. Original failing runs and immutable manifests remain intact.

## 2026-09-27 — Expand the revised 16-column thermal/pattern screen

Added 13 transients and 528 independent references to the retained nominal
control. All selected checks pass across 14 transients/576 references: five
patterns at 27/125 °C, 432.966 µV worst total error and 301.658 µV output tracking.
Alternating-pattern 100→50 ns differences are 0.220/0.449 µV. Joint far-shunt
comparisons stay below 0.122 µV HOLD and 0.156 µV STORE. Contrast/brightness
ordering passes; the separate mixed-versus-uniform response reaches 88.972 µV.

Added bounded pattern orchestration, exact-regression-tested faster trace
sampling, independent binary-trace/DC auditing and a report with 2,453 evidence
hashes. Two sampling and fourteen reuse/schedule/progress tests pass. Updated
the overview with temperature/pattern plots, detailed tables, limits and handoff.
The physical layout is unchanged. Individual placements, other-pattern numerical
checks, schematic comparisons, corners, full-bank and chip qualification remain
open; no full tapeout pass is implied.

## 2026-09-27 — Qualify the 16-column trace and correct its ground bus

Provenance-checked transient reuse completes all 48 independent references.
The original nominal screen fails at 540.016 µV against 500 µV; a fresh 100 ns
run confirms 540.185 µV, with 0.185 µV maximum saved-sample difference.
Physical MIM probes identify ground motion at row deselection. Three extended
reference controls agree within 0.000136241 µV. The hot two-column reuse control
matches exactly; eight reuse and six schedule/progress regressions pass.

Widened only the physical M4 ground bus from 2 to 8 µm. Both main DRC checks
and both LVS paths pass with unchanged devices/reference netlist. A direct GDS
XOR audit verifies the sole rectangle change. The revised nominal 100 ns run
and all 48 references pass: 189.413 µV total error, 55.267 µV output tracking.
The 16-column bounding box grows 1.8 µm to 709.56 × 978.28 µm. Updated the
overview with the original failure, corrected result, comparison plot and
reproducible evidence hashes. Revised-bank hot/pattern/placement/timestep checks
remain open; no 64-column revision or full-chip tapeout pass is claimed.


## 2026-09-27 — Advance KLU bank simulations and refresh the overview

KLU resolves 64-column initialization/reset without changing devices, parasitics
or tolerances. The hot two-column accuracy control passes with 0.009070 µV
saved-terminal change. Eight-column alternating nominal/hot cases pass 24
references each (195.412/430.243 µV worst error); 200→100 ns comparisons are
0.170/0.401 µV. Gear has no observed runtime benefit; equivalent voltage-form
drivers abort initialization. Thirteen local tests pass.

Built a physically verified 16-column bank; its longer transient completes both
scans in 440 s. The 64-column run reaches 1.686001 ms and 14/128 scheduled
readout instants before a 900 s timeout. Neither bank has a new accuracy pass.
Added phase/runtime observations, retained all controls and updated the handoff.

Rechecked Run 3 dates, pricing, full-slot availability and exact die/core sizes.
Added a dated cost table, Los Angeles deadline conversions, conservative fit
diagram and release gates to the overview; validated anchors and Firefox
rendering. The full default core remains the viable planning envelope.
No full 64×64 chip, slot purchase or tapeout submission is implied.
[Latest overview](docs/overview.html#compact-bank-solver).

## 2026-09-27 — Restore VNC and diagnose compact-bank initialization

Restored Docker Desktop and the existing VNC workstation; opened the compact
64-column GDS in KLayout. Added compact tile/diode support to the resistor
reducer and deterministic audited-model input to the compact simulation runner.
Seven reducer tests and four schedule tests pass. A hot two-column reduction
control completes with 0.058281 µV maximum saved-sample difference. Four/eight-
column physical controls pass both main DRC and LVS paths; four columns complete
both scans, while eight recover through transient OP fallback and reach readout.
Reducing 1824 internal nodes still leaves the compact 64-column model at zero
samples after 180 s. Full-bank electrical qualification remains open.
[Diagnostic evidence](docs/compact-bank-initialization.md).

## 2026-09-26 — Build compact 64-column bank and preserve Git checkpoint

Committed and pushed the accumulated source, reports and evidence manifests;
about 32 GB of generated archives remain local and are now ignored by Git.
Built the compact 1×64 row/bank at 2627.76 × 978.28 µm. Both main DRC checks
and both LVS paths pass (642 MOS, 512 MIM, 64 diodes). Expanded the simulation
runner to 64 columns with nonoverlapping scans; four schedule tests and an
exact hot two-column sample regression pass. Both 180 s full-bank controls
remain incomplete: extracted initialization produces zero samples, while the
schematic reaches 1.785052 ms/76,919 samples. Physical fit is demonstrated;
full-bank electrical accuracy remains open. [Report](docs/compact-bank-64.md).

## 2026-09-26 — Verify compact shared two-column bank

Built two joined pixels/capture columns with shared physical reference MOS and
power/reference/capture/output buses at 40 µm pitch. Main DRC, direct LVS and
RC-collapsed LVS pass, along with 100 transients and 240 references across five
nominal/hot illumination patterns. Worst capture/readout error is 419.033 µV,
physical refinement 0.431 µV and selected placement sensitivity 0.038 µV.
Separate layout–schematic response reaches 5.821 mV; a neighbor illumination
change produces up to 26.670 µV output change. One capture and two reads per
column are tested. Compact 1×64, repeated frames and manufacturing remain open.
Docker restored by opening the Windows application; cancelled a stalled CLI
restart without interrupting Ubuntu. [Evidence and GDS view](docs/compact-bank.md).

## 2026-09-26 — Verify physically joined compact pixel/capture tile

Connected the compact pixel and column through extracted COL/VDD/GND routes.
Both main DRC and LVS paths pass; the 18 × 18 µm geometric aperture stays clear.
All 54 transients and 72 references pass the scoped capture/readout, timestep
and selected-shunt-placement checks. Worst total error is 419.404 µV; physical
refinement is 0.325 µV and sampled placement sensitivity stays below 0.018 µV.
The layout–schematic integrated-response shift reaches 3.922 mV and is recorded
separately. The test captures once and reads twice after pixel deselection/reset;
shared-bank and repeated-frame qualification remain open. Docker Desktop/WSL
access recovered after a transient environment interruption.
[Evidence and actual layout](docs/compact-tile.md).

## 2026-09-26 — Qualify compact 40 pF capture column

Repacked seven unchanged transistor devices and eight equal-area MIM plates
at 40 µm pitch. The selected column occupies 36.6 × 861.48 µm and passes
Magic/KLayout main DRC, direct/RC-collapsed LVS and adjacent-column spacing.
All 60 nominal/hot transients and 36 DC references pass: 165.716 µV tracking,
395.222 µV layout–schematic shift, 0.262 µV refinement, 0.024 µV independent
COL/BIAS shunt-placement sensitivity. The original generator mode retains
identical polygon geometry and direct extraction. Fixed solver-command
rewriting when reusing an already-SPARSE fixture, and reject simulator command
errors. Conditional MIM selection, raw extraction approximations, physical
pixel joining and shared-bank qualification remain open.
[Results and reproduction](docs/compact-capture.md).

## 2026-09-26 — Qualify compact reset-shunt approximation

Reproduced the isolated raw hot reset abort at 220.01 µs. Applied the existing
conserved-total shunt audit to a fresh copy and completed 12 nominal/hot
transients plus six extended-reference sets. Both isolated placements pass:
24.204 µV worst tracking, 2.573 µV refinement and 0.035 µV placement sensitivity.
The unchanged 2×2 boundary control passes. All other extracted records and
fixture statements are preserved. Raw distributed capacitance remains
diagnostic; compact capture and a physical joined tile remain next.
[Report and reproduction](docs/compact-reset.md).

## 2026-09-26 — Restore EDA access and build compact pixel

Confirmed Docker and the pinned ngspice 46 environment. Repacked unchanged
20 µm diode and transistor primitives at 40 µm pitch. Single-pixel and 2×2
controls pass Magic/KLayout main DRC and direct/RC-collapsed LVS. The 2×2
nominal/hot imaging screens reach 191.066/234.550 µV worst tracking error and
2.804/2.710 µV timestep differences. Seven of eight small-cell transients
complete; the isolated hot 100 ns run aborts at reset and retains an unqualified
negative extracted RST capacitance. Raw/reduced full-bank operating-point and
reset controls all time out at 180 s without samples. Original strip geometry
passes a regression DRC/LVS control. Preserved evidence and open limits in the
[compact-pixel report](docs/compact-pixel.md). No release geometry changed.

## 2026-09-25 — Replan 64×64 first silicon for wafer.space

User confirmed wafer.space GF180 and modest frame rate. Checked published slot
sizes: existing array and reinforced bank cannot fit, even before pads/controls.
Replaced accumulated 3×3-first planning with a compact-layout critical path and
archived the prior planning files intact. Added reproducible slot-fit arithmetic,
a candidate 40 µm-pitch block budget and a diagram. Added resistor-only star-mesh
preparation: 4239 nodes eliminated with device/capacitor records retained, audited
port/far models and five analytical/corruption tests. Optional coupled-runner input
reaudits the supplied equivalent model. Docker WSL integration is unavailable;
no new SPICE/DRC/LVS or runtime improvement is claimed. No release GDS changed.
[Plan](COMPLETION_PLAN.md) · [Fit study](docs/64x64-slot-fit.md) ·
[Solver preparation](docs/bank-solver-preparation.md).

## 2026-09-25 — Reinforce physical bank routing

Built two physically verified 64-column revisions with stronger supplies,
reference feeds and local buffer current paths. Worst nominal/hot static shift
falls from 5.331 to 1.320 mV over 1.2–2.0 V; some higher-input cases favor the
intermediate revision. Audited all 48 DC records and 13 contraction controls.
The 180 s coupled reset test times out during initialization without transient
samples. Preserved both revisions, rejected spacing control and runtime evidence.
[Measurements, scope and reproduction](docs/bank-reinforcement.md).

## 2026-09-25 — Diagnose shared-bank routing

Read back all 16 saved static traces and completed eight selective resistance
controls. VDD/PREF routing contributes to spatial spread; a 2.199 mV common
offset remains after idealizing supplies/references. The full-RC control is
bit-exact with the prior result. An ideal-wire coupled bank crosses reset to
0.25 ms; a physical-bank Gear attempt times out during initialization.
Preserved all diagnostics and explicit qualification limits in a new checkpoint.
[Measurements and reproduction](docs/bank-routing.md).

## 2026-09-25 — Implement the shared physical capture bank

Repeated the qualified column 64 times, placed the two shared reference devices,
and routed power, capture clocks, references and the output bus. Both main DRC
checks and both LVS paths pass with exact device parameters. Preserved the
rejected wide-strap control and all extracted RC. Sixteen isolated DC controls
complete, exposing millivolt-scale static spatial shifts. Coupled-row numerical
initialization and full readout accuracy remain open; no camera or tapeout pass
is claimed. [Results and reproduction](docs/capture-bank.md).

## 2026-09-25 — Qualify the physical capture column

Resolved the transient blocker using independent SPARSE fixtures with unchanged
error tolerances. All 48 nominal/hot runs complete; worst tracking error is
176.560 µV, timestep difference 0.318 µV and COL-shunt placement sensitivity
0.0125 µV. Revised supplies/vias/output routing reduce the largest schematic
shift from 2140.397 to 482.228 µV without changing any device. Both main DRC
checks and both LVS paths pass. Audited traces, references, rejected routing
attempts and solver controls are preserved in a new checkpoint. The shared
64-column bank remains next. [Report](docs/capture-column-qualification.md).

## 2026-09-25 — First physical capture column

Restored the Docker toolchain and built an isolated seven-transistor/eight-MIM
column. Magic and KLayout main DRC report zero errors; direct and RC-collapsed
LVS match with exact device parameters. Independent capacitor controls measure
40.0075/40.0425 pF at 27/125 °C, matching the installed model. Retained negative
COL-shunt extraction corrections and two capacitance-placement approximations;
their sensitivity and the incomplete capture transients remain unqualified.
No release layout or carrier change. [Report](docs/physical-capture-column.md).

## 2026-09-24 — Prepare the physical capture-column circuit

Exported a seven-transistor column and separate shared references/bias fixture;
verified all 512 repeated elements against the accepted 64-column deck. Prepared
three conditional eight-plate MIM storage banks using the archived area, fringe,
temperature and supported leakage terms. Checked serialized circuit expansion,
capacitor arithmetic, changed-clock rejection, provenance hashes and identical
regeneration. Archived the inputs and documented bottom-plate routing constraints
and inactive voltage-dependence terms. Physical verification awaits restoration
of Docker/WSL access; no new physical or transient pass is claimed.
[Preparation report](docs/capture-column-preparation.md).

## 2026-09-24 — Complete grid-row readout qualification

Completed four full 64-column SPARSE transients on the physical M5-grid row. Nominal/hot total errors 173.457/289.658 µV and timestep differences 3.897/3.703 µV pass the retained limits. All sampled controls pass; independent capture and selected output references are verified at double settling duration. Added reproducible workflow, fixture audits, per-column results/plot, physical tile implementation plan and a separate evidence checkpoint. Physical periphery, repeated/multirow operation, wire corners and startup remain open. [Report](docs/grid-readout.md).

## 2026-09-24 — Physical row power-grid diagnosis and improvement

Verified the 354 mV turn-on pulse and its resistance sensitivity; built an M5 power-grid candidate with distributed via arrays. Both DRC checkers and both LVS paths pass, with no added photodiode coverage. Full-wire-R+C turn-on loss falls to 42.574 mV nominal / 34.516 mV hot; nominal refinement and independent-solver controls agree. Both runs reach capture; independent acquisition references are checked at two settling durations. Full serial-output requalification, physical periphery, wire corners and startup remain open. Failed/slow solver controls are preserved separately. [Report](docs/row-power.md).

## 2026-09-24 — Full-row capture and routing recovery

Widened physical strip power rails and verified DRC/direct/RC-collapsed LVS. Added simultaneous transistor column capture and buffered serial output; the selected 40 pF/500 kΩ/12.4 kΩ circuit passes both 64-output nominal/hot accuracy screens (171.295/289.919 µV) and timestep refinement (4.317/4.439 µV). Preserved rejected candidates, incomplete numerical diagnostics and the still-unqualified legacy serial mode. Quantified new charging-current/power-grid and storage-area costs. Storage/periphery physical implementation, startup/full-chip/PVT and release gates remain open. [Report](docs/array-recovery.md).

## 2026-09-24 — Extracted 64-pixel strip tests

Added physical 1×64/64×1 strips and short controls, DRC/LVS, explicit wire-R/C audit, shared-readout settling and free-integration comparisons, timestep and reset-capacitance placement checks. Found long-row exposure skew and bright-pixel over-integration. Existing release layout and carrier unchanged. [Report](docs/array-strips.md).

## 2026-09-24 — Tested timing/bias and cold-pad proposals

- Retained slower-acquisition and intermediate-bias failures; validated the nominal combined 470/100 pF, 30 µs / 50 µs, 12.4 kΩ PREF and explicit 100 kΩ unused-pad termination candidate across 27 samples: 461.383 µV tracking, 5.620 µV drift, 0.278 µV first-frame refinement.
- Both terminated cold first-frame cases pass; selected FF/cold three frames give 152.650 µV tracking and 5.336 µV drift, with 0.300 µV refinement. Existing unbonded-pad hardware remains unchanged.
- Documented current/power, timing/exposure and physical-connection tradeoffs, plus tapeout/scaling gates. No full PVT, startup, distributed-R+C or manufacturing release claim.

## 2026-09-24 — Bounded full-camera load/PVT screen

- Screened eight initial conditions with per-condition stock DC bias, recomputed MOS-capacitance corners and full extracted-camera transient/DC readout checks: five pass; heavy capacitive load fails accuracy; two cold corners stop at DC watchdogs.
- Isolated board/sample capacitance effects and verified the heavy-load result within 5.701 µV at finer timestep. Hot-corner refinement agrees within 0.303 µV.
- Completed three frames under a 100 kΩ load: 27 samples, 5.550 µV frame-two/three drift and 191.889 µV maximum DC tracking error.
- Preserved exact models, runs, failed controls and matched references; documented cold unused-pad numerical sensitivity without promoting a diagnostic shunt as a camera fix. Startup and distributed-R+C qualification remain open.

## Earlier: three-frame and nominal readout checks — 2026-09-24

**The full extracted 3×3 camera completes three consecutive frames: 27/27 samples.** Brightness ordering passes: True; control-state checks pass: True. Frame-two/three maximum change is **5.733 µV** against the retained **50 µV** screen (pass).

All 27 matching DC references were checked. Maximum HOLD tracking error is **167.766 µV**, and ADCIN error is **166.826 µV**, against the **500 µV** screen (pass). Sampled bias agreement within 1%: True.

The model is unchanged from the successful single-frame run; only stop time changed to 10.25 ms. It retains the equivalent reset source, all clamp domains, full-layout wiring capacitance and a 1 µs maximum step. Constant illumination was repeated. Reset voltages and capacitor bias ranges are recorded; this is not changing-scene, startup, optical/noise, full-RC or fabrication qualification.

**Next:** Run a bounded full-chip load/process/voltage/temperature matrix, revalidating the frozen-capacitor approximation at each operating condition. Nonlinear startup and distributed wire resistance remain separate gates. No simulation remains running.

[Report and waveforms](docs/three-frames.md), `simulations/three-frames.json`, and verified evidence in `checkpoints/three-frames/`.


## Earlier: staged integration and full-frame success — 2026-09-21

**The full extracted 3×3 normal-operation candidate now completes a frame to 4.25 ms, with all nine pixels in the expected brightness order.** Only the 2 V / 1 Ω reset reference was rewritten as an electrically equivalent Norton source. The full chip model, all fifteen clamp domains, supply, control timing and tolerances are unchanged. The first six samples match the original failed trace within 0.060 µV. The 1 µs maximum-step rerun also completes all nine samples; maximum difference from 5 µs is 2.778 µV.

Staged shared-readout, buffer, ADC-load and finite-supply tests also pass on 3×3 and 4×4 array-core PEX models. The rail-diode control revealed a small numerical failure resolved by the same equivalent-source rewrite. The earlier stage-7 watchdog and other failed controls are retained.

**Next:** repeated full-chip frames and frame stability, matched DC transfer/settling reference, load/PVT checks, nonlinear startup and distributed wiring resistance. This is a first normal-operation imaging result, not fabrication qualification; MOS capacitors remain bias-frozen. No simulation remains running.

[Detailed report](docs/staged-integration.md), `simulations/staged-integration.json`, and verified evidence in `checkpoints/staged-integration/`.


## Earlier: physical array extension tests — 2026-09-20

**3×3, 4×3, 3×4 and 4×4 unfilled physical arrays all pass DRC/device LVS and complete three frames in both device-only and C-only PEX simulations.** Every sampled pixel has the expected brightness ordering. These use 100 Ω control drivers and independent column loads, without shared readout/pads/clamps/fill or distributed wiring resistance. An initial ideal-driver C-only 3×3 failure is retained separately. The original full-chip failure is unresolved; no simulation remains running.

[Results and exact scope](docs/array-extension.md), `simulations/array-extension.json`, and `checkpoints/array-extension/`. Next: integrate the shared readout into this parameterized, working array baseline, then restore supply/pad/clamp blocks in stages. Do not treat these core passes as complete-camera qualification.


## Shared-circuit numerical investigation — 2026-09-20

Shared camera/readout tests cross the third-row reset with zero or one supply-clamp domain; seven domains time out near the earlier row turn-off. A separate ideal-supply failure now reproduces in under a second and disappears when only the reset reference is expressed with the same terminal-current equation. This is numerical sensitivity in a different early control, not a resolved original third-row failure. The full-model nine-driver rewrite also times out before the target event. [All ten outcomes and scope](docs/shared-circuit.md).

Next: instrument the fast failed/completed pair, then test a supported change on the original finite-supply circuit. Exact evidence is archived in `checkpoints/shared-circuit/`; no simulation remains running.

## Standalone row investigation — 2026-09-20

All three extracted rows have identical local device/resistor records after renaming. All 12 isolated reset tests complete with staged capacitance/pad protection, third-row finite-supply and finer-step controls. The full-chip internal capture reproduces the earlier failure exactly; no causal device or fix is established. Shared circuitry and charge history remain outside the standalone checks. [Step-by-step results](docs/standalone-row.md).

Next: restore shared column/readout and supply/clamp circuitry in stages to minimize the failure. Exact inputs/results and the internal full-chip trace are archived in `checkpoints/standalone-row/`. No simulation remains running.

## Streamed nine-pixel attempt — 2026-09-20

The unchanged frame attempt crosses the earlier slowdown but aborts at **3.27002 ms** after 21.06 minutes, before third-row readout. Six samples and 17,764 points are preserved. This is an explicit timestep failure, not a watchdog stop. The failure coincides with the third-row reset fall; ngspice names `bdrive_row1#branch`, which does not by itself establish the cause. [Results](docs/streamed-frame.md).

Next: internal gate/device capture around this transition and one justified correction, then a completed nine-pixel transient, matched references and refinement. Three preliminary static-reference probes pass the 0.5 mV screen; no full-frame pass is claimed. Updated the overview and archived the exact evidence.

## Streamed row-switching diagnostic — 2026-09-20

- Added a bounded diagnostic runner that preserves accepted waveform points after watchdog stops, with KLU selected after circuit load and unique run directories. Captures controls, pixels, supply/output, clamp timing nodes and sampling-switch currents.
- The unchanged trapezoidal candidate completes to 3.24 ms in 1,166.94 s. Its entire 14,326-point prefix matches the shorter attempt exactly. The previously reported stall is a severe but traversable numerical slowdown; rounded logs conceal accepted subnanosecond progress.
- Compared one row-slew change (10 ns to 100 ns); the slow region follows the shifted row-fall endpoint. No timing change is promoted. Preserved setup errors and watchdog runs alongside the completed diagnostic.
- Six retained samples have expected brightness ordering, switch currents match their terminal equations, and all 16 MOS-cap ranges satisfy the existing screen over the captured interval. No complete-frame, DC-reference settling, refinement, startup or fabrication pass is claimed.
- Added plots, checksummed diagnostic evidence and updated the handoff. Next: an unchanged streamed nine-pixel frame with adequate bounded runtime.

## Project handoff and complete checkpoint — 2026-09-19 22:39 PDT

- Added [PICK_UP_HERE.md](PICK_UP_HERE.md) with the latest status, precise switching-edge blockers, ordered next tasks, Docker/KiCad startup guidance and archive restoration instructions.
- Checkpointed all accumulated work since `0eec653`: routed/filled 3×3 chip, pad/interface proposals, extraction and charge-conservation investigations, simulator/model controls and patches, reports/plots, manifests and diagnostic archives. Historical entries below retain their original results and limitations.
- Included native KiCad carrier/tester projects, local libraries, mechanical/BOM information, saved checks and review exports; board electrical/mechanical qualification remains open.
- Added the wafer.space setup audit and direct Tiny Tapeout, JKU, ISHI-KAI and wafer.space references to the overview. Inspected newer PDK models match the installed models; reference projects do not establish our transient qualification.
- Added the measured-bias functional-camera candidate: stock final-chip DC passes; 1,680 MOS capacitors are frozen only for the separate normal-operation experiment, with all other records retained. Trap and Gear attempts stall at row-switching edges and were manually stopped. No full-frame, startup, PVT, distributed-R or ADC qualification is claimed.
- Preserved matched ngspice 46/47 evidence and unsent public issue drafts. Updated README navigation and the HTML overview; no issue or review packet has been posted.
- This commit is an engineering checkpoint, not a fabrication release. Large evidence archives are intentional; Docker images, caches and regenerable build directories remain excluded.

## Matched simulator comparison — 2026-09-19 11:30 PDT

Built ngspice 46 and 47 with matching options in an isolated project folder. Both capacitor controls pass the independent current/charge checks. The unextracted stock corner fails at startup in 46 and fails parsing in 47. Both extracted stock-model cases fail at startup. A PDK-free reproducer isolates a separate v47 explicit-capacitor-multiplier parser failure (`m=1/8/70`); omitting the multiplier passes. **A simple upgrade does not resolve the qualification blocker.**

[Results and plot](docs/ngspice-version-comparison.md) · [Small public issue draft](docs/reviews/ngspice47-cap-multiplier-issue.md). Nothing has been posted and the working PDK/simulator/layout remain unchanged. The bounded comparison is complete; the earlier local helper candidate has not been promoted or rerun in this batch. Next: review the small parser failure separately from the extracted transient failure, then select a justified numerical-model correction and repeat accuracy/refinement gates before full-chip qualification. No new hardware or packaging decision is needed.


## Electrical checkpoint — 2026-09-19 10:02 PDT

**Complete-chip electrical qualification remains blocked by the clamp numerical model.** Both 50 ns corner runs complete, but both 25 ns/strict-tolerance runs abort at the 151 µs load transition in `e.x354.ehelper#branch`. No candidate is promoted; no full-chip startup/frame/PVT pass is claimed.

The final filled-chip lumped-capacitance extraction preserves all 4,037 semiconductor records. Its floating-fill reduction passes charge/energy checks and leaves 2,179 capacitors on 279 retained nodes. Distributed wire resistance remains unqualified. [Current results](docs/scaled-electrical-progress.md).

Next: use the saved failing deck to resolve the clamp-helper load-edge failure, then run the gated full-chip startup, repeated frames, refinement and PVT/load checks. `scripts/simulate-filled-chip-baseline.py` is prepared but has not been run; its prerequisites intentionally reject the current failed corner screen. No additional hardware or user decision is needed for this diagnostic work.


## Electrical qualification update — 2026-09-19 09:34 PDT

[New control-resolution and extracted-clamp results](docs/scaled-electrical-progress.md): matched capacitor controls pass the unchanged current limit; the isolated extracted clamp completes and passes 25 ns/tolerance voltage refinement. Both complete-corner capacitance placements now complete at 50 ns. These are diagnostic milestones, **not complete-chip qualification**. Final-GDS extraction and the [remaining electrical gates](docs/full-chip-electrical-plan.md) are open.

## Removable KiCad sensor fixture — 2026-09-19 08:30 PDT

- Added native KiCad 7 tester and removable 40 × 40 mm die-carrier projects, embedded symbols, local footprints, BOMs and mechanical coordinates.
- Implemented underside pogo contacts, optical aperture, local carrier bias resistors, disabled-by-default timing buffers, dual analog buffer and ADS1115 with faster-ADC expansion.
- Routed both boards and corrected native DRC findings: zero final violations/unconnected pads; schematic pin/net comparison passes. Saved reports with file hashes, PDF schematics and layout previews.
- Added Windows/Docker instructions, ADC timing limitations, assembly requirements and remaining qualification steps. Updated the HTML overview and top-level README. No fabrication release or external publication.

## Clamp-model local review — 19 September 2026

Audited ngspice’s expanded MOS-capacitor model and tested one algebraically equivalent internal scaling. Both standalone traces complete, but the current comparison fails (2.71 nA versus 0.1 nA); no clamp trial or fix accepted. [Results and specific reviewer questions](docs/clamp-model-review.md). External review has not occurred; further sweeps remain stopped.

## Filled working demonstrator — 2026-09-19 03:15 PDT

Regenerated central fill with all nine optical keepouts preserved. Density/antenna and main KLayout DRC report zero violations; device LVS matches uniquely; all 4,566 connectivity checks pass. [Evidence and reproduction](docs/filled-demonstrator.md). Next: resolve the clamp-model review, qualify post-fill electrical behavior, and confirm run/bonding requirements. The local simulator stop rule remains active; this is not a fabrication release.

## Routed working demonstrator — 2026-09-19 02:57 PDT

13 functional signal paths routed through local protection; seven supply/return pads connected. Metal connectivity: 4566 checks, PASS. Main KLayout DRC: 0 markers. Magic DRC: 0. Device LVS unique match: True. Four diagnostic signal paths remain disconnected; fill and final sign-off are open. [Evidence](docs/routed-demonstrator.md). Next: close physical findings and regenerate/verify fill; retain the stop on simulator parameter experiments.

## Pad-placement proposal — 2026-09-19 02:12 PDT

Created a 24-pad custom-carrier proposal, coordinate CSV, labeled diagram and separate unrouted GDS. All 19 core ports are represented. Packaging, diagnostic loading and protection choices remain open; no routing or sign-off claimed. [Review](docs/pad-proposal.md). Next: obtain the selected run/package requirements and close the pad-map review before routing.

## Completion reset — 2026-09-19 01:59 PDT

Frozen the 3×3 first-release scope, replaced stale completion instructions with milestone exit conditions and a two-trial solver stop rule, documented all 19 core ports and board timing assumptions, and prepared manufacturing/optical questions. README now leads with the 3×3 target. Signal pads are explicitly identified as unfinished. Final solver results and an unsent expert-review package accompany this checkpoint.

## MOS-capacitor isolation — 2026-09-19 01:49 PDT

24/24 simple capacitor transients complete; 0/4 initial isolated-clamp transients complete. Integration follow-up: 1/2 complete; refinement: 0/2 pass. [Evidence](docs/moscap-branch.md). Next: investigate solver conditioning and the behavioral-capacitor equations in this reproducer; the trapezoidal candidate failed refinement and is not accepted.

## Corner-interface evaluation — 2026-09-19 01:32 PDT

DC/AC interface comparison: NOT VERIFIED. Full-corner ramp/load transients: NOT VERIFIED. [Evidence](docs/corner-interface.md). Next: resolve full-corner startup before integrated 3×3 qualification.

This log summarizes engineering checkpoints. Simulation passes apply to the stated model and test conditions; they do not establish optical performance, manufacturing yield, or fabrication readiness.

## 2026-09-19 01:11 PDT — Verified resistor reduction and placement probes

Reduced four reference networks with preserved capacitance/device records and 16 DC comparisons. Added AC/load-step comparisons, half-step refinements, and retained failed full-corner startup attempts. Supply-ramp completion: False. [Report](docs/charge-reduction.md).

## 2026-09-19 00:42 PDT — Charge-conserving reference and confirmed 3×3 scope

Built and independently audited 8 lumped-C/distributed-R reference models; all 16 ngspice charge checks pass. Preserved exact R/device records, recorded every capacitor anchor, and retained the spatial-placement limitation. User confirmed the 3×3 demonstrator as the first release. [Report](docs/charge-reference.md).

## 2026-09-19 00:28 PDT — Area-sign fix and charge-accounting regression

Added an isolated one-line Magic area correction: 4 coupons now have no negative C, with 2 LVS and 16 DC checks passing. Eight independent small-control AC checks confirm a separate exported common-mode capacitance excess. Recorded both outcomes, archived evidence, and added a completion plan. [Report](docs/capacitance-candidate.md).

## 2026-09-18 23:55 PDT — Ring-section candidate audit

Fresh baseline/combined full and metal coupons; 4 LVS and 32 DC checks pass. Negative-energy witnesses reject the corner parasitic capacitance network. Added plot, preserved diagnostics, dated next steps and checksummed evidence. [Report](docs/ring-candidate.md).

## 2026-09-18 14:06 PDT — Combined extraction candidate

Fresh buffer/readout extraction, four LVS passes, 80 corner transients and two via controls pass. Added isolated build, reusable reducer paths, plots and archived evidence. [Report](docs/combined-patch.md).

## 2026-09-18 — Triangle-reduction cause and device-aware reader regression

Recorded **2026-09-18 13:17 PDT**. [Report](docs/network-investigation.md).

- Instrumented construction-time reductions and independently solved normal, unreduced and corrected graphs for two via arrays.
- Identified six half-milliohm additions in triangle-to-star conversion; a separate candidate restores unreduced DC resistance within printed precision.
- Preserved device parameters, capacitor connectivity/values and hierarchy in reader-patch exports of the actual output buffer and a two-instance fixture.
- Matched the PDK startup grid and verified the normalized baseline against the saved original buffer netlist.
- Four nominal reduced-RC transients pass with about 0.05 µV maximum output change. Four direct fill-heavy runs timed out; no raw-network transient pass is claimed.
- Updated documentation, plots and a checksummed checkpoint. Combined-patch qualification remains pending; production tools/netlists/layouts are unchanged.

## 2026-09-18 — Export-reader cause confirmed and via-array anomaly localized

Recorded **2026-09-18 12:28 PDT**. [Results and source reference](docs/extraction-diagnostics.md).

- Traced the per-resistor export increment to the Magic 8.3.664 floating-point resistor reader at pinned commit `381714e2d5debf2ded71c5a6b6604e6b936422cf`.
- Built isolated patched and unmodified executables with matched configuration. All five unchanged raw inputs export without the offset after the one-line patch; the baseline reproduces installed exports.
- Passed independent ngspice checks for both export variants and four via-array controls.
- Demonstrated the separate two-layer raw-extraction inconsistency by adding vias to unchanged metal. The exact extraction cause remains open.
- Added plots, reproducible build/test scripts, the diagnostic patch and a checksummed checkpoint. Installed tools, production netlists and layout files were not changed.

## 2026-09-18 — Full-width rail-face measurements

Recorded **2026-09-18 11:09 PDT**. [Results](docs/rail-faces.md).

- Replaced narrow measurement leads with ideal full-width M5 electrode faces on five diagnostic metal stacks, clipping to the two-filler x extent while preserving interior shapes.
- Verified the M5 body against the analytic 0.1142857 Ω strip resistance; raw Magic agrees to printed precision.
- Found raw Magic / spatial-model agreement within 0.013% for three or more layers; identified a roughly 0.0005 Ω per-resistor export increment producing about 11.2% equivalent-resistance increase. The two-layer anomaly remains open.
- Passed DC partition checks at three mesh sizes per stack and independently verified all five Magic exports with ngspice.
- Added a comparison plot, notebook/README update, dated handoff and compact checksummed evidence checkpoint. Production layout files are unchanged.

## 2026-09-18 — Isolated real rail and probe-access investigation

Recorded **2026-09-18 08:30 PDT**. [Results](docs/rail-isolation.md).

- Isolated the VDD-connected conductor component and added M4 through M1 incrementally, preserving the real metal and via shapes.
- Completed three mesh sizes per stage and two extra M5-only refinements. The discrepancy precedes the vias and strongly implicates the abrupt probe-to-rail transition.
- Verified five Magic exports against ngspice, audited topology and reproduced the earlier full-coupon VDD resistance.
- Identified a diagnostic inconsistency: adding M4 increases Magic resistance while the spatial model decreases. Absolute DC accuracy remains unqualified.
- Corrected the earlier negative-threshold interpretation after finding Magic usage errors. New accepted-syntax runs and logs are retained.
- Updated the notebook, README, handoff and compact checksummed checkpoint; production layout files are unchanged.

## 2026-09-18 — Matched terminal, bend and via controls

Recorded **2026-09-18 07:45 PDT**. [Experiment and limitations](docs/geometry-controls.md).

- Aligned the straight-strip measurement positions; analytic, mesh and raw Magic resistance agree at 0.192 Ω.
- Added a two-turn M5 path and M4/M5 bridges with one or three vias per transition, audited against duplicate/missing resistor paths and three mesh sizes.
- Verified DC stitching for every control and the real matched-plane filler. These new runs use matrix solves, with no new ngspice claim.
- The filler discrepancy remains approximately 12–18%; terminal matching alone does not resolve absolute resistance.
- Added comparison plots, documentation and a checksummed checkpoint. Physical sensor and ring layouts are unchanged.

## 2026-09-16 — Terminal calibration and extraction controls

Recorded **2026-09-16 18:53 PDT / 2026-09-17 01:53 UTC**. [Details](docs/terminal-calibration.md).

- Corrected ideal-electrode half-cell resistance in an explicit mesh mode; preserved legacy reproduction.
- Passed four analytic strip controls at two mesh sizes, corrected filler DC stitching and the 1 µm independent ngspice check.
- Isolated missing passive nets and duplicate parallel resistors in Magic selection controls; retained canonical negative-threshold extraction as a diagnostic only.
- Completed via-edge-aligned refinement. Absolute resistance convergence and the approximately 10–15% Magic discrepancy remain unresolved.
- Added plots, notebook/README updates, reproducible scripts and a checksummed evidence checkpoint. Sensor and ring geometry were not modified.

## 2026-09-16 — Distributed two-filler DC stitching benchmark

Recorded **2026-09-16 15:38 PDT**. See [method and limits](docs/filler-stitch.md).

- Enumerated all 81 conductor intervals across the actual two-filler boundary and verified exact metal coverage and via ownership in the two partitions.
- Built independent combined and stitched conductor-only finite-volume DC models from geometry, using nominal sheet/via values from the installed PDK. The finest mesh preserves 4,593 individual seam ports.
- Passed the 1e-8 relative stitching screen on four meshes and exported hierarchical two-part resistor SPICE models. The 1 µm model passes an independent ngspice DC check.
- Retained the finer ngspice 120-second timeout separately. Fine-mesh matrix results complete; absolute resistance remains mesh-sensitive and differs from the earlier Magic control.
- This validates DC partition construction, **not stitched Magic RC/device extraction**. Capacitor, substrate and full-ring camera qualification remain open.
- Added plots, JSON summaries, exact matrices, terminal maps, netlists and a checksummed archive. Sensor and ring geometry are unchanged.

## 2026-09-16 — Small ring-section extraction experiment

Recorded **2026-09-16 14:52 PDT**. See [the experiment notes](docs/ring-sections.md).

- Extracted one filler, two abutted fillers, a corner, and a corner-plus-filler with bounded runtimes; all corrected full-device exports finish in under 29 seconds.
- Added conductor-only controls, 830 physical macro-label probes, terminal connectivity/isolation checks, and sparse resistor-network current-balance checks.
- All four device LVS checks pass after shorting extracted resistor networks. Corner LVS uses the actual ring's tied analog supply domain; filler LVS preserves four ports.
- Preserved invalid dual-export and internal-terminal diagnostics. Narrow external probe leads resolve the missing-terminal checks; reported resistance includes those leads.
- Found semiconductor ground coupling in corner extraction, up to about 27% full/control resistance differences, and negative capacitor entries in corner exports. These models are not yet qualified for full-ring stitching or camera transient simulation.
- Added actual M5 geometry views, resistance comparison plots, JSON results, reproduction scripts, and a checksummed checkpoint. The sensor and ring GDS are unchanged.

## 2026-09-16 — Extracted camera, pads, and physical supply ring

Recorded **2026-09-16 13:11 PDT (America/Los_Angeles, UTC−07:00)**. This entry consolidates the work since commit `a87383d`; individual experiments were performed across the preceding sessions.

### Pixel array and extracted readout

- Added resistance/capacitance extraction of the 20 µm photodiode 3×3 array, with schematic, capacitance-only, and RC comparisons.
- Added column bias, a column multiplexer, and a shared output buffer, including layouts, extraction scripts, and off-chip ADC load simulations.
- Investigated cold idle/startup convergence and hot sampling margin. Revised the buffer reference to 40 µA and added an all-row startup reset; retained diagnostic failures and follow-up evidence.
- Connected the array, readout, and buffer in a physical test core: **37 MOS devices and nine photodiodes**, with passing recorded Magic/KLayout DRC and unique Netgen LVS.
- Completed the connected-core **24-condition process/temperature matrix**: all RC cases pass the 0.5 mV sampling screen; worst HOLD error is approximately **0.207 mV**. Wire R/C remains nominal and bias references are ideal in this matrix.

### Bias, pads, and board interface

- Added an external-resistor bias candidate: 5.1 MΩ from VDD to BIAS and 49.9 kΩ from PREF to ground. Recorded 84 DC and 18 selected startup/imaging cases; worst sampling error is approximately **0.216 mV**.
- Researched foundry GF180 pad macros and wafer.space/Tiny Tapeout references; evaluated analog-pad leakage, loading, and local protection candidates.
- Laid out a local protection cell with a nominal **149 Ω** poly resistor and extracted its capacitance. Recorded selected imaging checks and pad-wrapper LVS.
- Distinguished the untouched pad's 87 CUP.3 findings from the wafer.space-configured coupon checks, which exclude CUP and reported zero main, density, and antenna markers. These are different verification scopes.
- Evaluated foundry supply clamps, soft-start, and reset hold. Completed nominal/hot three-frame camera-plus-clamp runs with all 27 samples per run passing and worst sampling error approximately **0.221 mV**, corroborated by independent numerical checks.
- Added assumed board supply resistance, inductance, and local decoupling, including a weaker-supply sensitivity case and a finer hot simulation. These earlier camera tests use the supply-pad pair, not the new complete physical ring.

### Physical supply ring checkpoint

- Built a **1.110 × 1.010 mm** development ring from two supply pads, four corners, and 125 foundry filler cells; included all **ten clamps** and filler decoupling in the schematic model.
- Placed the unchanged 3×3 sensor inside the ring and routed power/ground using 4 µm trunks and bridges to the existing core buses.
- Recorded **zero ring Magic DRC violations**, **zero configured KLayout DRC violations on ring and assembly**, and a **unique flat ring device LVS match**.
- Independently checked metal/via connectivity: **10,948 assembly probes pass**, with no supply-to-ground short.
- Extracted the actual connecting-wire RC. Widening routes reduced total added resistance from **27.1802 Ω to 12.34158 Ω**: VDD **5.14704 Ω**, ground **7.19454 Ω**.
- Completed nominal/hot ring load tests using foundry schematic devices plus extracted connecting wires. Maximum core-supply drop: **2.567 mV nominal**, **2.451 mV hot**; both pass the declared 1% rail screen.
- The finer hot run agrees within **0.036 µV at core VDD** on the common comparison grid, below the 10 µV numerical screen.

### Incomplete work retained explicitly

- Four full-ring distributed RC extraction variants were stopped without a complete validated model. Their logs/intermediates are preserved; none is substituted for a verified camera model.
- Strict direct and exact-interface ring-load diagnostics timed out after 900 seconds. The completed ring load tests use the documented practical tolerances.
- Ring-metal resistance, complete assembly coupling, signal-pad routing, and full camera simulation with the physical ring remain outstanding.
- Ring DRC uses `all,-antenna,-density,-cup`. No complete die precheck, ESD stress, optical response, package, or fabrication qualification is claimed.

### Documentation and reproducibility

- Expanded the living [HTML notebook](docs/overview.html) with layouts, plots, comparison tables, assumptions, and failed-run evidence.
- Added source circuits, layout generators, simulation/check/report scripts, JSON results, GDS/netlist checkpoints, and checksummed evidence archives.
- Updated the top-level README with actual assembly and performance pictures, alongside the original labeled pixel, array schematic, and camera concept.
- Added the dated [continuation plan](NEXT_STEPS.md). The pinned Docker workflow remains the supported environment; no new host virtual environment was required.

## Earlier committed checkpoints

- **`a87383d` — Architecture and resolution overview:** README camera concept, area planning, grayscale resolution comparison, and HTML slider.
- **`8d76ff3` — Labeled layout and schematic:** README views of the larger photodiodes, pixel transistors, and 3×3 Xschem hierarchy.
- **`be0a047` — Verified GF180 arrays and Docker workflow:** single-pixel/repeatability work, 3×3 array schematics/simulations, 5/10/20 µm diode-size layout comparisons, local DRC/LVS, saved evidence, and Docker/VNC reproduction.
- The original gdsfactory prototype remains in [test.py](test.py); later verified layout work is under [layout/](layout/).
