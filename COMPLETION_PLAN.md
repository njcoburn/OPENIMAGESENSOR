# 64×64 first-silicon completion plan

**Current — five-device candidate overnight queue started (30 September):**
The corrected physical column and both banks pass DRC/LVS. Twelve extracted
small-bank controls and 72 references pass; worst total error is 192.269 µV.
The separate 64-column candidate has 898 MOS devices and uses 13 µs acquisition.
The new detached queue tests typical/SS/FF at 125 °C first, then advances only
on audited passes through mixed corners, 27 °C and typical illumination cases.
Three jobs run concurrently, with an eight-hour transient watchdog; the first
batch is estimated at 6–10 hours. No full-bank electrical pass is claimed yet.
[Current overview](docs/overview.html#stack5-sequence) · [Live status](build/stack5-sequence-20260930-overnight/status.json) · [Reproduction profile](verification/compact-bank-stack5.json).
The previous three-device timeout and FF failure remain historical evidence.

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

**Repeatability prerequisite, 30 September:** before the next coverage batch, prepare a manifest-driven rerun controller that can preserve and compare pixel revisions. The [verification journal](docs/verification-journal.html) records the current matrix, test meaning, known fixed-layout assumptions and required build/audit stages. This does not replace the remaining electrical or manufacturing gates.

**Completed and reviewed, 30 September:** bright illumination and the authorized
joint parasitic-placement batch both pass. All five illumination patterns now
pass at 27/125 °C: 20 transients and 1,920 independent references, plus four
placement transients and 384 references. Those baseline jobs are complete; the process batch above is active.
Next: process/wire/supply corners and remaining placement/local-supply checks,
then real drivers and repeated rows. Full-chip qualification remains open.
[Completion review](simulations/compact-bank-overnight-review-20260930.json) · [Handoff](PICK_UP_HERE.md).

Updated 2026-09-30. **User-confirmed target: 64×64, GF180 through wafer.space;
prioritize working first silicon at a modest frame rate.** A separate 3×3 tapeout
is no longer a prerequisite. The earlier demonstrator remains reference evidence.

## Assessment

**Overnight results:** bright total error is 359.158/402.995 µV at 27/125 °C
against 500 µV. Joint relocation of 67 conserved shunts passes at 27 °C
alternating and 125 °C inverse; the largest HOLD/STORE change is 1.527 µV
against 10 µV. Bright and placement took 3.97 and 3.87 hours respectively,
including audits. All ten simulation/audit containers exited successfully.

**Reviewed 29 September:** uniform dark passes at 27/125 °C: four completed
transients and 384 audited references, with 248.852/411.912 µV worst total error
against 500 µV. All simulation/audit jobs finished successfully in 4.04 hours.
Middle (80 pA) and bright (240 pA) subsequently passed the same independent checks. [Current handoff](PICK_UP_HERE.md).

**Reviewed 29 September:** the alternating/inverse matrix passes at both 27 °C
and 125 °C: eight complete 100/50 ns transients and 768 matched references. The
new crossed cases have 387.179/430.383 µV worst total error; the matrix maximum
remains 438.213 µV, below 500 µV. Maximum saved-sample refinement is 0.150 µV.
All 1,707 new distinct evidence files verify, and all jobs/auditors exited
successfully. Remaining corners/placements and full-chip
qualification remain open. [Current handoff](PICK_UP_HERE.md).

We have verified building blocks, but no assembled, qualified 64×64 chip.
Compact pixel, isolated column, joined-tile and two-column shared-bank feasibility
are demonstrated. The compact 64-column bank now passes scoped physical checks
and fits its local floorplan budget; complete-chip slot fit remains open,
along with broader bank electrical coverage, multirow loading, real
addressing/drivers and final-chip qualification.

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

**Immediate next step:** define a bounded process/wire/supply-corner matrix
and separately version the runner/auditor to support it. Verify generated decks
and matched references before long runs; preserve all frozen evidence. Individual
placements and local supply/reference-drop checks also remain open. No new
simulations were launched during the completion review.

**2026-09-27 continuation:** KLU completes 64-column initialization and reset
without changing the circuit or tolerances. Eight-column alternating nominal/hot
cases pass 24 independent references each (195.412/430.243 µV worst error), with
0.170/0.401 µV saved-terminal 200→100 ns differences. The 16-column physical
control passes main DRC and both LVS paths. Complete full-bank readout/accuracy
and other patterns/placements remain open. [Latest simulations and run budget](docs/overview.html#compact-bank-solver).

**Earlier 2026-09-27 diagnosis:** Docker/VNC is restored. New four/eight-column controls
pass both main DRC and LVS paths. Four columns complete capture and two scans;
eight columns recover through transient operating-point fallback and reach
readout. Audited reduction of the compact 64-column model removes 1824 internal
nodes but still times out at 180 s with zero samples. A hot two-column reduction
control differs by at most 0.058281 µV at saved sample points. These are bounded
diagnostics, not new electrical accuracy qualifications. Continue localization
on the smaller models. [Evidence](docs/compact-bank-initialization.md).

**Latest physical follow-up:** [compact 1×64 bank](docs/compact-bank-64.md),
2627.76 × 978.28 µm including its pixel row/references, passes both main DRC
checks and both LVS paths. Its 642 MOS, 512 MIM and 64 diodes match the independent
reference. Full-bank electrical accuracy is not yet qualified. The expanded
runner avoids overlapping its two output scans at 64 columns.

**2026-09-26 progress:** Docker works. The first 40 µm-pitch pixel and 2×2
control pass main DRC and both LVS paths. The 2×2 nominal/hot electrical and
refinement screens pass. The isolated pixel now passes the
[reset follow-up](docs/compact-reset.md) with audited port/gate shunt models
(24.204 µV tracking, 2.573 µV refinement, 0.035 µV placement sensitivity).
The raw negative-shunt extraction remains diagnostic. Extended references pass
for both cells. The [compact capture column](docs/compact-capture.md) now fits
40 µm pitch and passes main DRC/both LVS paths, abutment spacing, 60 nominal/hot
transients and 36 references. Worst tracking is 165.716 µV; layout–schematic
shift is 395.222 µV and refinement 0.262 µV. All four raw/reduced full-bank
OP/reset controls time out at 180 s. The [physical joined tile](docs/compact-tile.md)
now passes both main DRC/LVS paths, 54 transients and 72 references; worst total
capture/readout error is 419.404 µV. The small-tile development screen passes.
The [shared two-column bank](docs/compact-bank.md) now passes both main DRC/LVS
paths, 100 transients and 240 references: 419.033 µV worst capture/readout error,
0.431 µV refinement, 0.038 µV placement sensitivity. It includes physical
reference MOS and shared buses. Its 5.821 mV layout–schematic response
and 26.670 µV neighbor-pattern response remain separate model/scaling
measurements. Run-specific MIM/aperture requirements, full-bank and repeated-frame
operation remain open.
[Results and limits](docs/compact-pixel.md).

| Block | Evidence | Remaining limit |
|---|---|---|
| 64-pixel row and column | Extracted strips pass scoped physical checks | Not a 4096-pixel assembly |
| Full 64-output row | Nominal/hot output error 173.457/289.658 µV; refinement below 10 µV | Readout periphery is schematic in this test |
| Compact physical capture column | 40 µm pitch; 60 nominal/hot transients; main DRC, both LVS paths and abutment spacing pass | Isolated imposed-input test; conditional MIM option |
| Physical compact pixel/column tile | Extracted COL/VDD/GND joins; 54 transients/72 references pass; worst total error 419.404 µV | One capture, two reads; schematic references/drivers, selected shunt approximations |
| Compact shared two-column bank | Main DRC/both LVS paths, 100 transients/240 references; 419.033 µV worst total error | One capture, two reads per column; external bias resistors/drivers; no 64-column loading |
| Compact physical 64-column bank | 2627.76 × 978.28 µm; main DRC and both LVS paths pass | Coupled electrical accuracy, supply sizing and placement/refinement checks remain open |
| Earlier physical 64-column bank | Main DRC and both LVS paths pass; reinforced routing improves DC behavior | Up to 1.320 mV static schematic shift; coupled transient stalls before capture |
| Full 64×64 | Not implemented | Floorplan, joining wires, multirow operation, drivers, pads and signoff |

Sources: [row](docs/grid-readout.md), [column](docs/capture-column-qualification.md),
[bank](docs/bank-reinforcement.md). Static bank shifts and matched dynamic output
errors are different measurements; do not apply the 500 µV output criterion to
the static shift as if it were a completed camera measurement.

## Manufacturing constraint changes the critical path

The provider-linked [slot data](https://mith.ro/gf180mcu-project-template/slots.json)
gives a full-slot die of 3932 × 5122 µm, inside-seal area of 3880 × 5070 µm and
default core of **3048 × 4238 µm**. Checked 2026-09-25; generated 2026-06-04.
Use a full slot as the planning envelope; no slot purchase or reservation is assumed.

The existing 80 × 50 µm pitch makes a **5120 × 3200 µm array**. The selected
bank's saved geometry is **5198 × 945.04 µm**. Neither fits inside the seal ring,
even rotated. Their combined 21.296 mm² exceeds even the 19.672 mm² inside-seal
area, before controls, pads or spacing. A custom pad ring alone cannot fix this.

[Reproducible floorplan budget](docs/64x64-slot-fit.md) proposes a **40 × 40 µm
pixel pitch** and a **2700 × 1100 µm bank budget** inside the default core.
The compact pixel and isolated capture column now have scoped physical and
electrical evidence; the new compact 64-column geometry now fits the bank
rectangle and passes scoped physical checks, with electrical work still open.
The tested 20 × 20 µm junction and transistor circuits are preserved. Continue
repacking and requalifying actual routing rather than scaling GDS polygons or
shrinking transistor dimensions blindly.

## Scope for the first chip

- 4096 monochrome pixels; row-wise exposure with simultaneous column capture.
- Retain 40 pF per-column storage and the tested circuit as the initial target.
- One analog output and an external ADC/controller; programmable slow timing.
- Use the tested 20 µs output slots initially. Readout alone costs 81.92 ms/frame;
  the earlier simple non-overlapped schedule budgets about 10.5 frames/s. Actual
  achievable rate depends on exposure, compact routing, drivers and the ADC.
- Implement scalable addressing on chip. A candidate is externally supplied
  6-bit row and 6-bit column addresses, row reset/enable, capture and output enable,
  with on-chip decoding, complementary controls and break-before-make timing.
  Freeze the pin/protocol contract before layout; independent ideal controls
  are not the final interface.
- Measure optical sensitivity, dark current, noise and variation on first silicon.
  No measured optical performance is assumed. Keep electrical startup and
  reliability checks as release gates.

## Milestones and exit criteria

| Order | Work | Exit evidence |
|---|---|---|
| 0 — now | Docker restored; freeze full-slot envelope, selected run's PDK/metal/MIM options, pad map and optical packaging requirements | Reproducible tools; dimensioned floorplan; traceable run requirements; viable optical/bond plan |
| 1 — development screen passed | Compact pixel, capture column and physically joined single tile | Scoped DRC/both LVS paths, geometric aperture audit and nominal/hot electrical screens pass; run-specific MIM/aperture requirements remain |
| 2 — selected full-bank cases passed; coverage open | Extend the shared control to compact 1×64 row/bank and joins | All 128 first/late output samples and 64 capture references at 27/125 °C within 500 µV; 200→100 ns differences within 10 µV; shunt placement check; independent settled references |
| 3 | Implement real decoders/drivers; exercise 4×64 with repeated bright/dark row transitions and a target-length loaded column | No double selection, reset/capture interference or stale stored charge; complete repeated output checks; idle-row leakage and full-column loading measured |
| 4 | Assemble 64×64 with power grid, pad ring, real clocks/references and output interface | Exact connectivity/device census; routed joins; full-chip extraction; boundary/interior/worst-load and repeated-frame checks; actual ADC/load validated |
| 5 | Final release review and wafer.space precheck on exact submission geometry | Required process/supply/temperature and wire corners, nonlinear startup/protection, numerical refinement, DRC/LVS/ERC, density/antenna, optical keepouts, seal/pads/bond map and reproducible release package |

Manufacturing/pad planning and addressing design can proceed alongside analog
qualification. Expand only after each small physical tile passes. Keep the
large existing bank as a diagnostic reference; avoid repeated routing changes
to geometry that cannot fit the selected slot.

## Bound the simulation work

**Latest:** use KLU/current-form drivers/trapezoidal integration. Full-bank
initialization/reset now completes; readout runtime is the next bottleneck.
Phase observations distinguish first saved samples, reset release, capture and
readout. Gear did not improve runtime in the small control; voltage-form drivers
abort startup and must not replace the tested formulation. Preserve all failed
controls. The overview records both complete and timed-out runs with hashes.

The earlier compact-bank diagnosis is in
[the 2026-09-27 report](docs/compact-bank-initialization.md). The compact
64-column reduction also fails to initialize within 180 s. Use the new
four/eight-column controls to separate initialization cost from transient
event cost before another full-bank attempt. The older-bank record follows.

The raw and algebraically reduced bank operating-point and short reset controls
all timed out during initialization at 180 s on 2026-09-26, with unchanged
tolerances and all transistor/capacitor records preserved. The reduction removes
4239 internal nodes but has not resolved initialization. Its algebraic/readback
audit is not a SPICE pass. See [results](docs/compact-pixel.md) and
[commands and scope](docs/bank-solver-preparation.md).

If initialization still fails, localize the problem with small joined tiles and
controlled bank loads. Do not spend another open-ended iteration on a full bank
without a discriminating experiment. Do not remove real parasitics or use UIC
as evidence that startup is qualified.

## Schedule and decisions still needed

**Rechecked 2026-09-27:** [Run 3 dates, costs and exact slot dimensions](docs/overview.html#wafer-space-run3).
Full slot: $7,000 early / $8,000 standard per 1,000 dies; optional CoB adds
$1,500, subject to unresolved optical compatibility. Early bird ends 30 September
23:59 AoE. The provider reported few full slots remaining on 19 September; no
reservation is assumed. The actual compact-bank bounds leave 3.409 mm² unreserved
in the conservative array/bank/row-driver budget. This is not a full-chip fit.

The [wafer.space Run 3 table](https://wafer.space/) currently lists purchase by
**9 December 2026**, clean GDS by **16 December 2026**, both 23:59 AoE, and parts
in Q2 2027. These are provider dates, not a project commitment or a booked slot.
Use the dated table; the page also contains inconsistent expired-countdown text.

There is no defensible “days from tapeout” estimate: complete-chip layout fit
and full 64-column accuracy remain unresolved. The compact bank now fits
its local budget; KLU resolves initialization/reset, while full readout remains
expensive. Re-estimate after milestones 1–2 using measured run times and the
completed tile. The extracted single tile
and shared two-column control now pass their scoped development screens; the next
deliverable is an electrically qualified compact 1×64 row and bank.

Still confirm: full-slot budget/booking, intended run, optical bonding/encapsulation,
permitted aperture/fill treatment, actual ADC and operating range. The
[manufacturing review](docs/manufacturing-review.md) tracks those open items.
The template supports changing signal pad types while preserving default bond
positions; generate and check the actual analog pad allocation rather than
assuming its two default analog pads satisfy all references/output connections.

[Immediate commands](NEXT_STEPS.md) · [Handoff](PICK_UP_HERE.md) ·
[Prior planning snapshots](checkpoints/planning-history-20260925/README.md)
