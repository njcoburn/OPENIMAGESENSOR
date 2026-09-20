# Resistor reduction and capacitance-placement sensitivity

Recorded **2026-09-19 01:11 PDT**. Release target: **3×3 demonstrator**.

**All four resistor networks are reduced and verified.** Six short placement transients and their six half-timestep refinements complete. The full corner needs a separate nonlinear startup treatment; its result is reported below.

![Network reduction and refined placement response](assets/charge-reduction.png)

## Reduction results

| Coupon | Original R | Reduced R | Eliminated nodes |
|---|---:|---:|---:|
| fill10-full | 2,259 | 1,196 | 1,370 |
| fill10-metal | 1,914 | 12 | 1,184 |
| corner-full | 571,551 | 87,748 | 316,078 |
| corner-metal | 451,892 | 12 | 253,777 |

The Schur complement eliminates only nodes connected exclusively through resistors. Ports, all semiconductor terminals, and capacitor terminals for **both** placements remain. Thus this reduction introduces no frequency-dependent approximation for the stated reference circuit; it is subject to numerical precision. Device records and capacitor values are unchanged.

Three independent terminal-voltage excitations per resistor component compare original and reduced currents and power. Maximum relative current error: **1.59e-10**; energy error: **1.46e-10**. The serialized models additionally pass 16 DC rail-resistance comparisons, maximum relative error **6.21e-10**, and preserve the original capacitance-pair matrix for both placements. No new layout/LVS/DRC run is claimed; device records retain the preceding topology evidence.

## Placement experiment

The nominal model uses the original named node, or nearest recorded resistor-node coordinate when that name was eliminated. The alternate moves each lumped capacitor anchor to the most distant recorded coordinate **within the same original resistor-connected net**. Both preserve the original R-collapsed capacitance matrix. This is a deliberately different geometric placement, not a proven physical worst-case bound or a distributed field-extracted capacitance model.

The short fixture uses 3.3 V at 27 °C, a shared 2 Ω source, two 100 kΩ standby loads, and simultaneous 1 mA-per-rail load pulses with 1 ns edges. Full coupons retain their PDK devices. In metal-only fixtures the implicit substrate is explicitly grounded. No package inductance is included.

| Completed short fixture | Refined maximum placement change (µV) | Largest 1 ns→0.5 ns timestep change (µV) |
|---|---:|---:|
| fill10-full | 8.986 | 12.299 |
| fill10-metal | 1.551 | 0.814 |
| corner-metal | 76.222 | 1.593 |

The full filler's placement difference is comparable to its numerical variation, so its few-microvolt peak is not accurately resolved. The metal-only corner's approximately 76 µV edge difference is much larger than its timestep variation. Late samples at 1.5 µs agree to saved precision in these short fixtures. This is rail behavior in a chosen fixture, not pixel/ADC error qualification.

## Full-corner solver and startup results

The full corner's AC sweeps complete using KLU. Maximum complex voltage-transfer difference is **6.3674e-05 V/V through 1 MHz**, and **0.054615 V/V through 1 GHz**. The wide sweep is diagnostic, not a claim that the lumped PDK model is physically valid to 1 GHz.

The initial hierarchical and flat SPARSE runs timed out. KLU completed AC, but transients starting from the DC solution aborted at time zero in a MOS-capacitor controlled-source branch. Those attempts are retained as non-passes. Using rail `.nodeset` guesses and the earlier practical clamp settings did not establish a completed DC-start transient.

The separate supply-ramp fixture uses the repository's GF180 clamp initialization (`ngbehavior=hsa`, `wnflag=1`), KLU, one simulator thread, `gmin=1e-17`, `abstol=1e-12`, `reltol=1e-6`, and zero-charge startup (`uic`). It ramps the supply over 100 µs, holds until a 1 mA-per-rail pulse at 151 µs, and runs to 153 µs with a 100 ns maximum step and adaptive steps at the 1 ns pulse edges. This fixture is explicitly different from the short DC-start experiment.

Both full-corner supply-ramp runs abort just after 100 µs in `e.x354.ec_moscap#branch`, before the 151 µs load pulse. They are not transient passes. The complete AC sweeps remain valid, but full-corner transient placement sensitivity is unverified.

Two bounded-degree star-mesh alternatives were also electrically verified, but retained 512,726 and 533,044 resistors and were not selected. An energy-bound sparsity inspection found that a tight bound removes too few dense edges to solve the performance issue; no resistor pruning was applied.

## Next acceptance gate

Test the voltage/current-preserving interface already used in the earlier clamp-convergence work around the corner macro, and verify its terminal equivalence. Resolve the MOS-capacitor startup abort before refining the full-corner load comparison and integrating the 3×3 model.

The placement probe is not a manufacturing guarantee. Substrate-domain interpretation, accurate spatial capacitance, native Magic capacitance-export accounting, and full-chip qualification remain open. The first release remains the 3×3 demonstrator. Production GDS and installed tools are unchanged.

## Reproduce

Prerequisite: the charge-reference checkpoint and its original extraction dependencies.

```sh
bash scripts/run-tools.sh python3 scripts/reduce-charge-reference.py
bash scripts/run-tools.sh python3 scripts/audit-charge-reduction.py
bash scripts/run-tools.sh python3 scripts/check-charge-placement.py
# The command above retains the full-corner timeout as a non-pass.
bash scripts/run-tools.sh python3 scripts/refine-charge-placement.py
bash scripts/run-tools.sh python3 scripts/check-charge-placement.py --practical-corner
# This DC-start attempt retains the MOS-capacitor transient abort.
bash scripts/run-tools.sh python3 scripts/check-corner-placement-startup.py
bash scripts/run-tools.sh python3 scripts/report-charge-reduction.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The checksummed evidence archive includes the reductions, placement maps, simulator decks/logs/waveforms, failed attempts and scripts. Large parent reference inputs remain in the charge-reference checkpoint, linked by source hashes.
