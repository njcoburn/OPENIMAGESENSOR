# 64×64 first-silicon completion plan

Updated 2026-09-26. **User-confirmed target: 64×64, GF180 through wafer.space;
prioritize working first silicon at a modest frame rate.** A separate 3×3 tapeout
is no longer a prerequisite. The earlier demonstrator remains reference evidence.

## Assessment

We have verified building blocks, but no assembled, qualified 64×64 chip.
Compact pixel, isolated column, joined-tile and two-column shared-bank feasibility
are demonstrated; complete bank
**slot fit** remains open, followed by coupled readout,
multirow loading, real addressing/drivers and final-chip qualification.

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
electrical evidence; the bank rectangle remains an implementation target.
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
| 2 — two-column control passed | Extend the shared control to compact 1×64 row/bank and joins | All 64 matched output samples at 27/125 °C within 500 µV; 200→100 ns differences within 10 µV; shunt placement check; independent settled references |
| 3 | Implement real decoders/drivers; exercise 4×64 with repeated bright/dark row transitions and a target-length loaded column | No double selection, reset/capture interference or stale stored charge; complete repeated output checks; idle-row leakage and full-column loading measured |
| 4 | Assemble 64×64 with power grid, pad ring, real clocks/references and output interface | Exact connectivity/device census; routed joins; full-chip extraction; boundary/interior/worst-load and repeated-frame checks; actual ADC/load validated |
| 5 | Final release review and wafer.space precheck on exact submission geometry | Required process/supply/temperature and wire corners, nonlinear startup/protection, numerical refinement, DRC/LVS/ERC, density/antenna, optical keepouts, seal/pads/bond map and reproducible release package |

Manufacturing/pad planning and addressing design can proceed alongside analog
qualification. Expand only after each small physical tile passes. Keep the
large existing bank as a diagnostic reference; avoid repeated routing changes
to geometry that cannot fit the selected slot.

## Bound the simulation work

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

The [wafer.space Run 3 table](https://wafer.space/) currently lists purchase by
**9 December 2026**, clean GDS by **16 December 2026**, both 23:59 AoE, and parts
in Q2 2027. These are provider dates, not a project commitment or a booked slot.
Use the dated table; the page also contains inconsistent expired-countdown text.

There is no defensible “days from tapeout” estimate: full-bank layout fit
and coupled 64-column simulation remain unresolved. Re-estimate after milestones 1–2
using measured run times and the completed tile. The extracted single tile
and shared two-column control now pass their scoped development screens; the next
deliverable is a working compact 1×64 row and bank.

Still confirm: full-slot budget/booking, intended run, optical bonding/encapsulation,
permitted aperture/fill treatment, actual ADC and operating range. The
[manufacturing review](docs/manufacturing-review.md) tracks those open items.
The template supports changing signal pad types while preserving default bond
positions; generate and check the actual analog pad allocation rather than
assuming its two default analog pads satisfy all references/output connections.

[Immediate commands](NEXT_STEPS.md) · [Handoff](PICK_UP_HERE.md) ·
[Prior planning snapshots](checkpoints/planning-history-20260925/README.md)
