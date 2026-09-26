# First physical capture column — 2026-09-25

**Follow-up:** the [revised column is electrically qualified](capture-column-qualification.md).
The incomplete transients below describe the earlier stage; they are retained as
development history.

**The isolated column passes Magic DRC, KLayout main DRC, and both direct and
resistor-collapsed LVS. Its eight extracted MIM devices pass independent
capacitance and leakage checks at 27 °C and 125 °C. Transient accuracy remains
unqualified.** Docker/WSL access is restored.

The candidate is `build/capture-column-v2-20260925/column.gds`. It contains the
same three NMOS and four PMOS as the prepared schematic, with eight parallel
MIM capacitors in place of the ideal 40 pF store. The conditional 2 fF/µm² option
matches the installed Magic generator; this is not a manufacturing selection.
Existing release layouts and the carrier are unchanged.

| Check | Result |
|---|---|
| Magic DRC | 0 errors |
| KLayout main DRC, including MIM rules | 0 violations |
| Direct-device and resistor-collapsed LVS | Both match uniquely |
| Device terminal/parameter audit | Exact match to schematic and capacitor dimensions |
| Physical extent | 66.4 × 678.24 µm |
| Storage | Eight 64 × 38.880 µm plates |
| Bottom-plate islands | Eight separate islands, each 2,488.32 µm² |
| Lower vias touching capacitor plate overlap | None |
| Extracted wire network | 79 resistors and 110 capacitance records |

The capacitor generator rounds the prepared 38.875 µm length to 38.880 µm.
The implemented reference explicitly uses that extracted dimension. The first
primitive trial's misplaced ground label and the first assembled candidate's
landing/spacing errors are retained as excluded development attempts. The final
candidate corrects these errors. Layer 0/0 contains oversized Magic bounding-box
annotations; those annotations are removed when assembling the physical cell.
Process geometry remains intact.

The cell fits within an 80 µm width, but an abutted 64-column bank, shared routing,
array placement and peripheral supply grid have not been implemented. The
isolated cell contains no optical junctions. Integration must still place the
storage outside the pixel apertures and audit added metal against those apertures.
Main DRC excludes antenna, density and CUP checks; this is unfilled development
geometry, not manufacturing signoff.

## Independent capacitor measurements

The accepted control is `build/capture-capacitance-v3-20260925`. It measures
the eight capacitor instances from the direct extraction with a 1 Hz AC source
and a 1.6 V DC bias. Routing capacitances are excluded from this device control.

| Temperature | Measured capacitance | Modeled DC leakage magnitude |
|---|---:|---:|
| 27 °C | 40.007474567 pF | 60.579643392 fA |
| 125 °C | 40.042520979 pF | 60.525305105 fA |

Both measurements match independent area/perimeter/temperature calculations.
The capacitor model explicitly uses a 25 °C nominal temperature; its leakage
resistor inherits the fixture's 27 °C nominal temperature. The `.spice` model
loaded by the simulator and the previously archived `.ngspice` model have the
same SHA-256 hash. Voltage-dependent expressions remain commented out in this
model, so this check does not qualify physical voltage dependence or retention.
Earlier capacitor-control setup/parser mistakes are excluded and retained.

## Transient qualification is still open

The new fixture compares the ideal-capacitor schematic, the physical-capacitor
schematic, and two extracted-wire models under controlled input/supply terminals.
It retains the 1.4 ms capture edge, first/last 20 µs column slots, 10 µs acquisition,
500 kΩ / 12.4 kΩ reference fixture, and 100 pF board / 20 pF sampling loads. The
column input is imposed directly; this is not the full pixel-row fixture.

Only the nominal 1.6 V input condition was attempted. No 27/125 °C transient
matrix, output-accuracy pass, refinement pass or placement-sensitivity pass is
claimed. The single-thread 100 ns trapezoidal run aborts at 1.400010 ms with a
small-timestep error naming BIAS. Other runs encounter very slow integration;
incomplete traces are excluded. Alternative solver, integration-method and
fixed-bias diagnostic attempts are preserved. Fixed-bias tests explicitly omit
reference dynamics and cannot qualify the shared reference circuit.
The fixed-bias tests also time out before capture, so reference dynamics alone
have not been established as the cause. All remaining jobs have exited; no
simulation is left running. Completed layout/device checks remain separate from
these incomplete electrical attempts.

Magic's raw RC export includes four negative corrections among the COL-to-GND
shunts. Two diagnostic models consolidate all six shunt records to their positive
30.43332 fF total, placed either at the input port or the farthest COL resistor
node. Every resistor and other coupling capacitor is retained. This conserves
total shunt capacitance but approximates its distribution; its sensitivity is
**not yet qualified**. The untouched raw export is retained. The 0.68392031 pF
sum of all parasitic records is not an effective storage capacitance and does
not replace or duplicate the explicit MIM device models.

Next: isolate the slow/failed transient using individual schematic/device/RC
controls, verify the capacitance approximation, and obtain complete matched
column transients and numerical refinement before building the 64-column bank.
The existing full-row 500 µV output and 10 µV refinement gates remain unchanged.
Real drivers, repeated/multirow operation, full process/wire corners, startup,
noise and manufacturing checks remain open.

## Reproduce

Use fresh output directories; generators preserve existing experiments.

```sh
bash scripts/run-tools.sh python3 scripts/build-capture-column.py \
  --out build/capture-column-reproduce
bash scripts/run-tools.sh bash -lc 'cd build/capture-column-reproduce && klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=column.gds -rd report=main-drc.lyrdb -rd topcell=capture_column -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup -rd threads=2 > klayout.log 2>&1'
bash scripts/run-tools.sh python3 scripts/verify-capture-column.py \
  --run build/capture-column-reproduce
bash scripts/run-tools.sh python3 scripts/check-capture-capacitance.py \
  --extraction build/capture-column-reproduce --out build/capture-capacitance-reproduce
```

The build imports four earlier verified transistor GDS primitives; those inputs
are included in the physical-column evidence checkpoint. Machine-readable
results are in `simulations/physical-capture-column.json`, with detailed
verification and capacitor reports in the checkpoint. The transient runner is
diagnostic and must not be treated as a passing qualification flow.
