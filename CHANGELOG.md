# Changelog

This log summarizes engineering checkpoints. Simulation passes apply to the stated model and test conditions; they do not establish optical performance, manufacturing yield, or fabrication readiness.

## 2026-09-16 — Extracted camera, pads, and physical supply ring

Recorded **2026-09-16 13:11 PDT (America/Los_Angeles, UTC−07:00)**. This entry consolidates the work since commit `a87383d`; individual experiments were performed across the preceding sessions.

### Pixel array and extracted readout

- Added resistance/capacitance extraction of the 20 µm photodiode 3×3 array, with schematic, capacitance-only, and RC comparisons.
- Added column bias, a column multiplexer, and a shared output buffer, including layouts, extraction scripts, and off-chip ADC load simulations.
- Investigated cold idle/startup convergence and hot sampling margin. Revised the buffer reference to 40 µA and added an all-row startup reset; retained diagnostic failures and follow-up evidence.
- Connected the array, readout, and buffer in a physical test core: **37 MOS devices and nine photodiodes**, with passing recorded Magic/KLayout DRC and unique Netgen LVS.
- Completed the connected-core **24-condition process/temperature matrix**: all RC cases pass the 0.5 mV sampling screen; worst HOLD error is approximately **0.207 mV**. Wire R/C remains nominal and bias references are ideal in this matrix.

### Bias, pads, and board interface

- Added an external-resistor bias candidate: 5.1 MΩ from VDD to BIAS and 49.9 kΩ from PREF to ground. Recorded 84 DC and 18 selected startup/imaging cases; worst sampling error is approximately **0.216 mV**.
- Researched foundry GF180 pad macros and wafer.space/Tiny Tapeout references; evaluated analog-pad leakage, loading, and local protection candidates.
- Laid out a local protection cell with a nominal **149 Ω** poly resistor and extracted its capacitance. Recorded selected imaging checks and pad-wrapper LVS.
- Distinguished the untouched pad's 87 CUP.3 findings from the wafer.space-configured coupon checks, which exclude CUP and reported zero main, density, and antenna markers. These are different verification scopes.
- Evaluated foundry supply clamps, soft-start, and reset hold. Completed nominal/hot three-frame camera-plus-clamp runs with all 27 samples per run passing and worst sampling error approximately **0.221 mV**, corroborated by independent numerical checks.
- Added assumed board supply resistance, inductance, and local decoupling, including a weaker-supply sensitivity case and a finer hot simulation. These earlier camera tests use the supply-pad pair, not the new complete physical ring.

### Physical supply ring checkpoint

- Built a **1.110 × 1.010 mm** development ring from two supply pads, four corners, and 125 foundry filler cells; included all **ten clamps** and filler decoupling in the schematic model.
- Placed the unchanged 3×3 sensor inside the ring and routed power/ground using 4 µm trunks and bridges to the existing core buses.
- Recorded **zero ring Magic DRC violations**, **zero configured KLayout DRC violations on ring and assembly**, and a **unique flat ring device LVS match**.
- Independently checked metal/via connectivity: **10,948 assembly probes pass**, with no supply-to-ground short.
- Extracted the actual connecting-wire RC. Widening routes reduced total added resistance from **27.1802 Ω to 12.34158 Ω**: VDD **5.14704 Ω**, ground **7.19454 Ω**.
- Completed nominal/hot ring load tests using foundry schematic devices plus extracted connecting wires. Maximum core-supply drop: **2.567 mV nominal**, **2.451 mV hot**; both pass the declared 1% rail screen.
- The finer hot run agrees within **0.036 µV at core VDD** on the common comparison grid, below the 10 µV numerical screen.

### Incomplete work retained explicitly

- Four full-ring distributed RC extraction variants were stopped without a complete validated model. Their logs/intermediates are preserved; none is substituted for a verified camera model.
- Strict direct and exact-interface ring-load diagnostics timed out after 900 seconds. The completed ring load tests use the documented practical tolerances.
- Ring-metal resistance, complete assembly coupling, signal-pad routing, and full camera simulation with the physical ring remain outstanding.
- Ring DRC uses `all,-antenna,-density,-cup`. No complete die precheck, ESD stress, optical response, package, or fabrication qualification is claimed.

### Documentation and reproducibility

- Expanded the living [HTML notebook](docs/overview.html) with layouts, plots, comparison tables, assumptions, and failed-run evidence.
- Added source circuits, layout generators, simulation/check/report scripts, JSON results, GDS/netlist checkpoints, and checksummed evidence archives.
- Updated the top-level README with actual assembly and performance pictures, alongside the original labeled pixel, array schematic, and camera concept.
- Added the dated [continuation plan](NEXT_STEPS.md). The pinned Docker workflow remains the supported environment; no new host virtual environment was required.

## Earlier committed checkpoints

- **`a87383d` — Architecture and resolution overview:** README camera concept, area planning, grayscale resolution comparison, and HTML slider.
- **`8d76ff3` — Labeled layout and schematic:** README views of the larger photodiodes, pixel transistors, and 3×3 Xschem hierarchy.
- **`be0a047` — Verified GF180 arrays and Docker workflow:** single-pixel/repeatability work, 3×3 array schematics/simulations, 5/10/20 µm diode-size layout comparisons, local DRC/LVS, saved evidence, and Docker/VNC reproduction.
- The original gdsfactory prototype remains in [test.py](test.py); later verified layout work is under [layout/](layout/).
