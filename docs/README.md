# Sensor references

All 18 selected five-device bank cases are complete and passing. Start with [PICK_UP_HERE.md](../PICK_UP_HERE.md) and the [completion overview](overview.html#stack5-completion). No verification job is queued.

Current five-device overnight sequence and preflight are at [overview](overview.html#stack5-sequence); see [replay profile](../verification/compact-bank-stack5.json). The previous three-device batch remains historical evidence.

Latest: [interrupted candidate review](overview.html#stack3-interrupted-review). Three coarse runs and 576 references audited; refined runs timed out and FF electrical error remains. No simulator jobs or subsequent stages are running.

Running: [64-column candidate sequence](overview.html#stack3-sequence). The controller updates results and stops progression on failures. Portable physical candidate: `checkpoints/compact-bank-stack3-64`; electrical qualification remains pending.

Latest: [physical three-device capture candidate](overview.html#physical-stack3), with extracted-circuit results, DRC/LVS evidence, layout detail and a one-command electrical rerun. Full-bank candidate validation is next.

Latest: [candidate capture-cycle results](overview.html#bank-capture-cycles), including the model-only three-device switch screen, acquisition extension, and exact rerun commands. Physical implementation and full-bank validation remain pending.

[Process diagnosis and candidate comparisons](overview.html#bank-process-diagnosis):
SS/FF screens completed with total-error failures. Direct probes locate the
selected FF leakage path; length/series-stack DC candidates are screened but
not yet transient- or layout-qualified. See the current handoff for correction work.

[Verification journal and rerun guide](verification-journal.html): test explanations, all current bank results, running history and the path to a single-command rerun after pixel changes.

[Current device layout](overview.html#current-device-layout): labeled exact GDS,
pixel/readout close-up and dimensions of the 64-column bank plus one pixel row.
[Portable layout checkpoint](../checkpoints/compact-bank-64-matrix/README.md).

Current status, 30 September: all [uniform dark/middle/bright cases](compact-bank-64-uniform.md) and the [alternating/inverse matrix](compact-bank-64-cross.md) pass at 27/125 °C. The selected [joint parasitic placements](overview.html#compact-bank-64-placement) also pass. No simulations remain active. Next are operating corners and remaining placement/local-supply checks; see [the handoff](../PICK_UP_HERE.md).

The [16-column extension](overview.html#compact-bank-16-extension) passes
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
[selected readout comparison](overview.html#compact-bank-64-read-probes)
and [capture/ground diagnosis](compact-bank-64-ground8.md).

Extending acquisition from 10 to 12 µs on that same grid **passes the selected
diagnostic** at 269.281 µV total error and 62.529 µV tracking. Only the
ACQ falling edges and sample times move; selection/reset and the 20 µs slot
budget stay unchanged. Three new matched references and an unchanged-prefix
comparison are audited. The separately versioned full-bank runner now supports
this timing. The resumed nominal/hot screens and crossed temperature/pattern
cases now pass: eight transients and 768 independent references. See
[the current handoff](../PICK_UP_HERE.md) for the completed matrix and next coverage.

These are bounded development screens. Full 16-column corner/placement
coverage, remaining 64-column corners/individual placements, real drivers,
repeated rows and exact 64×64 manufacturing qualification remain open.

[Earlier: 16-column thermal and pattern screen](compact-bank-16-screen.md) —
five patterns pass at 27/125 °C, with 432.966 µV worst total error. Fourteen
transients and 576 references are audited. Alternating-pattern refinement and
joint far-placement controls pass; individual placements and broader numerical,
schematic and corner checks remain open.

[Earlier: 16-column trace and routing correction](compact-bank-16.md) — an 8 µm
physical ground bus reduces nominal total error from 540.185 to 189.413 µV.
All 48 nominal references and both main DRC/LVS paths pass; the expanded
thermal/pattern follow-up is above.

[Latest simulations, Run 3 pricing and die fit](overview.html#compact-bank-solver) —
KLU full-bank reset completion, eight-column nominal/hot accuracy and refinement,
and a dated full-slot manufacturing budget.

[Earlier initialization follow-up](compact-bank-initialization.md) — four/eight-column
physical controls, a completed four-column transient and an audited reduction
that still does not resolve the 64-column initialization timeout.

[Latest: compact 64-column physical bank](compact-bank-64.md) — fits the local
bank budget; both main DRC checks and both LVS paths pass. Full-bank electrical
qualification remains open. Includes the expanded nonoverlapping readout schedule.

[Latest: compact shared two-column bank](compact-bank.md) — physical reference
MOS and shared supply/reference/capture/output buses; main DRC/both LVS paths,
100 transients and 240 references pass. 419.033 µV worst capture/readout error;
5.821 mV separate layout–schematic difference. Compact 1×64 remains next.

[Earlier: physically joined compact tile](compact-tile.md) — actual COL/VDD/GND
connections pass main DRC/both LVS paths and 54 transients/72 references.
419.404 µV worst capture/readout error; separate layout–schematic integrated
response shift up to 3.922 mV. The two-column follow-up is above.

[Latest: compact capture column](compact-capture.md) — 40 µm pitch; scoped
DRC/LVS and abutment-spacing checks pass; 60 transients and 36 references pass.
165.716 µV tracking, 395.222 µV layout–schematic shift, 0.262 µV refinement.
The physical pixel join and two-column follow-up are above.

[Latest: compact reset follow-up](compact-reset.md) — 12 nominal/hot transients
and six extended-reference sets pass. Conserved-total shunt placement resolves
the isolated development-screen abort; raw distributed extraction remains diagnostic.

[Earlier: compact 40 µm pixel](compact-pixel.md) — Docker restored; single-pixel
and 2×2 main DRC/LVS pass, 2×2 nominal/hot electrical and refinement screens pass.
The reset follow-up is above; full-bank initialization remains unresolved.

[Current: 64×64 first-silicon plan](../COMPLETION_PLAN.md) · [wafer.space slot-fit study](64x64-slot-fit.md) · [Bank solver preparation](bank-solver-preparation.md). The existing layout does not fit the full slot; compact tiles are the next implementation priority. Older checkpoints below retain their original scope.

[Latest: physical bank routing reinforcement](bank-reinforcement.md) — both DRC/LVS paths pass; worst static shift improves to 1.320 mV; coupled initialization and full readout remain open.

[Latest: shared-bank routing diagnosis](bank-routing.md) — eight audited static controls and bounded coupled reset tests; full readout remains unqualified.

[Current: shared 64-column physical bank](capture-bank.md) — passing main DRC and both LVS paths; static spatial shifts and coupled-row electrical qualification remain open.

[Earlier: physical capture column qualified](capture-column-qualification.md) — 48 completed nominal/hot runs; 176.560 µV tracking, 0.318 µV refinement; passing DRC/LVS. Shared-bank follow-up is above.

[Earlier: first capture/readout column](physical-capture-column.md) — original layout and capacitor-device controls; the later qualification resolves its transient blocker.

[Current: full readout on the physical grid](grid-readout.md) — complete nominal/hot accuracy, refinement and reference-settling checks. [Next: physical capture/readout tile](capture-tile-plan.md).

[Earlier: row power-feed investigation](row-power.md) — verified turn-on dip, resistance-only diagnosis, physical upper-metal grid and its qualification status.

[Earlier: power-routing and column-capture recovery](array-recovery.md) — measured rail improvements, numerical checks, capture and hot-retention experiments.

[Latest: extracted 64-pixel row and column tests](array-strips.md) — wire resistance, settling, supply drop, exposure skew and refinement.

[Earlier: readout/cold-pad proposals](readout-followup.md) · [Tapeout readiness and larger-array planning](tapeout-readiness.md).

- [Load and operating-corner results](camera-operating-corners.md): passing conditions, capacitive-load settling limits, cold DC gaps and selected repeatability/refinement checks.

[Earlier: three-frame and nominal readout checks](three-frames.md) — 27 samples, repeatability, reset behavior and matching DC references.

[Earlier: staged integration and first full-camera frame](staged-integration.md) — nine completed samples with the unchanged extracted chip model and an equivalent reset source; qualification remains open.

[Physical array extension tests](array-extension.md) — 3×3, 4×3, 3×4 and 4×4 complete three frames with extracted capacitance; core-only scope.

[Earlier: shared-circuit numerical investigation](shared-circuit.md) — restored readout controls and a fast failed/completed source-equation pair; original full-chip failure unresolved.

[Standalone row investigation](standalone-row.md) — identical local device topology, twelve completed isolated tests; full-chip failure remains unresolved.

## Filled-layout checkpoint — 2026-09-19 03:15 PDT

[Filled-layout verification](filled-demonstrator.md) and [HTML overview](overview.html#filled-demonstrator): density/antenna, main DRC and device LVS results for the latest working revision.

## Current working layout

[Routed demonstrator report](routed-demonstrator.md) · [Working external pad names](routed-pad-map.csv) · [Current completion plan](../COMPLETION_PLAN.md). The standalone [HTML overview](overview.html) includes the routed-layout images and verification summary.

## Image Sensor Basics

- Author: Yuhao Zhu, University of Rochester.
- Course: CSC 292/572, Mobile Visual Computing, Fall 2022, Lecture 10.
- [Local PDF](lect10-sensor-basics.pdf)
- [Original source](https://www.cs.rochester.edu/courses/572/fall2022/decks/lect10-sensor-basics.pdf)
- Downloaded September 14, 2026; 101 PDF pages, 51,700,937 bytes.
- External reference material; attribution and rights remain with the original owners.

### Reading guide

Page numbers below are PDF page numbers, since slide builds repeat printed numbers.

| PDF pages | Topic |
| --- | --- |
| 10–23 | Quantum efficiency, integration, full well, dynamic range |
| 33–36 | Fill factor and pixel structure |
| 44–49 | Charge-to-voltage conversion, source follower, reset and sampling |
| 54 | Ideal monochromatic sensor model |
| 58–73 | CMOS readout and rolling/global shutter |

### Application to our GF180 design

The following are project recommendations, not GF180 specifications from the lecture.

Start with the three-transistor active pixel: photodiode, reset transistor,
source follower, and row-select transistor. Add a column current sink and load
capacitance in the testbench. Use GF180 transistor models and an explicitly
parameterized light-current model. Verify the installed PDK variant and device
voltage ratings before choosing supplies.

The transfer-gate example on PDF pages 45–49 uses a separate floating diffusion
and pinned-photodiode architecture. Our initial 3T pixel senses the photodiode
node directly. Its reset also erases the exposure signal, so do not copy that
example's post-exposure floating-diffusion reset sequence into our circuit.
Likewise, do not assume its correlated sampling noise benefits automatically
apply to the 3T readout.

First milestone: reset, integrate, and read one pixel at dark, dim, and bright
photocurrents. Plot sensing-node and column voltages; measure integration slope,
reset level, usable swing, and column settling. Sweep exposure and capacitance.
For approximately constant capacitance, the voltage drop magnitude is I*t/C.
Separate assumed optical response from PDK electrical behavior; this lecture
does not provide GF180 quantum efficiency, dark current, or diode capacitance.

Then build a small array with row timing, followed by gdsfactory layout,
design-rule and connectivity checks, and simulation with extracted parasitics.
Reserve optical access above the diode when planning metal routing. Treat noise
and mismatch as subsequent analyses: an ordinary deterministic transient run
does not establish sensor noise or dynamic range.

## Living project overview

[Open the HTML notebook](overview.html) for the circuit, timing, simulation
history, four-cycle waveforms, sampled results, limitations, and next steps.
The HTML embeds its images and works as a single offline file for sharing.

Regenerate after simulation changes:

```sh
bash scripts/simulate-cycles.sh
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Refresh `docs/assets/xschem-cycles.png` separately from the VNC desktop after
schematic changes. The builder embeds that capture, creates the waveform
plots, checks the readout data, and refreshes `overview.html`.

### Repeatability and the 3×3 target

The newest notebook sections compare 20-cycle reset conditions and define
pixel/array verification gates. Data: `simulations/repeatability.json`;
original failed numerical comparison: `simulations/repeatability-initial.json`.

```sh
bash scripts/simulate-cycles.sh
bash scripts/run-tools.sh python3 scripts/check-repeatability.py
bash scripts/simulate-reset-candidate.sh
bash scripts/run-tools.sh python3 scripts/check-reset-candidate.py
bash scripts/check-layout-probe.sh
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The report preserves earlier experiments and prepends new findings through
`scripts/overview-progress.py`. See `layout/README.md` for the 3×3 interface,
physical diode extraction issue and DRC/LVS acceptance criteria. The first
verified physical cell is one transistor, not the sensor pixel or array.

### Completed physical array

The notebook now starts with the verified 3×3 layout and scan results.
Reproduce with `bash scripts/verify-array.sh`, then rebuild the notebook.
The filled GDS and all reports are generated under `build/`; the checked
GDS fingerprint is saved in `simulations/array-verification.json`.

## Latest handoff

[Pick up here](../PICK_UP_HERE.md) — current results, numerical blockers, evidence locations and ordered next tasks.
