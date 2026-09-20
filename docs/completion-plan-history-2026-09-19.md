# Project completion plan

## Latest isolation result — 2026-09-19 01:49 PDT

24/24 simple capacitor transients complete; 0/4 initial isolated-clamp transients complete. Integration follow-up: 1/2 complete; refinement: 0/2 pass. [Evidence](docs/moscap-branch.md). Next: investigate solver conditioning and the behavioral-capacitor equations in this reproducer; the trapezoidal candidate failed refinement and is not accepted.

## Latest interface result — 2026-09-19 01:32 PDT

DC/AC interface comparison: NOT VERIFIED. Full-corner ramp/load transients: NOT VERIFIED. [Evidence](docs/corner-interface.md). Next: resolve full-corner startup before integrated 3×3 qualification.

Updated **2026-09-19 01:11 PDT**.

## First release scope

Confirmed by the user: finish a **3×3 monochrome demonstrator first**, using the existing array, readout and pad work. The 64×64 camera is a later expansion, not part of this first release. This plan does not authorize fabrication purchases or submission.

“Finished” has two separate milestones: a reproducible, reviewed design ready for fabrication, and a fabricated camera demonstrator verified on the bench. Simulation alone cannot establish optical response, yield or saleable sensor count.

## Gates to a fabrication-ready design

| Gate | Required evidence | Current position |
|---|---|---|
| 1. Reliable parasitic model | Original and R-collapsed capacitance matrices agree; passive RC; preserved devices and DC; explicit substrate model | Area-sign defect corrected in an isolated build. A separate reference model now preserves the original capacitance matrix and passes independent charge checks; native export is still incorrect. Spatial placement sensitivity and accepted reduced-RC models remain open. |
| 2. Close the integrated 3×3 electrical model | Accepted extracted array/readout/buffer/pads/bias/ring model; process, supply and temperature checks; repeatable sampling and realistic ADC acquisition load | Earlier block and system checkpoints exist. Repeat relevant checks after the accepted extraction model is fixed. |
| 3. Freeze first-chip interface and timing | Approved pad map, supply/ground strategy, reset/row/column controls, external ADC load and reference requirements, startup sequencing and frame timing | Existing pad and readout work is the starting point; final system requirements must be recorded. |
| 4. Close physical implementation | Final layout generated reproducibly; clean applicable full-chip DRC/LVS and density checks; connectivity, well ties, optical keepout and pad/bond geometry reviewed | Prior checks apply to their recorded geometry only. Recheck the final assembled design after changes. |
| 5. Confirm manufacturing and optical access | Confirm chosen run rules, acceptable detector geometry, exposed optical path, passivation/metal restrictions, die/wafer delivery and bondable packaging | Requires current run-specific confirmation. This plan does not assume a standard CMOS junction is an optically qualified photodiode. |
| 6. Release review | Versioned GDS, source/netlists, tool/PDK versions and hashes, reports, pinout, known limitations, independent review and user approval for submission | Open. Diagnostic Magic builds are not yet production tools. |

## Bench demonstrator

1. Build a board with the chosen external ADC, controller, low-noise supplies, references and appropriate signal buffering.
2. Package and wire-bond the die with optical access; verify continuity and safe power-up.
3. Measure dark current, reset behavior, signal versus exposure, pixel variation, crosstalk, noise, spectral response and usable dynamic range.
4. Capture a reproducible 3×3 monochrome image and publish hardware, firmware, calibration and measured limits.
5. Use measured results to set realistic specifications and the cost/yield model for a larger sensor or commercial launch.

## If the first release is 64×64

Add array scaling, row/column addressing, long-line parasitics and settling, power and data-rate budgets, full floorplanning/routing and a fresh complete verification cycle before gate 4. The existing 3×3 checks cannot qualify a 64×64 chip by repetition alone.

## Immediate next task

Test the voltage/current-preserving interface already used in the earlier clamp-convergence work around the corner macro, and verify its terminal equivalence. Resolve the MOS-capacitor startup abort before refining the full-corner load comparison and integrating the 3×3 model. The [reduction report](docs/charge-reduction.md) preserves all successful and failed checks and the placement approximation.

No additional host tools or new Python environment were needed for the current diagnostic work. The existing Docker environment provides the extractor, LVS, simulator and plotting tools.
