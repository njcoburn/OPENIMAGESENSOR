# Compact 40 µm pixel — 2026-09-26

**Follow-up:** [compact reset qualification](compact-reset.md) passes the isolated
screen with conserved-total shunt models and extends both cells' references.
The raw-model failure below remains diagnostic evidence.

**The first 40 × 40 µm pixel and 2×2 boundary control pass scoped physical checks.**
Docker access is restored. The existing 20 × 20 µm diode and three W=1 µm,
L=0.5 µm transistors are imported unchanged; only placement and routing change.
Both cells pass Magic DRC, KLayout main DRC, direct-device LVS and
resistor-collapsed LVS against independently constructed circuit references.
The 2×2 control contains 12 MOSFETs and four diodes, with distinct row and column nets.

The pixel's fabricated geometry bounds are (−0.2, 2.2)–(40.2, 38.7) µm.
The 0.2 µm overhang joins horizontal buses at 40 µm pitch; this is not a
strictly contained 40 µm square. External supply trunks add 10.3 µm on the left
of the control array. The central 18 × 18 µm region is free of M1–M5 metal.
This geometric aperture audit does not establish legal passivation openings,
fill treatment or optical performance. Density, antenna and cup decks are excluded.

## Extracted electrical screen

Seven of eight imaging transients complete with matched settled output references.
The 2×2 control completes all four 27/125 °C, 200/100 ns runs and passes both
screens. The isolated pixel completes three runs; its hot 100 ns run aborts.
These retain the existing schematic mux/output/ADC fixture and ideal control
sources; there is no physical capture bank in this test. Readout slots are
50 µs, with 30 µs acquisition. Limits are 500 µV tracking and 10 µV refinement.

| Cell | Temperature (°C) | Worst tracking (µV) | 200→100 ns sample difference (µV) |
|---|---:|---:|---:|
| r1c1 | 27 | 8.661 | 2.501517 |
| r1c1 | 125 | Incomplete | 100 ns transient aborts |
| r2c2 | 27 | 191.066 | 2.803905 |
| r2c2 | 125 | 234.550 | 2.709671 |

**Isolated-cell limitation:** the r1c1 extraction contains
`C35 RST0.t0 GND -0.51561f`. It is retained unchanged in the diagnostic runs;
passivity is not qualified. Its 125 °C, 100 ns run aborts at the reset edge
(220.01 µs) with a timestep-too-small error. The coarser hot run completes with
24.204 µV tracking error, but is not refinement-qualified. The negative term
is a candidate cause, not an established diagnosis.
The 2×2 extraction has no negative capacitor records.
The output-reference fixture uses its existing 200 µs optran-assisted DC solve;
an independent longer-reference comparison remains open. These results establish
a small development screen, not completion of the compact joined-tile milestone.

## Bounded full-bank solver comparison

| Model | Analysis | Elapsed (s) | Completed | Saved points |
|---|---|---:|---|---:|
| raw | op | 180.01 | False | 0 |
| raw | reset | 180.01 | False | 0 |
| equivalent | op | 180.01 | False | 0 |
| equivalent | reset | 180.01 | False | 0 |

The raw and audited resistor-reduced banks retain identical device/capacitor
records and unchanged SPICE tolerances. Each attempt has a 180 s limit; reset
controls request 0.25 ms. The reduction does not resolve initialization in
these attempts. Some independent layout/simulation jobs overlapped, so elapsed
times are timeout evidence, not an isolated performance benchmark. No completed
terminal-voltage comparison or improved convergence is claimed. Use a small
coupled tile next; avoid another open-ended full-bank attempt.

## Reproduce

Use fresh output directories. Physical build:

```sh
bash scripts/run-tools.sh python3 scripts/build-compact-pixel.py --out build/compact-pixel-new
```

Run this for temperatures 27 and 125 and steps 200 and 100, each with a fresh output:

```sh
bash scripts/run-tools.sh python3 scripts/simulate-array-strips.py \
  --source build/compact-pixel-new --output build/compact-imaging-new \
  --cases r1c1 r2c2 --modes rc --fixture imaging --temperature 27 \
  --step-ns 200 --timeout 120 --dc-timeout 120
```

The dated evidence is under `build/compact-pixel-v1-20260926` and
`build/compact-pixel-imaging-*-20260926`. The audit/report command is
`python3 scripts/report-compact-pixel.py`; it validates the dated GDS/netlist
hashes, physical results, sample correspondence and numerical screens.
Machine-readable results: [compact-pixel.json](../simulations/compact-pixel.json).
The [checkpoint](../checkpoints/compact-pixel/README.md) retains source snapshots,
GDS, models, logs, raw traces, references and failed bank attempts.

Next: review isolated reset capacitance; repack the 40 pF capture column;
qualify a small physically joined tile before scaling to 64 columns.
Run-specific MIM and optical requirements remain open.
