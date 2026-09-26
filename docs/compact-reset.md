# Compact pixel reset follow-up — 2026-09-26

**Next stage completed:** the [compact capture column](compact-capture.md)
now passes isolated checks; the physically joined tile remains next.

**All 12 nominal/hot development transients pass with the audited shunt models
and unchanged 2×2 boundary control.** Six independent extended-reference runs
also pass. The untouched isolated raw model reproduces its reset-edge abort.
This closes the small-cell electrical screen using an explicit capacitance
placement approximation; it does not qualify the raw distributed extraction.

## Controlled change

The isolated reset net contains a +6.29159 fF port shunt and a −0.51561 fF
local-gate correction. The existing strip audit conserves their **5.77598 fF**
signed total, placing it at the reset port or local reset gate in two models.
All resistors, devices, other shunts and coupling capacitors remain identical.
The resistor-collapsed capacitance matrix is conserved to the audit's 1e−25 F
tolerance. The 2×2 raw model contains no negative capacitor and is unchanged.
The physical GDS, aperture audit and previous DRC/LVS evidence are unchanged.

The repeated 125 °C, 100 ns raw control aborts at 220.01 µs. Both positive-shunt
variants complete with identical fixture statements, simulator binary and
tolerances. This isolates the reset-shunt representation as the discriminating
change for this failure; it does not validate the extractor's physical distribution.
The source netlist and failed trace are preserved.

## Electrical checks

Conditions: 27/125 °C, 200/100 ns maximum timestep, existing 50 µs read slots
and 30 µs acquisition. Tracking limit: 500 µV; timestep, placement and reference
duration comparison limits: 10 µV. The 100 ns traces are reused unchanged for
independent matched DC references with optran extended from 200 to 1000 µs.
These are six additional reference sets, not six additional transients.

| Cell | Model | °C | Worst tracking (µV) | 200→100 ns (µV) | 200→1000 µs reference (µV) |
|---|---|---:|---:|---:|---:|
| r1c1 | rc-port | 27 | 8.661 | 2.535673 | 0.000000 |
| r1c1 | rc-gate | 27 | 8.660 | 2.503433 | 0.000000 |
| r1c1 | rc-port | 125 | 24.204 | 2.573103 | 0.000000 |
| r1c1 | rc-gate | 125 | 24.204 | 2.553877 | 0.000000 |
| r2c2 | rc | 27 | 191.066 | 2.803905 | 0.000002 |
| r2c2 | rc | 125 | 234.550 | 2.709671 | 0.000000 |

Worst port-versus-gate sampled output difference: **0.034648 µV**.
All expected samples are present and paired by row, column and sample time.

## Scope and next step

The electrical screen retains schematic readout periphery and imposed controls.
It does not exercise a physical capture column, joined routing, real drivers,
full-column loading, repeated frames, startup, process corners or manufacturing
requirements. The raw isolated model remains diagnostic. Placement sensitivity
must be checked again after physical joining; these results cannot be inherited
by the future 64-column assembly without requalification.

Next: repack the 40 pF capture column to the slot-fit budget, qualify it, then
physically join a small pixel/capture tile. Milestone 1 remains open.
[Original compact layout evidence](compact-pixel.md) ·
[Current plan](../COMPLETION_PLAN.md) ·
[Machine-readable results](../simulations/compact-reset.json).

## Reproduce

Use fresh output directories in the pinned EDA container:

```sh
bash scripts/run-tools.sh python3 scripts/qualify-compact-reset.py \
  --source build/compact-pixel-v1-20260926 --out build/compact-reset-new
bash scripts/run-tools.sh python3 scripts/simulate-array-strips.py \
  --source build/compact-pixel-v1-20260926 --output build/compact-reset-raw-new \
  --cases r1c1 --modes rc --fixture imaging --temperature 125 \
  --step-ns 100 --timeout 120 --dc-timeout 120
python3 scripts/report-compact-reset.py --run build/compact-reset-new \
  --raw-control build/compact-reset-raw-new
```

The raw-control command is expected to record the reproduced abort. The report
checks that failure and compares normalized raw/approximated fixture decks.
The completed dated run is `build/compact-reset-v1-20260926`.
Archived evidence: [compact reset checkpoint](../checkpoints/compact-reset/README.md).
