# Adding rows and columns — 2026-09-20

**All four array sizes complete three frames in both device-only and extracted-capacitance simulations.** This is evidence that the pixel array can extend to four rows and four columns under the tested loading. It does not resolve or reproduce the final assembled camera failure.

Dimensions below are **rows × columns**. Each physical pixel has a 20 × 20 µm photodiode, three 1 µm / 0.5 µm NFETs, and an 80 × 50 µm placement pitch. The generator repeats the existing physical pixel, extends actual metal supply/column trunks and row rails, and extracts each newly generated layout with Magic. Netgen checks each against an independently generated schematic. The 3×3 control is geometrically identical to the existing unfilled 20 µm array on all physical drawing layers; labels are not part of that geometry comparison.

| Array | Pixels | Extracted wire capacitors | DRC / device LVS | Device-only / C-only transient | Frame 2→3 max change (µV, C-only) | Common 3×3 pixels versus control (µV, C-only) |
|---|---:|---:|---|---|---:|---:|
| 3 × 3 | 9 | 168 | Pass / pass | Both complete | 6.88 | 0.00 |
| 4 × 3 | 12 | 220 | Pass / pass | Both complete | 6.77 | 16.23 |
| 3 × 4 | 12 | 216 | Pass / pass | Both complete | 6.86 | 0.03 |
| 4 × 4 | 16 | 283 | Pass / pass | Both complete | 6.78 | 16.21 |

All sampled pixels have the expected ordering at 0, 80 and 240 pA: more photocurrent produces a lower column voltage. Three-row runs finish at 9.05 ms; four-row runs at 12.05 ms. The comparison uses each pixel's sample 970 µs after its reset pulse starts. Adding a row increases frame period from 3 to 4 ms; the common-pixel difference therefore includes that changed history, not just additional loading.

## What these simulations include

PEX means parasitic extraction: it supplies layout-derived elements to an electrical simulator. These terms are not alternatives.

- **Device-only controls:** actual layout-extracted transistor/diode geometry and PDK device capacitances, without extracted wire capacitors.
- **C-only PEX:** the same devices plus all extracted wiring/coupling capacitances, with no capacitance pruning or grounded remote coupling plates. There are no capacitor-only floating nodes in these four coupons.
- **Boundary conditions:** ideal 3.3 V supply and 2 V reset reference; 100 Ω series row/reset control drivers; separate 1 MΩ || 1 pF loads on each column; 10 ns control edges. Column voltages are sampled directly.
- **Excluded:** shared column mux/bias/output buffer and ADC acquisition, pad protection and supply clamps, density fill, distributed wire resistance, optical propagation, calibrated photon conversion and noise. These unfilled core coupons are not complete die layouts or fabrication signoff.

The final-chip simulation that originally failed also uses extracted devices and wiring capacitance, but its normal-operation candidate freezes 1,680 MOS capacitors at settled bias. Distributed wiring resistance remains unqualified there. Earlier array studies have separate RC extraction evidence; that does not turn either this C-only experiment or the final-chip candidate into full-chip RC qualification.

## Retained initial failure

The first 3×3 control used ideal zero-impedance row/reset drivers. Its device-only run completed, but its C-only run aborted at 2.07002 ms with a timestep error naming `vs1#branch`. Changing the control drivers to 100 Ω series impedance gives the completed matrix above. That changes the electrical boundary condition and is not a proven equivalent numerical rewrite. It does not establish the cause of the original whole-chip abort at 3.27002 ms. Both original decks and logs are retained.

## Reproduction and next step

Run `python scripts/check-array-extension.py --output /foss/designs/build/<new-unique-directory>` inside the existing tools container. The generator refuses an existing output directory. It uses the archived `build/size-study/20um/build/pixel_physical.gds` primitive. Maximum timestep is 200 ns with Gear integration and explicit tight tolerances; no tolerance relaxation was used between array sizes.

[Machine-readable results](../simulations/array-extension.json) contain all three sampled frames, source hash and scope. Exact layouts, extracted decks, independent LVS references, waveforms and logs are retained in `build/array-extension-finite-20260920/` and archived with hashes under `checkpoints/array-extension/`.

Next, connect this parameterized array to the shared readout and restore supply/pad/clamp blocks in stages, checking complete frames at each step. Extending the full camera requires that integration test and then extraction of its own routed layout. The original assembled-chip failure remains open; these results give us a working physical array baseline to build from.
