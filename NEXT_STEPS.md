# Next steps — 64×64 on wafer.space GF180

The user prioritizes working first silicon at a modest frame rate.
[The completion plan](COMPLETION_PLAN.md) is the current source of priorities.

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
coverage, remaining full-bank patterns/corners, real drivers, repeated rows
and exact 64×64 manufacturing qualification remain open.

1. Extend the independent auditor for uniform dark/middle/bright patterns
   (0/80/240 pA per pixel), preserving the current hash-pinned source and verifying
   the new path before launching long jobs. Test all three at 27/125 °C with
   100/50 ns comparisons and 192 matched references per 100 ns case. Six cases
   imply 12 transients and 1,152 references; schedule bounded batches. Do not
   relabel uniform illumination as alternating/inverse to bypass assertions.
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
