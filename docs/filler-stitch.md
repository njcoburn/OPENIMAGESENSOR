# Two-filler stitching — conductor-only DC benchmark

## What this completes

A stitched pair and a combined model now preserve the same 81 metal intervals across the x = 10 µm boundary: one M1 interval, two M2 intervals, and 26 each on M3, M4 and M5. The finest mesh uses 4,593 distinct interface ports rather than one ideal node per rail. Stitched and combined DC resistance agree below the 1e-8 relative screen on four meshes.

This is **not a stitched Magic RC/device model**. It is a separate finite-volume conductor reference to validate the boundary construction and expose differences from the earlier extraction. Device/capacitance/substrate stitching remains unfinished. See [the HTML comparison](overview.html#filler-stitch) and [machine-readable results](../simulations/filler-stitch.json).

## Geometry and material ownership

The input is the unchanged conductor-only two-filler coupon with its external measurement leads. Each metal region is decomposed into exact Manhattan rectangles and checked by polygon XOR. Left and right partitions are constructed from clipped geometry; their union equals the complete region and their interiors do not overlap. This avoids counting overlapping macro-edge material twice. No via cut crosses the partition in this coupon.

An independent KLayout inspection enumerates the physical boundary intervals. The report compares every interval's coordinates, not just their count. Every stitched interface node must have exactly two connections, one into each half; deliberately omitting a port fails the coverage check.

The mesh aligns every metal edge and the boundaries of the outer measurement electrodes. It subdivides large cells to maximum dimensions of 2, 1, 0.5 and 0.25 µm. Each crossing interval is represented by multiple separate face nodes as needed. It is not made equipotential across its full width.

## DC model

Parameters are read from the nominal section of the installed `gf180mcuD.tech` file:

- M1–M4 sheet resistance: 0.09 Ω/square.
- M5 sheet resistance: 0.04 Ω/square.
- V1–V4: 4.5 Ω per cut.

The recorded technology-file hash identifies the source. No temperature coefficients or process corners are included.

Lateral face conductance is face width divided by center-to-center distance and sheet resistance. Each via cut's conductance is distributed by exact overlap area with the mesh cells on its two metal layers; total conductance is conserved. This is a modeling approximation, not an assertion that it reproduces Magic's internal tiling.

The combined model connects adjacent cell centers directly. Each independently built half instead connects its boundary cells to separate seam ports through its own half-cell resistance. Joining matching seam ports produces the stitched network. A sparse nodal solve applies 1 A between each rail's two outer electrodes, checks current balance, positive resistance, energy consistency, and isolation of the four rails. A finite 0.2 × 0.2 µm equipotential outer electrode is used, which differs from Magic's terminal interpretation.

Matrices, terminal maps, and a real SPICE netlist with `half_left`, `half_right`, and `filler_stitched` subcircuits are saved for each mesh. The 1 µm hierarchical SPICE model passes an independent ngspice DC comparison within 2e-6 relative error. The finer 0.5 µm ngspice run timed out at 120 seconds; its separate matrix comparison passes. The finest run is matrix-only. A passed matrix partition check must not be reported as a completed ngspice run.

## Limits of the result

The extremely close stitched/combined match establishes consistency of the partitioned discretization. It does not establish absolute resistance accuracy: both constructions share the material parameters, mesh rules and electrode assumptions. The latest mesh refinement still changes the resistance estimates, and there is a material difference from the earlier Magic conductor-only extraction. Those values remain diagnostic, not calibrated macro resistances.

All resistance values include the external probe leads. No lead resistance has been silently subtracted. No capacitance, transistor, semiconductor-ground path, or temperature behavior is included. The earlier negative capacitor entries and corner ground-coupling issues are not resolved by this experiment. The original sensor and ring geometry are unchanged; no new fabrication DRC/LVS claim is made for this numerical fixture.

## Reproduce

Restore or regenerate the preceding ring-section coupon first, then run from the repository root with the pinned Docker image:

```sh
bash scripts/run-tools.sh python3 scripts/inspect-filler-boundary.py
bash scripts/run-tools.sh python3 scripts/prepare-filler-stitch.py
bash scripts/run-tools.sh python3 scripts/compare-filler-stitch.py --step-um 2 --skip-spice
bash scripts/run-tools.sh python3 scripts/compare-filler-stitch.py --step-um 1
# Optional independent simulator attempt; the recorded attempt timed out:
bash scripts/run-tools.sh python3 scripts/compare-filler-stitch.py --step-um 0.5
# Save matrix results separately without implying an ngspice pass:
bash scripts/run-tools.sh python3 scripts/compare-filler-stitch.py --step-um 0.5 --skip-spice
bash scripts/run-tools.sh python3 scripts/compare-filler-stitch.py --step-um 0.25 --skip-spice
bash scripts/run-tools.sh python3 scripts/report-filler-stitch.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

An independent ngspice attempt writes `ngspice-attempt.json`; `--skip-spice` preserves that evidence while recording that the current run is matrix-only. Successful simulator results and timeouts are distinct from the DC partition verdict. The optional simulator run can take up to the 120-second watchdog. Sparse-matrix runs are much faster in the measured environment.

The checksummed archive under `checkpoints/filler-stitch/` contains the input geometry, terminal maps, conductance matrices, hierarchical resistor netlists, logs, results and source scripts. Restore into a separate review directory to avoid overwriting newer sources.

## Next acceptance gate

1. Refine and benchmark the outer electrode/probe-lead treatment on controlled shapes; establish spatial convergence before trusting absolute resistance.
2. Reconcile the resulting values with Magic under equivalent terminal and material assumptions.
3. Transfer the distributed interface to device-aware sections and compare a stitched extraction against a combined extraction, including internal device taps.
4. Resolve capacitance passivity and corner semiconductor-ground treatment before assembling the full ring and running camera transients.
