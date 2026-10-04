# Next steps — 64×64 on wafer.space GF180

**Current — completed results checkpoint, 4 October:** all 18 selected
five-device bank cases passed, with 36 transients and 3,456 reference calculations.
The sequence finished 2 October at 15:11 Pacific after 48 h 21 min; no verification
jobs remain active. Worst total/tracking errors are 456.591/215.322 µV against
500 µV; sample refinement is 0.465218 µV against 10 µV. This is selected coverage
of a one-row, 64-column bank, not full-chip qualification.
Next: define bounded supply/wiring/placement checks before real drivers and
multirow integration. [Resume here](PICK_UP_HERE.md) ·
[Completion record](simulations/stack5-completion-checkpoint-20261004.json) ·
[Overview](docs/overview.html#stack5-completion).
Earlier status entries below are historical.

**Latest review, 30 September — stopped; no active simulations:** all three
100 ns runs and 576 references completed and are independently audited. All three
50 ns runs hit the four-hour timeout, leaving 11 of 384 output samples unverified.
Coarse typical/SS totals are 391.959/445.375 µV, but FF is 602.413 µV against
500 µV. 7 available fine FF samples also exceed the limit (up to 577.376 µV).
No complete pair is qualified and the later queue did not start. Next: address
remaining fast-corner capture/storage error and use a longer watchdog for reruns.
[Reviewed evidence](docs/overview.html#stack3-interrupted-review) · [Handoff](PICK_UP_HERE.md).
Earlier running/completion statements below are historical.

**Running, 30 September — 64-column candidate sequence:** checkpoint and
changelog were pushed as `06889e5` before this work. The new physical 64-column
bank passes DRC/LVS and all capture-chain checks. Six typical/SS/FF 125 °C
simulations are running, with 576 matched references planned for this batch.
On audited passes, the controller advances through mixed corners, 27 °C cases,
and remaining typical-process illumination patterns (18 cases / 36 transients /
3,456 references in the complete queue). Failure stops subsequent stages.
[Live overview](docs/overview.html#stack3-sequence) · [Status](build/stack3-sequence-20260930-away/status.json).
Earlier status entries below are historical.

**Latest, 30 September — physical candidate verified:** the three-device capture
switch is implemented in a separate column and two-column bank. DRC/LVS and
40 µm abutment pass. With 12.5 µs acquisition, extracted typical/SS/FF worst total
errors are 152.197/181.071/258.782 µV across port/far placement (limit 500 µV).
Placement sensitivity is below 0.044 µV. This stage completed 18 transients and
108 references. Next: separate 64-column candidate build and process validation.
No simulation jobs remain active; the old 64-column checkpoint is unchanged.
[Physical candidate and rerun guide](docs/overview.html#physical-stack3) · [Handoff](PICK_UP_HERE.md).
Earlier status entries below are historical.

**Latest, 30 September — candidate cycle tests reviewed:** 20 transients and
120 references are complete. Three series NMOS capture devices pass the selected
two-column typical/SS/FF screen; FF error improves from 1240.756 to 410.653 µV
(limit 500 µV). A separate 12.5 µs acquisition test improves SS settling.
Next: check the combined changes, implement a separate physical column revision,
verify extraction/DRC/LVS and small-bank behavior, then repeat full-bank corners.
The current GDS and its known process failures remain unchanged. No jobs are active.
[Results and rerun guide](docs/overview.html#bank-capture-cycles) · [Handoff](PICK_UP_HERE.md).
Earlier status entries below are historical.

**Diagnosis completed, 30 September:** the process failures are reviewed and
short current/candidate tests are complete. FF retention is dominated by the
NMOS capture switch in the probed states; series devices reduce DC leakage but
are not yet a validated correction. Next: candidate capture/readout transients
and an SS acquisition-timing test. No new long batch is active.
[Diagnosis and plots](docs/overview.html#bank-process-diagnosis) · [Handoff](PICK_UP_HERE.md).

**Current, 30 September:** the SS/FF process batch finished. Both total-error
checks fail (512.924 / 2000.323 µV vs 500 µV); other selected checks pass. All
384 references are audited and 1,740 evidence files verify. Next is diagnosis
of SS output settling and FF storage retention, before more corner coverage.
[Review](simulations/compact-bank-process-review-20260930.json) · [Handoff](PICK_UP_HERE.md).
Earlier active-job descriptions below are historical.

**Active, 30 September:** the first SS/FF MOS-process batch is running at
125 °C inverse illumination: four 100/50 ns transients and 384 planned references,
with an independent watcher. The small FF control failed capture/storage accuracy;
that failure is retained while measuring the actual 64-column layout. Results
are pending. [Overview journal](docs/overview.html#verification-journal) ·
[Profile and scope](verification/compact-bank-process-suite.json) · [Handoff](PICK_UP_HERE.md).

**User-selected next step, 30 September:** proceed with process variation now.
Start with a bounded SS/FF MOS-only batch at 125 °C inverse, after typical-deck
regression, a retained full-bank audit control and small physical SS/FF controls.
The general pixel-rerun controller remains future work. See the
[process profile](verification/compact-bank-process-suite.json) and
[handoff](PICK_UP_HERE.md) for launch status; earlier proposed priorities below
are superseded by this instruction.

**30 September — documentation and repeatability:** the user requested a detailed test explanation and a running record before proceeding. See the [verification journal](docs/verification-journal.html). The next proposed implementation task is a versioned manifest-driven rerun controller, validated against the current baseline, followed by the remaining operating-corner profile. No new simulations were launched for this documentation task.

**Completed and reviewed, 30 September:** bright illumination and the authorized
joint parasitic-placement batch both pass. All five illumination patterns now
pass at 27/125 °C: 20 transients and 1,920 independent references, plus four
placement transients and 384 references. Those baseline jobs are complete; the process batch above is active.
Next: process/wire/supply corners and remaining placement/local-supply checks,
then real drivers and repeated rows. Full-chip qualification remains open.
[Completion review](simulations/compact-bank-overnight-review-20260930.json) · [Handoff](PICK_UP_HERE.md).

The user prioritizes working first silicon at a modest frame rate.
[The completion plan](COMPLETION_PLAN.md) is the current source of priorities.

**Overnight results:** bright total error is 359.158/402.995 µV at 27/125 °C
against 500 µV. Joint relocation of 67 conserved shunts passes at 27 °C
alternating and 125 °C inverse; the largest HOLD/STORE change is 1.527 µV
against 10 µV. Bright and placement took 3.97 and 3.87 hours respectively,
including audits. All ten simulation/audit containers exited successfully.

**Reviewed 29 September:** uniform dark passes at both temperatures, with
248.852/411.912 µV worst total error against 500 µV. Four transients and 384
references are complete; all five containers exited successfully after 4.04 hours.
Middle (80 pA) and bright (240 pA) subsequently passed at both temperatures. [Current handoff](PICK_UP_HERE.md) · [Uniform results](docs/compact-bank-64-uniform.md).

**Reviewed 29 September:** all four alternating/inverse temperature combinations
pass: eight transients and 768 references. The new 27 °C inverse / 125 °C alternating
cases reach 387.179/430.383 µV worst total error, below 500 µV; refinement stays
below 0.150 µV. Their 1,707 distinct evidence files verify, and all job/auditor
containers exited successfully. No new batch is running.
[Results](docs/compact-bank-64-cross.md) · [Handoff](PICK_UP_HERE.md).

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
this timing. The original attempts were stopped on 27 September; the resumed
nominal/hot inverse pairs now pass their complete selected audits. See
PICK_UP_HERE.md for results and the next coverage batch.

These are bounded development screens. Full 16-column corner/placement
coverage, remaining full-bank corners/individual placements, real drivers, repeated rows
and exact 64×64 manufacturing qualification remain open.

1. Define the next bounded process/wire/supply-corner matrix and a separately
   versioned runner/auditor: the current full-bank runner fixes typical process
   and nominal supply. Verify deck generation and matched references before
   launching long runs. Preserve all hash-pinned sources and use fresh outputs.
   Uniform illumination is complete; joint far-node placement passes the two
   selected cases, while individual placements and local supply/reference drops
   remain open.
2. Use `build/compact-bank-c64-ground-grid-20260927` for the revised ground
   routing and retain `build/compact-bank-c64-ground8-20260927` as its failing
   selected-read control. The original `build/compact-bank-c64-v1-20260926`
   remains the archived 2 µm-bus baseline. Use fresh output directories.
3. Keep KLU, current-form drivers, trapezoidal integration and strict tolerances.
   The completed fresh transients took 166.2–182.5 minutes with concurrent work;
   independent references add time. The four-hour transient and 30-minute
   per-reference watchdogs remain planning allowances. Preserve measured run
   timings, and do not alter the circuit/tolerances to manufacture a pass.
4. Finish 16-column placement at other pattern/temperature combinations,
   remaining schematic patterns, process/wire/supply corners and local
   supply/reference-drop checks. The hot inverse placement extension is limited
   to its stated case. Keep physical/schematic response separate from same-state
   accuracy; it has no assigned threshold.
5. Once the remaining bank coverage passes, exercise 4×64 repeated rows with real
   decoding/drivers and full-column loading. Then add 63 rows to the joined
   bank's existing row and assemble the exact 4096-pixel chip. Close final-chip
   extraction, power/pads, optical, DRC/LVS/ERC, density/antenna and provider
   precheck gates. The prior two-column full matrix remains a control.

Manufacturing and interface work can proceed now: resolve the run/slot booking,
optical packaging and pad allocation; draft 6-bit row/column addressing with
safe reset/capture/output sequencing and an external ADC. A separate 3×3 tapeout
and a 30 fps redesign are not prerequisites.

The [dated Run 3 overview](docs/overview.html#wafer-space-run3) gives advertised
full-slot pricing of $7,000 early / $8,000 standard for 1,000 dies; optional CoB
adds $1,500 and is not yet optically approved. Early bird ends 30 September;
purchase and clean GDS are due 9/16 December 2026, 23:59 AoE. Full slots were
reported limited on 19 September. Plan for the 3.048 × 4.238 mm default core;
smaller slots cannot fit the current array even inside their seal rings. Final
assembly must add 63 rows to the joined bank's existing row, not duplicate it.

Offline checks already available:

```sh
python3 scripts/test-compact-bank-schedule.py
python3 scripts/test-compact-bank-resistors.py
python3 scripts/budget-64x64-floorplan.py --out build/slot-budget-new
python3 scripts/compact-bank-resistors.py \
  --source build/compact-bank-c64-v1-20260926/rc-port.spice \
  --out build/bank-equivalent-new
```

Use fresh output directories. Preserve existing experiments. Source/reports/manifests
through the previous checkpoint were pushed; the new diagnostic work is local.
Generated checkpoint archives remain local and ignored by Git. A fresh
clone needs separate evidence copies or reproduced builds; see [storage](checkpoints/README.md).
[Earlier detailed next steps](checkpoints/planning-history-20260925/NEXT_STEPS.md)
are historical, not a second active plan.
