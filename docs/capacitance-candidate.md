# Capacitance area correction and charge-accounting audit

Recorded **2026-09-19 00:28 PDT**.

**A one-line area-sign correction removes every negative capacitor in the four ring coupons. A separate exported-charge accounting error still blocks RC model acceptance.** The candidate remains isolated; no installed tool or production netlist is replaced.

![Area correction and remaining accounting discrepancy](assets/capacitance-candidate.png)

## Confirmed area-sign defect

In Magic 8.3.664, `resis/ResMakeRes.c`, the one-breakpoint branch of `ResCalcEastWest` adds `height * (LEFT(tile) - RIGHT(tile))` to the node's area. That is negative for a finite-width tile. The correction reverses the subtraction; the north–south counterpart already uses positive height. `ResDistributeCapacitance` in `ResSimple.c` normalizes those areas to allocate capacitance, carrying negative weights into `.res.ext` and SPICE.

Patch: `patches/magic-8.3.664-single-break-area.patch`, applied on top of the previously tested resistor-reader and triangle corrections, against source commit `381714e2d5debf2ded71c5a6b6604e6b936422cf`.

| Geometry | Previous negative entries | Corrected |
|---|---:|---:|
| Full filler | 0 | 0 |
| Metal-only filler | 4 | 0 |
| Full corner | 5 | 0 |
| Metal-only corner | 132 | 0 |

Both full-device LVS checks pass. All 16 DC rail solves pass; maximum change versus the prior candidate is 6.86527e-09 Ω. Four corrected capacitor networks contain only nonnegative elements, so the explicit parasitic capacitor networks satisfy the passive-energy sign condition. This does **not** establish accurate capacitance magnitudes, substrate behavior, or complete transistor-model qualification. Existing grid-snapping and `Missing rptr` extraction diagnostics remain recorded.

## Two different conservation checks

**Internal redistribution:** the raw rnode capacitances sum to the original node's incident coupling-capacitance total, not its `.ext` node-shunt field. Comparing the proper quantities gives a maximum relative discrepancy of 59.794 ppm across both candidates and all coupons. This reports numerical normalization accuracy; it is not full-network charge conservation. The source uses single-precision area accumulation and printed raw values.

**Exported electrical network:** the two-layer T control exposes a separate failure. Its original extraction has 6.59538 fF total shunt capacitance to substrate and 3.91030 fF between the two metal electrodes. Driving both electrodes together should put zero voltage across that coupling capacitor. The corrected RC export instead measures **10.50568 fF** to substrate—an excess of **3.91030 fF**, equal to the coupling capacitance within printed precision.

The exported netlist retains the original coupling capacitor and adds its redistributed value as substrate shunts. The nonnegative area correction does not fix this accounting. Eight ngspice AC checks (four control geometries × two candidates) independently reproduce the exported netlist's calculated common-mode capacitance. They confirm the discrepancy; they are not model-acceptance passes.

The control fixture explicitly exposes and grounds the implicit substrate, drives A/B/REF together, and measures current at 1 MHz with a 1 V AC source. Metal resistors have zero voltage in that excitation. The original expected value comes directly from `.ext` node shunts. No measured optical or semiconductor capacitance is implied.

The small T controls demonstrate the accounting error and changed area allocation, but do not reproduce negative entries themselves. The metal-only filler is the smallest tested negative-capacitance reproducer. Earlier control attempts with an outside terminal, a duplicate extraction call, and no coupling are retained as failed/non-exercising attempts, not passing regressions.

## Decision and next step

Keep the area correction as a diagnostic patch. Do not use this candidate to requalify camera settling yet. Next, correct the distinction between distributed shunt capacitance and retained mutual coupling, then require:

1. Original and R-collapsed RC capacitance matrices agree within an explicit numerical budget, including common-mode and differential excitations.
2. No negative-energy modes; preserved charge, device topology and DC resistance.
3. Repeated buffer/readout process-temperature and ADC-load tests using the accepted model.
4. Substrate-ground treatment resolved before corner stitching and full-ring simulation.

See [Completion plan](../COMPLETION_PLAN.md) for the remaining design, verification and fabrication milestones.

## Reproduce

Use the pinned tools container and matching configured Magic source from the earlier diagnostic checkpoints.

```sh
bash scripts/run-tools.sh bash scripts/build-capacitance-candidate.sh
bash scripts/run-tools.sh python3 scripts/extract-ring-candidate.py --area-fixed
bash scripts/run-tools.sh python3 scripts/audit-ring-sections.py --cases fill10 corner --work-dir build/ring-candidate/area-fixed --output build/capacitance-candidate/dc-audit.json
python3 scripts/audit-ring-capacitance.py --variants area-fixed --output build/capacitance-candidate/capacitance-audit.json
python3 scripts/audit-capacitance-conservation.py
bash scripts/run-tools.sh python3 scripts/check-capacitance-controls.py
bash scripts/run-tools.sh python3 scripts/check-capacitance-accounting.py
bash scripts/run-tools.sh python3 scripts/report-capacitance-candidate.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

`checkpoints/capacitance-candidate/evidence.tar.gz` retains fresh raw extraction, RC models, audits, small controls, ngspice measurements, source patch and scripts with SHA-256 verification. The prior combined ring models remain in the previous ring-candidate checkpoint. Production ring GDS hashes are unchanged.
