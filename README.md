# Open Image Sensor

An open monochrome image-sensor experiment using GF180MCU, Xschem,
ngspice, gdsfactory, Magic, KLayout, and Netgen.

## Current milestone

A connected 3×3 physical array, matching hierarchical Xschem schematic,
row-scan simulation, zero Magic DRC errors, zero violations from the installed
full GF180MCUD KLayout DRC deck, and unique Netgen LVS matches.
The checked array contains 27 MOSFETs and nine physical diodes.
These are local core checks, not a completed camera or manufacturing signoff.

- [Living HTML notebook](docs/overview.html): self-contained file with embedded
  schematic/layout captures, plots, measurements, limitations and history.
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
machine-readable measurements under `simulations/`. `docs/overview.html` can
be shared by itself and opened offline.
