# Sensor references

## Image Sensor Basics

- Author: Yuhao Zhu, University of Rochester.
- Course: CSC 292/572, Mobile Visual Computing, Fall 2022, Lecture 10.
- [Local PDF](lect10-sensor-basics.pdf)
- [Original source](https://www.cs.rochester.edu/courses/572/fall2022/decks/lect10-sensor-basics.pdf)
- Downloaded September 14, 2026; 101 PDF pages, 51,700,937 bytes.
- External reference material; attribution and rights remain with the original owners.

### Reading guide

Page numbers below are PDF page numbers, since slide builds repeat printed numbers.

| PDF pages | Topic |
| --- | --- |
| 10–23 | Quantum efficiency, integration, full well, dynamic range |
| 33–36 | Fill factor and pixel structure |
| 44–49 | Charge-to-voltage conversion, source follower, reset and sampling |
| 54 | Ideal monochromatic sensor model |
| 58–73 | CMOS readout and rolling/global shutter |

### Application to our GF180 design

The following are project recommendations, not GF180 specifications from the lecture.

Start with the three-transistor active pixel: photodiode, reset transistor,
source follower, and row-select transistor. Add a column current sink and load
capacitance in the testbench. Use GF180 transistor models and an explicitly
parameterized light-current model. Verify the installed PDK variant and device
voltage ratings before choosing supplies.

The transfer-gate example on PDF pages 45–49 uses a separate floating diffusion
and pinned-photodiode architecture. Our initial 3T pixel senses the photodiode
node directly. Its reset also erases the exposure signal, so do not copy that
example's post-exposure floating-diffusion reset sequence into our circuit.
Likewise, do not assume its correlated sampling noise benefits automatically
apply to the 3T readout.

First milestone: reset, integrate, and read one pixel at dark, dim, and bright
photocurrents. Plot sensing-node and column voltages; measure integration slope,
reset level, usable swing, and column settling. Sweep exposure and capacitance.
For approximately constant capacitance, the voltage drop magnitude is I*t/C.
Separate assumed optical response from PDK electrical behavior; this lecture
does not provide GF180 quantum efficiency, dark current, or diode capacitance.

Then build a small array with row timing, followed by gdsfactory layout,
design-rule and connectivity checks, and simulation with extracted parasitics.
Reserve optical access above the diode when planning metal routing. Treat noise
and mismatch as subsequent analyses: an ordinary deterministic transient run
does not establish sensor noise or dynamic range.

## Living project overview

[Open the HTML notebook](overview.html) for the circuit, timing, simulation
history, four-cycle waveforms, sampled results, limitations, and next steps.
The HTML embeds its images and works as a single offline file for sharing.

Regenerate after simulation changes:

```sh
bash scripts/simulate-cycles.sh
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Refresh `docs/assets/xschem-cycles.png` separately from the VNC desktop after
schematic changes. The builder embeds that capture, creates the waveform
plots, checks the readout data, and refreshes `overview.html`.

### Repeatability and the 3×3 target

The newest notebook sections compare 20-cycle reset conditions and define
pixel/array verification gates. Data: `simulations/repeatability.json`;
original failed numerical comparison: `simulations/repeatability-initial.json`.

```sh
bash scripts/simulate-cycles.sh
bash scripts/run-tools.sh python3 scripts/check-repeatability.py
bash scripts/simulate-reset-candidate.sh
bash scripts/run-tools.sh python3 scripts/check-reset-candidate.py
bash scripts/check-layout-probe.sh
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The report preserves earlier experiments and prepends new findings through
`scripts/overview-progress.py`. See `layout/README.md` for the 3×3 interface,
physical diode extraction issue and DRC/LVS acceptance criteria. The first
verified physical cell is one transistor, not the sensor pixel or array.

### Completed physical array

The notebook now starts with the verified 3×3 layout and scan results.
Reproduce with `bash scripts/verify-array.sh`, then rebuild the notebook.
The filled GDS and all reports are generated under `build/`; the checked
GDS fingerprint is saved in `simulations/array-verification.json`.
