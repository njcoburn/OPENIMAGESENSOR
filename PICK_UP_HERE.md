# Pick up here — 64×64 wafer.space first silicon

Updated 2026-09-26. **User confirmed GF180 with wafer.space and first silicon
over frame rate.** Read [COMPLETION_PLAN.md](COMPLETION_PLAN.md), then
[NEXT_STEPS.md](NEXT_STEPS.md). Do not resume the old 3×3-first release sequence.

## New finding: existing geometry cannot fit

Full-slot default core: 3048 × 4238 µm. Existing array: 5120 × 3200 µm;
selected bank: 5198 × 945.04 µm. Both exceed even the inside-seal dimensions
in either orientation. The new [floorplan budget](docs/64x64-slot-fit.md)
uses a candidate 40 µm pixel pitch and repacked bank. It is not qualified GDS.
The compact pixel, isolated capture column, physically joined single tile
and compact shared two-column bank are implemented and screened.
A compact 1×64 bank is next.

## Resumed work — 2026-09-26

**Latest: [compact shared two-column bank](docs/compact-bank.md).**
`build/compact-bank-c2-v1-20260926` has two physically joined pixels/columns,
one physical reference pair and shared supply/reference/capture/output wiring.
Both main DRC and LVS paths pass (22 MOS, 16 MIM, two diodes, 293 resistors).
The matrix in `build/compact-bank-c2-matrix-v1-20260926` passes 100 transients
and 240 independent references across nominal/hot, five illumination patterns,
two timesteps and seven selected shunt placements. Worst total capture/readout
error is 419.033 µV, physical refinement 0.431 µV, and sampled placement
sensitivity 0.038 µV. Layout–schematic integrated response differs by up to
5.821 mV; changing one pixel changes its neighbor's output by up to 26.670 µV.
These are separate model/shared-response measurements, not capture-error passes.
One simultaneous capture and two reads per column are tested; repeated frames
and full-bank loading remain open. Evidence: `checkpoints/compact-bank`.

Next: compact 1×64 with actual shared wiring, supply/reference sizing and all
64 matched output/refinement/placement checks. The two-column control does not
validate 64-column supply drops. Keep the old stalled full bank diagnostic.

Docker Desktop/WSL is restored. If the CLI reports running with no engine,
launch `C:\Program Files\Docker\Docker\Docker Desktop.exe` directly. The CLI
restart waited for active Ubuntu processes and was cancelled; do not terminate
the working Ubuntu distro to satisfy that wait. No Docker settings were changed.

**Earlier: [physically joined tile](docs/compact-tile.md).**
`build/compact-tile-v1-20260926` joins the pixel/column through extracted COL,
VDD and GND routes. Both main DRC and LVS paths pass (10 MOS, eight MIM, one
diode, 133 resistors); the geometric aperture remains clear. The matrix in
`build/compact-tile-matrix-v1-20260926` passes 54 transients and 72 references:
419.404 µV worst total capture/readout error, 0.325 µV physical timestep
difference, 0.018 µV maximum sampled shunt-placement difference. Both nominal
and hot conditions read a captured value after pixel deselection/reset.
The layout–schematic integrated response differs by up to 3.922 mV; this is
separate from the same-physical-circuit 500 µV accuracy screen. Six selected
placements of BIAS/COL0/RST0/VRESET shunts are tested; raw negative corrections
remain diagnostic. One capture/two reads does not establish repeated frames.

The shared two-column follow-up above now passes; compact 1×64 routing, loading
and numerical screens remain next. Do not restart the old stalled full bank.

**Latest: [compact capture column](docs/compact-capture.md).**
`build/compact-capture-v4-20260926` fits 40 µm pitch (36.6 × 861.48 µm),
passes Magic/KLayout main DRC, both LVS paths and a two-column spacing control.
The selected seven-transistor/eight-MIM column passes 60 nominal/hot transients
and 36 DC references: 165.716 µV tracking, 395.222 µV layout–schematic shift,
0.262 µV refinement and 0.024 µV independent shunt-placement sensitivity.
Storage is 40.034/40.069 pF nominal/hot. VDD/ground/output trunks are
0.8/2/0.6 µm; all transistor primitives are unchanged. COL and BIAS shunts
use audited signed-total approximations; raw negative corrections remain
diagnostic. The 2 fF MIM option is still conditional. No shared bank is implied.

The joined follow-up above qualifies the next small development step. Reassess
the routing balance and shunt placements again when building a shared bank.

Docker and pinned ngspice 46 work. `build/compact-pixel-v1-20260926` contains
a 40 µm-pitch pixel and 2×2 control using the unchanged 20 µm junction and
transistor primitives. Both main DRC and direct/RC-collapsed LVS paths pass.
The [reset follow-up](docs/compact-reset.md) now passes 12 nominal/hot transients
and six extended-reference sets. Isolated port/gate shunt models conserve
5.77598 fF total reset capacitance; worst tracking is 24.204 µV, refinement
2.573 µV and placement sensitivity 0.035 µV. The unchanged 2×2 control still
passes (191.066/234.550 µV tracking). The raw isolated model reproduces its
220.01 µs reset abort and remains diagnostic; distributed capacitance is
approximated, not qualified. Evidence: `build/compact-reset-v1-20260926` and
`checkpoints/compact-reset`. Six 100 ns traces were reused for independent
200→1000 µs reference checks; worst reference shift is below 0.000002 µV.

Raw/reduced bank `.op` and 0.25 ms reset attempts all time out at 180 s without
samples. The reduction has not resolved initialization. The small coupled
shared two-column control now initializes and passes its development screen. Scale from that geometry; run-specific MIM/aperture gates remain.
[Report/reproduction](docs/compact-pixel.md) · [Evidence](checkpoints/compact-pixel/README.md).

## Verified evidence retained

- Extracted power-grid row plus schematic periphery: all 64 outputs at 27/125 °C
  pass 500 µV tracking and 10 µV timestep limits. `docs/grid-readout.md`.
- Isolated physical column: all 48 transients and both main DRC/LVS paths pass.
  `build/capture-column-routed-v8-20260925`; `docs/capture-column-qualification.md`.
- Reinforced physical bank: main DRC/both LVS pass; 16 DC controls complete;
  worst static physical–ideal buffer shift is 1.320 mV over 1.2–2.0 V.
  `build/capture-bank-c64-v5-20260925`; `docs/bank-reinforcement.md`.
- Coupled bank still unqualified: last 180 s attempt never completed initialization.
  Row-bank joins remain ideal; no full 64×64, startup or manufacturing pass.

## Work done during the 2026-09-25 replan

Archived the previous planning files without dropping evidence. Checked current
provider dimensions and schedule. Added reproducible slot-fit arithmetic and SVG.
Added standard-library resistor-only star-mesh reduction and five analytical/
corruption tests, plus an audited optional model input to the coupled runner.
The port model loses 4239 resistor-only nodes; device/capacitor/port records are
unchanged. Algebraic audits pass; the subsequent bounded runtime attempts above
all fail to initialize, so transient equivalence remains untested.
See [solver preparation](docs/bank-solver-preparation.md).

**Environment:** Docker access restored and EDA tools exercised on 2026-09-26.
No simulation remains running. No release GDS, carrier, commit, push, purchase
or external message changed. Existing uncommitted work is preserved.

Provider Run 3 dates are recorded in the plan; no run/slot reservation is assumed.
Optical access, analog pad allocation, MIM option and exact run requirements
remain open. Preserve all existing uncommitted work.

[Prior full handoff](checkpoints/planning-history-20260925/PICK_UP_HERE.md)
