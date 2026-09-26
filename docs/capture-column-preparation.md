# Capture column preparation — 2026-09-24

The seven-transistor column and three conditional storage banks are prepared in
[`checkpoints/capture-column-preparation/`](../checkpoints/capture-column-preparation/).
This is schematic preparation and model arithmetic. Physical layout, DRC, LVS,
extraction and new transient qualification have **not** been performed.

The saved full-row deck contains 64 identical columns: three NMOS, four PMOS and
one ideal 40 pF capacitor per column. The generator checks all 512 repeated
elements, including terminal order, dimensions and junction parameters. It
exports a single column with explicit STORE and CBUF terminals, a separate ideal
storage control, and shared reference devices. The 500 kΩ / 12.4 kΩ bias resistors
and 1 pF reference capacitors remain in a separate external fixture subcircuit.
The two reference transistors are instantiated once per bank.

## Conditional capacitor candidates

Each candidate uses eight parallel PDK capacitor instances with 64 µm-wide
plates. Lengths are rounded to a 5 nm grid. The nominal 40 pF target is at the
saved model's 25 °C reference temperature, typical capacitor corner and zero
Monte Carlo offset. Calculations include area and perimeter coefficients.

| Model option | Plate dimensions (µm) | Total at 25 °C (pF) | Total at 125 °C (pF) | 64-column plate area (mm²) |
|---|---|---:|---:|---:|
| 1.0 fF/µm² | 8 × 64 × 77.675 | 40.000639 | 40.050748 | 2.5453 |
| 1.5 fF/µm² | 8 × 64 × 52.210 | 40.000032 | 40.134848 | 1.7108 |
| 2.0 fF/µm² | 8 × 64 × 38.875 | 40.001202 | 40.037403 | 1.2739 |

No manufacturing option is selected. These areas exclude plate enclosure,
spacing, terminals, routing, shielding and transistors; the 64 µm plate width
does not prove the completed cell fits the 80 µm column pitch.

The archived MIM-B rules restrict both individual plate area and total capacitor
area on a common bottom-metal island to 10,000 µm². Keep the eight bottom-metal
islands separate and connect them electrically through upper metal. The same
rules prohibit a lower via touching the bottom plate. Full geometry and
connectivity still need verification with the installed PDK tools.

The saved models activate temperature coefficients. Their voltage-dependent
capacitor expressions are commented out; including those model files therefore
does **not** qualify voltage dependence. Only the saved 2.0 fF/µm² variant has an
active explicit leakage resistor: the proposed eight-cell bank gives about
26.415 TΩ at 25 °C. Missing leakage elements in the other variants do not establish
zero physical leakage. No hold-error or output-accuracy claim follows from this
arithmetic alone.

## Reproduce and resume

The checkpoint includes the source deck, capacitor model, MIM-B rules, generated
subcircuits and SHA-256 provenance. Regenerate into a new directory using only
Python's standard library:

```sh
python3 scripts/prepare-capture-column.py \
  --source checkpoints/capture-column-preparation/source.spice \
  --model checkpoints/capture-column-preparation/model.ngspice \
  --rules checkpoints/capture-column-preparation/rules.rb \
  --out build/capture-column-reproduced
```

The archived full-row deck retains its original `/foss/designs` dependencies; it
is an audit source, not a standalone simulator deck. The generated storage
subcircuits also require the original PDK models and corner/Monte Carlo
parameters. Use the full grid-readout checkpoint to restore that fixture.

The current session cannot access the pinned tools container: Docker reports
that WSL integration is unavailable. Magic, ngspice and Netgen were not found on
the host PATH. Once Docker Desktop's integration is restored, continue step 1 of
the [physical tile plan](capture-tile-plan.md): generate capacitor and transistor
geometry, verify DRC and connectivity, extract R+C, and compare the column with
the schematic under matched terminal stimuli. Preserve the existing full-row
timing and 500 µV output / 10 µV numerical gates.
