# Electrical qualification progress — 2026-09-19 10:03 PDT

**The 3×3 chip is not electrically qualified yet.** This checkpoint advances the numerical diagnosis while retaining the final-chip acceptance gates.

## Completed control investigation

The old standalone original/scaled comparison missed a 0.544 ns RC transient. Collinear source breakpoints resolve it without changing the physical supply waveform. At 50 ps and 25 ps local spacing, the maximum original/scaled current difference is 1.493 pA versus the unchanged 100 pA screen. Native-point errors versus an independently integrated terminal equation are below 2.875 pA. Integrated charge bookkeeping agrees to about 4.25e-8 relative in this fixture.

[Detailed control audit](clamp-control-reference.md) · [Machine-readable results](../simulations/clamp-control-breakpoints.json)

![Resolved control comparison](assets/clamp-control-breakpoints.png)

## Extracted-network results

The isolated 144-device clamp candidate completes at 50 ns. Its 25 ns normal and stricter-tolerance checks both complete and pass the recorded post-startup rail/capacitor voltage screens. Full-trace rail differences remain below 8.20 µV. Source-current differences are retained in the JSON; the voltage screens do not constitute a complete multiport current/charge-equivalence test.

| Test | Result | Evidence / scope |
|---|---|---|
| Isolated clamp 25ns | Complete | 0.328 µV rail difference |
| Isolated clamp 25ns-strict | Complete | 0.277 µV rail difference |
| Complete corner: nominal placement | Complete | 399.9 s runtime; not timestep-qualified |
| Complete corner: remote placement | Complete | 399.8 s runtime; not timestep-qualified |
| Complete corner: 25 ns / strict tolerances, both placements | FAIL | Both abort at 151 µs load onset in e.x354.ehelper#branch; candidate not promoted |

[Isolated refinement data](../simulations/clamp-scaled-refinement.json). These runs retain the extracted resistors, capacitors and semiconductor terminals. Only the named nonlinear MOS-capacitor's internal helper normalization changes; installed PDK files and chip GDS remain unchanged. The model candidate is limited to the tested equation/options and conditions.

## Final filled-chip extraction

Final-GDS extraction retains all 4,037 semiconductor records and the same ports as device LVS. The precise constant-capacitance reference reduces 358,494 floating nodes to 2,179 capacitor pairs on 279 retained nodes, passing recorded port-charge and quadratic-energy checks. It assumes zero initial floating charge and omits distributed wire resistance. Tiny negative extraction roundoff is bounded in the capacitance audit; this is not a manufacturing or full-chip electrical pass.

The saved LVS extraction is device-only. The fresh baseline explicitly adds lumped capacitance but omits distributed wire resistance. It must not be called the accepted post-fill RC model. [Exact target and remaining stages](../simulations/full-chip-qualification.json).

## What remains before complete-chip qualification

1. Resolve the reproducible clamp-helper failure at the 151 µs, 1 ns-rise load transition. Both strict corner runs fail; do not bypass this gate or run blind solver sweeps. Separate timestep and tolerance effects in a reviewer-agreed minimal reproducer before promoting the candidate.
2. Validate the complete pad-ring/device model and final-GDS capacitance/resistance extraction, including the known capacitance-export limitations and substrate interpretation.
3. Qualify complete-chip startup and three nine-pixel frames with refinement, then PVT and realistic external loading.
4. Validate ADS1115 slow acquisition separately from the earlier fast sample/hold fixture; photodiodes continue integrating during conversion.
5. Independently review the accepted model and archive the matching layout, netlists, stimuli and evidence.

[Full electrical plan](full-chip-electrical-plan.md). No ESD survival, fabricated-camera, QE or manufacturing-readiness claim follows from this numerical checkpoint.

## Evidence archive

[Final filled-chip capacitance evidence](../checkpoints/filled-electrical-baseline/evidence.tar.gz). [Refinement and corner evidence](../checkpoints/scaled-electrical-progress/evidence.tar.gz), with deck/model/waveform hashes in the result JSON files. Model dependencies remain the pinned PDK and the earlier reproducer. Nothing was posted or sent externally.
