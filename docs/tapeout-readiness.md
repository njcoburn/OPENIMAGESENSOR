# Tapeout readiness and array scaling — 24 September 2026

**Superseded planning sequence — 2026-09-25:** the user now targets 64×64 first silicon on wafer.space GF180 at a modest frame rate. The [current plan](../COMPLETION_PLAN.md) and [slot-fit study](64x64-slot-fit.md) take precedence. Compact pixel/bank geometry is required; a separate 3×3 tapeout is not a prerequisite. The earlier scope and evidence below are preserved.

**The 3×3 is a working normal-operation simulation candidate, not a tapeout-ready chip.** It now has complete nominal and selected loaded frames, matched DC readout checks, numerical refinement, selected load/corner results, and recorded scoped layout/connectivity checks. The work has moved beyond proving that a single row can run. It has not yet closed the release gates below.

The [readout/cold-pad follow-up](readout-followup.md) now supplies tested conditional ways to address the load and cold-DC blockers. They require physical interface adoption and broader combined validation; the release gates remain.

## What must close before releasing the demonstrator

| Gate | Evidence available | Work remaining |
|---|---|---|
| Normal imaging/readout | Nominal 27 samples; 100 kΩ loaded 27 samples; selected supply/hot-corner passes | Adopt/review the selected physical interface and actual ADC; validate the combined proposal across the required load/PVT range |
| Model and power-up | Stock nominal DC and bias-validated normal-operation capacitor approximation | Nonlinear startup/protection; independent model review; full distributed wire resistance plus capacitance and its refinement |
| Physical release | Recorded main DRC, device LVS, density/antenna and connectivity checks for the existing small layout | Final run-specific checks of the exact released geometry, pad/ESD and power review, die/seal/bond requirements |
| Optical package and manufacturing | Carrier concept and native board projects; custom pad arrangement | Select the manufacturing/bonding route and confirm permitted optical access, openings/keepouts, bond map and package compatibility |
| Test and bring-up | Fast generic sample/hold regression; external ADC fixture concept | Validate the actual ADC/interface sequence and a practical electrical/optical measurement plan |

Optical sensitivity, dark current, noise and pixel variation have not been measured in silicon. A first technology-demonstrator tapeout can be designed to measure these; they must be explicit first-silicon uncertainties, not advertised as established camera performance. No calendar tapeout estimate is justified until the intended release scope and manufacturing requirements are fixed.

## Target-length strip evidence

The [1×64 and 64×1 tests](array-strips.md) now complete with explicit wire resistance and capacitance, finite drivers, supply impedance and schematic shared readout. Their nominal fixed-sense settling results support continued scaling work, with a documented reset-capacitance placement approximation. Long-row free-integration timestep refinement still misses the 10 µV criterion. The long row reveals substantial exposure skew and late bright-pixel over-integration. These strips do not close full-chip RC, startup or full-array release gates.

The [capture follow-up](array-recovery.md) now passes 64-column nominal/hot accuracy and refinement with a 40 pF store and buffer per column. Maximum errors are 171.295/289.919 µV. This removes the measured within-row exposure gradient, while the old serial mode remains numerically unqualified. The new periphery is schematic: about 8.1 mA modeled analog current and a 354 mV row-enable local supply dip require distributed physical power routing. A conditional 1.3–2.6 mm² storage-bank area and ~10.5 frames/s non-overlapped timing budget inform the next tile; neither is a selected release specification.

## Why larger arrays need more than repeated pixels

The existing 3×3, 4×3, 3×4 and 4×4 core tests support **local pixel replication**. The 4×4 has also been exercised with staged shared readout. This is useful evidence, but not a full-camera extraction or electrical qualification at a much larger size.

The existing physical pixel pitch is 80 × 50 µm. At that pitch, a 64×64 array budgets approximately **5.12 × 3.20 mm for the array alone**, before addressing/readout, supply routing, pads and seal ring. The current roughly 1.21 mm square demonstrator floorplan is therefore not a container into which that array can simply be copied. A compact-pixel redesign would need its own layout, extraction and verification.

The present interface directly controls reset and select for every row and selection for every column. Directly extending it to 64 rows and 64 columns gives **192 control nets** (`2 × rows + columns`), before analog references, output and supplies. A larger camera therefore needs an addressing architecture, such as on-chip decoding or scan registers, as well as a column-readout plan.

Longer row/column wires increase load, delay and coupling; more pixels alter shared-line capacitance, leakage and supply demand. These effects must be measured on extracted target-length structures. The pixel keeps integrating during sequential readout, so a wider row also increases exposure differences between early and late columns. A larger camera must budget that skew or provide an appropriate capture/readout architecture. The recent external-capacitance failure is a concrete example of why a working small circuit does not automatically preserve its timing margin under a larger load.

## Readout arithmetic, not a performance claim

With one serial sample per pixel, the ideal readout-only time is `rows × columns × slot time`. For 64×64:

| Assumed slot | Readout-only frame time | Ideal upper frame rate |
|---|---:|---:|
| Existing 18 µs regression slot | 73.728 ms | 13.56 frames/s |
| Capture candidate: 20 µs slot | 81.92 ms | 12.21 frames/s, output only |
| Proposed 50 µs diagnostic slot | 204.8 ms | 4.88 frames/s |
| Budget for 30 frames/s | 8.14 µs/pixel | 30 frames/s before any overhead |

These are arithmetic bounds, not simulated 64×64 results. Reset, settling, ADC conversion, data transfer and any additional reset/reference sample consume time. Exposure scheduling may overlap some operations but does not eliminate the required output sample throughput. The existing ADS1115 fixture is intended for slow measurements; no large-camera ADC choice or frame rate is established here.

## Concrete scaling sequence

1. Finish the current load and cold-pad investigations, keeping proposed interface changes distinct from the unchanged baseline. Close startup/full-R+C and demonstrator release gates as appropriate to the chosen first tapeout.
2. **Confirmed next array target: 64×64; frame rate undecided.** Establish exposure range and external ADC/load, using extracted timing results to inform the frame-rate choice. Decide whether first silicon is a technology demonstrator or the larger camera.
3. **Initial 1×64 and 64×1 extraction tests are complete.** The simultaneous-capture candidate now passes selected full-row electrical tests; implement its capacitors, clock and distributed supplies on the next extracted tile. Check the additional coupling and power loading of neighboring rows/columns on the next tile.
4. Implement and verify addressing/readout on an intermediate tile, then assemble and extract the full intended array. Repeat electrical, physical and manufacturing checks against its own geometry.

This keeps the verified pixel work reusable while exposing the system-level changes before committing to a large die. The user has confirmed 64×64 as the next target. Frame rate remains undecided; the arithmetic above is a planning bound, not a committed performance specification.

[Current electrical results](camera-operating-corners.md) · [Array-extension evidence](array-extension.md) · [Full-chip electrical gates](full-chip-electrical-plan.md) · [Manufacturing review](manufacturing-review.md)
