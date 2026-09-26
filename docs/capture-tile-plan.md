# Physical capture/readout tile — implementation checklist

**Superseded planning sequence — 2026-09-25:** the user now targets 64×64 first silicon on wafer.space GF180 at a modest frame rate. The [current plan](../COMPLETION_PLAN.md) and [slot-fit study](64x64-slot-fit.md) take precedence. Compact pixel/bank geometry is required; a separate 3×3 tapeout is not a prerequisite. The earlier scope and evidence below are preserved.

The [full power-grid readout qualification](grid-readout.md) is complete.
This plan describes the next physical stage; it does not select a manufacturing
option or claim a completed physical tile.

**Latest shared-bank update, 2026-09-25:** the [64-column bank](capture-bank.md)
passes both main DRC checks and both LVS paths. Shared physical routing and
references are extracted. Isolated DC controls expose millivolt-scale spatial
shifts; resolve shared power/reference routing and coupled-row initialization
before full accuracy/refinement checks. The unseeded SPARSE run initializes via
transient-assisted fallback; full readout remains unqualified. Row-to-bank
joining routes are still ideal.

**Earlier update, 2026-09-25:** the [revised isolated column](capture-column-qualification.md)
passes all 48 nominal/hot transients, the tracking/refinement/placement checks,
both main DRC checks and both LVS paths. Use
`build/capture-column-routed-v8-20260925` for the shared-bank implementation.
Real-row coupling and shared-bank supplies/clocks/references/output remain open.

**Earlier physical update, 2026-09-25:** the [first isolated column](physical-capture-column.md)
passes Magic/KLayout main DRC, both LVS paths, and capacitor-device AC/leakage
checks at 27/125 °C. Matched-column transients and numerical refinement remain
open. Docker/WSL access has been restored.

**Earlier preparation update, 2026-09-24:** the [single-column schematic and conditional
MIM banks](capture-column-preparation.md) are now generated and checked against
all 64 schematic columns. Physical verification is pending restoration of the
Docker/WSL toolchain. No physical tile or new transient pass is claimed.

## Preserve the tested circuit

The current full-readout deck has 193 peripheral NMOS and 257 peripheral PMOS,
in addition to the extracted row's 192 NMOS and 64 photodiodes. Its 64 storage
capacitors are 40 pF each. The peripheral count comes directly from
`build/grid-readout-20260924/27-100/r1c64-rc-port/transient/test.spice`:

| Block | Devices to implement |
|---|---|
| Column bias | 64 NMOS sinks and one shared NMOS reference |
| Simultaneous capture | 64 NMOS/PMOS transmission-gate pairs |
| Stored-voltage buffers | 64 PMOS followers, 64 PMOS loads and one shared PMOS reference |
| Serial output selection | 64 NMOS/PMOS transmission-gate pairs |
| Storage | 64 × 40 pF; physically implemented capacitors replace the ideal elements |

Keep the existing transistor dimensions, 500 kΩ BIAS / 12.4 kΩ PREF fixture
settings, exposure/capture timing, 20 µs column slots and 10 µs acquisition
for the first comparison. External bias connections and actual on-chip bias
generation need an explicit implementation decision; the fixture resistors
are not evidence of a placed reference circuit. The carrier is unchanged.

## Build and verify in increments

1. **Complete for the isolated column:** build the capture/buffer/mux and modular
   capacitor bank; check connectivity, DRC, capacitance versus its model and
   matched-terminal transients. See the qualification above for tested limits.
2. Repeat it across 64 columns with physical common capture clocks, complementary
   controls, bias/reference lines, output bus, supply and return routes. Extract
   resistance and coupling capacitance, then rerun the full row fixture and
   its existing 500 µV output / 10 µV numerical limits.
3. Add shared rows and repeat captures so an earlier row's stored charge,
   reset activity and idle-row loading are included. Retain full-length column
   and row interconnect tests before promoting a full 64×64 layout.
4. Integrate real control drivers and scalable row/column addressing. The
   present 100 Ω behavioral drivers and independent ideal control sources
   do not qualify clock skew, driver power or the full camera's pin interface.

## Capacitor and routing constraints

The installed-model area-only budget for the 2.56 nF bank is 2.594, 1.741 or
1.286 mm² for the conditional 1.0, 1.5 or 2.0 fF/µm² options. These are not
manufacturing choices or placed areas. The installed MIM rule limits one
plate to 10,000 µm²; use parallel legal cells and include fringe capacitance,
spacing, terminals, shielding, voltage dependence and any supported leakage
model. See `build/array-strip-storage-area-20260924/budget.json`, whose model
and rule hashes are preserved in the earlier array-recovery checkpoint.

Place opaque storage structures outside the optical junction area and
explicitly audit the added metal against the junctions. The existing M5 row
straps do not qualify the peripheral power grid: the current schematic keeps
those devices on ideal shared rails apart from the external 2 Ω source.
Route and extract both peripheral supply and return, including via arrays
and shared feed paths. Measure local headroom, common capture disturbance,
reference movement and output error rather than assuming the row's resistance
improvement transfers to the much larger peripheral load.

The present device-temperature checks retain nominal wire RC. Interconnect
corners, wire temperature coefficients, process combinations, nonlinear
startup, noise/mismatch, actual ADC timing and full-chip/package/manufacturing
checks remain separate gates. Frame rate is still undecided; the present
timing is a test fixture, not a camera specification.
