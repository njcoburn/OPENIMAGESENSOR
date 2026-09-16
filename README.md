# Open Image Sensor

An open monochrome image-sensor experiment using GF180MCU, Xschem,
ngspice, gdsfactory, Magic, KLayout, and Netgen.

**Project checkpoint: 16 September 2026** · [Changelog](CHANGELOG.md) · [Dated next steps and handoff](NEXT_STEPS.md) · [Engineering notebook](docs/overview.html)

## Architecture overview

Our proposed camera is a **64 × 64 monochrome array** with a **40 µm pixel
pitch**, retaining the **20 × 20 µm photodiode** inside each pixel. The concept
reserves space for row control, column readout, multiplexing, output buffering,
and the perimeter bond pads and protection structures.

![Conceptual full-slot camera floorplan with a 64×64 array, row control, column circuits and perimeter pads](docs/assets/camera-floorplan-concept.png)

**Planning concept—not a routed or verified 64×64 chip.** The verified hardware
layout is currently a 3×3 array. The 2.56 × 2.56 mm proposed camera array fits
within the published 3.05 × 4.24 mm full-slot core as an area estimate; compact
pixel routing, optical packaging and readout performance still need verification.

| On the sensor die | On the camera board |
| --- | --- |
| Photodiodes and three-transistor pixels | External amplifier and ADC |
| Row sequencing and column multiplexing | MCU or FPGA for timing and image capture |
| Column bias, sampling and output buffer | Power supplies, references and connectors |
| Bond pads and protection | Wire-bond carrier, optical window and lens mount |

Signal path: **light → pixel → column readout → output buffer → bond pad →
board ADC → controller**. This is the proposed system partition; several blocks
remain to be designed.

## Physical supply ring checkpoint

The unchanged 3×3 sensor now sits inside a **1.110 × 1.010 mm foundry-macro supply ring**, with routed power and ground. Ring device LVS matches uniquely; configured KLayout DRC reports zero violations on the ring and assembly, and 10,948 physical continuity probes pass.

![Actual supply-ring and sensor assembly](docs/assets/power-ring-sensor.png)

Extracted connecting-wire resistance is **5.147 Ω on VDD and 7.195 Ω on ground**. Nominal and hot load tests pass the 1% rail screen using foundry schematic ring models plus those wire parasitics. **Full-ring distributed RC extraction remains unfinished.** Signal pads, complete camera simulation with ring RC, and fabrication qualification remain to be done.

![Connecting-wire resistance reduction and nominal/hot supply-load simulation](docs/assets/power-ring-performance.png)

The plot uses ring schematic devices plus extracted connecting wires. It does not include full-ring metal RC. Ring DRC uses `all,-antenna,-density,-cup`; these results are development checks, not complete die signoff.

[Results and plots in the running notebook](docs/overview.html#power-ring) · [Reproduction and limitations](docs/power-ring.md)

## Board supply simulation

The extracted 3×3 camera and foundry supply clamps are now tested with an assumed board RLC supply and local decoupling. See the [running notebook](docs/overview.html#board-supply) for nominal/hot results, a weak-supply sensitivity case, and numerical checks. [Reproduction instructions](docs/board-supply.md) identify the model assumptions and remaining regulator/package/pad-ring work.

## Earlier checkpoint: pad checks and supply-clamp evaluation

The unchanged analog-pad interface has **zero main, density and antenna DRC
markers** using wafer.space's published rule selection. That selection excludes
CUP; the earlier unfiltered report retains its 87 CUP.3 findings. This is a
coupon-level check, not a full die submission precheck.

A foundry VDD/VSS clamp pair is now modeled on the 3.3 V analog supply. Across
324 DC cases, modeled pair leakage is **0.146 nA nominal, 76.19 nA maximum**.
Fast ramps activate the clamps strongly. A **1 ms soft-start plus 200 µs reset
hold** is the current candidate: all 18 finite-source follow-up cases settled,
including six 1 ms cases. High-voltage MOS models remain typical; this is not
complete ESD or transistor-corner qualification.

**The full three-frame camera-plus-clamp simulation is now verified** at
nominal and hot conditions. All 27 samples per run pass, with worst sampling
error **0.221 mV**. The direct connection uses a 1 pA absolute-current
tolerance and a 1200 s watchdog; independent strict-tolerance and finer-step
checks corroborate the results. See the [convergence report](docs/overview.html#clamp-convergence)
and [reproduction instructions](docs/clamp-convergence.md).

![Supply-pad candidate and analog power domain](docs/assets/supply-pad-plan.svg)

See the [running notebook](docs/overview.html#pad-closure) and
[reproduction notes](docs/pad-closure.md) for comparison plots, numerical
failures and follow-ups, exact rule selection, and qualification limits.
This earlier simulation uses a supply-pad pair. The physical ring above adds corner clamps and filler decoupling; its full RC camera simulation and stress qualification remain open.

## What increasing resolution looks like

![The same grayscale scene sampled at 3×3, 8×8, 16×16, 32×32, 64×64, 96×96, 128×128 and 256×256 pixels](docs/assets/resolution-comparison.png)

The same synthetic scene is sampled at each resolution with a fixed field of
view. This illustrates ideal sampling, **not predicted GF180 image quality**;
noise, optics and detector efficiency are not modeled, and higher resolutions
shown here are not claims of fitting this die.

The [HTML notebook](docs/overview.html) includes an **interactive resolution
slider**, manufacturing and packaging research, and the full design history.
Clone or download the repository and open `docs/overview.html` in a browser to use the slider offline. Keep the adjacent `docs/assets/` folder for the newer layout and result images. The images above provide the README preview.

## Earlier milestone: standalone 3×3 array

A connected 3×3 physical array, matching hierarchical Xschem schematic,
row-scan simulation, zero Magic DRC errors, zero violations from the installed
full GF180MCUD KLayout DRC deck, and unique Netgen LVS matches.
The checked array contains 27 MOSFETs and nine physical diodes.
These are local core checks, not a completed camera or manufacturing signoff.

- [Living HTML notebook](docs/overview.html): report with
  schematic/layout captures, plots, measurements, limitations and history; keep `docs/assets/` beside it.
- [Layout implementation and verification](layout/README.md).
- [Simulation notes](simulations/README.md).
- [Original gdsfactory prototype](test.py), preserved unchanged.

## Labeled 20 µm pixel layout

![Labeled GF180 3×3 layout showing reset, source follower, row select, photodiode, horizontal buses, column output and dummy fill](docs/assets/large-pixel-labeled.png)

The larger variant has nine **20 × 20 µm photodiode junctions** at an
80 × 50 µm pixel pitch. Labels identify one representative pixel; its three
transistors and photodiode repeat nine times. Callouts use source coordinates
over the original VNC screenshot. [Open the scalable image](docs/assets/large-pixel-labeled.svg).

## 3×3 array schematic

![Xschem schematic of nine three-transistor pixels with shared row controls and three column outputs](docs/assets/xschem-array.png)

Each block contains a reset transistor, source follower, row-select transistor
and photodiode. The rows share reset/select controls and the three columns provide
separate outputs. This hierarchy is shared by all three diode-size variants.
[Open the Xschem source](xschem/array_3x3.sch).

## Checkpoint and workstation setup

- [Docker/VNC setup, checkpoint restore and full reproduction](docs/docker-setup.md).
- [Saved generated checkpoint](checkpoints/README.md).
- [5/10/20 µm diode-size comparison](docs/diode-size-study.md): all three layouts pass local DRC/LVS; the HTML includes electrical response plots.

## Tools

No host `.venv` is required. The scripts use the existing IIC-OSIC-TOOLS Docker
image pinned in `scripts/run-tools.sh`, which contains gdsfactory 9.44.0 and
all currently required EDA tools. Set `IIC_OSIC_IMAGE` to override the image.
The old prototype's `gf180mcu` Python package is not installed; the new layout
imports checked PDK-generated primitive GDS into gdsfactory instead.

## Reproduce

With Docker Desktop/WSL integration available, run from this directory:

```sh
python3 scripts/make-array-schematics.py
bash scripts/verify-array.sh
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The existing report also incorporates prior single-pixel experiments. Their
reproduction commands are listed in `docs/README.md`; on a clean checkout,
regenerate those baseline waveforms before rebuilding the complete notebook.

Results include `build/array_3x3.gds`, reports under `build/array-check/`, and
machine-readable measurements under `simulations/`. Share the `docs/` directory together so the notebook and its linked assets open offline.

## Extracted array electrical comparison

The 20 µm 3×3 array now has extracted resistance and capacitance models,
with schematic, C-only and RC scan comparisons. See the
[HTML notebook](docs/overview.html#parasitics) and
[reproduction method](docs/parasitic-extraction.md).

## Revised buffer and startup sequence

The latest candidate uses a 40 µA buffer reference and an all-row startup reset.
See the [updated notebook](docs/overview.html#buffer-hardening) and
[diagnostic/reproduction notes](docs/buffer-hardening.md). The standalone
three-PMOS buffer layout passes Magic DRC, KLayout DRC and Netgen LVS.

## Buffer parasitic extraction

The buffer now has an extracted RC model connected to the separately extracted
array and readout. See the [latest notebook section](docs/overview.html#buffer-pex)
and [reproduction notes](docs/buffer-pex.md). This earlier experiment used ideal
inter-block wiring; the connected layout below supersedes that geometry.

## Connected 3×3 test core

The pixel array, column bias/multiplexer and output buffer now share physical
signal, supply and ground routes. The filled layout passes Magic DRC,
KLayout DRC and Netgen LVS (37 MOS devices and nine photodiodes).

![Connected array above, bias/mux lower left, output buffer lower right](docs/assets/integrated-functional.png)

See the [connected-layout notebook](docs/overview.html#integrated) and
[reproduction and extraction notes](docs/integrated-layout.md). This is a test
core without pads/ESD or physical reference/control generators.

The [connected-layout process/temperature matrix](docs/overview.html#integrated-corners)
extends the initial three checks to 24 conditions. See the
[scope and reproduction instructions](docs/integrated-corners.md).
All 24 RC cases pass the 0.5 mV sampling screen; the worst error is 0.207 mV.
This uses fixed nominal wire R/C, ideal reference currents and the generic ADC load.

## Physical bias and startup candidate

Two external resistors now replace the ideal current sources in a separate
simulation checkpoint: 5.1 MΩ from VDD to BIAS and 49.9 kΩ from PREF to ground,
feeding the existing on-chip mirrors. All 84 DC cases converge and all 18 selected
startup/imaging cases pass; worst sampling error is 0.216 mV.

See the [startup plots and comparison table](docs/overview.html#bias-reference),
[component and scope notes](docs/board-bias.md), and
[Xschem interface](xschem/board_bias.sch). This is a board-bias candidate;
pad/ESD leakage, resistor TC/noise and actual reset-supply generation remain ahead.

## Analog pad evaluation

The installed GF180 analog pad plus a candidate local protection network passes
five selected extracted-core imaging checks with a finite-transition ADC load:
worst HOLD error **0.217 mV** against the **0.5 mV** screen. Both candidates
converge across 84 matched DC cases each; the secondary network changes core
reference currents by less than **0.18%**.

See the [pad evaluation and plots](docs/overview.html#pad-evaluation) and
[reproduction/evidence notes](docs/pad-evaluation.md). The original ideal-switch
secondary-protection runs fail numerically and are preserved. These are
functional model results; pad layout, thin-oxide ESD protection and package
qualification remain outstanding. The core GDS is unchanged.

## Earlier checkpoint: physical analog-pad interface

A routed local protection cell now passes Magic DRC, the full installed KLayout
DRC deck and unique Netgen LVS. Its physical poly resistor is **149 Ω nominal**;
five selected imaging checks with local extracted capacitance pass, with a worst
sampling error of **0.221 mV**.

The combined single-pad wrapper matches LVS and is Magic-clean. KLayout reports
**87 CUP.3 findings**, identical to the untouched library pad, in the unfiltered deck. The later coupon checks described above use the published selection excluding CUP. Neither result establishes ESD qualification or complete-die readiness.

See the [layout views and results](docs/overview.html#pad-layout) and
[reproduction and verification scope](docs/pad-layout.md).
