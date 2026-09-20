# 3×3 demonstrator completion plan

## Matched simulator comparison — 2026-09-19 11:30 PDT

Built ngspice 46 and 47 with matching options in an isolated project folder. Both capacitor controls pass the independent current/charge checks. The unextracted stock corner fails at startup in 46 and fails parsing in 47. Both extracted stock-model cases fail at startup. A PDK-free reproducer isolates a separate v47 explicit-capacitor-multiplier parser failure (`m=1/8/70`); omitting the multiplier passes. **A simple upgrade does not resolve the qualification blocker.**

[Results and plot](docs/ngspice-version-comparison.md) · [Small public issue draft](docs/reviews/ngspice47-cap-multiplier-issue.md). Nothing has been posted and the working PDK/simulator/layout remain unchanged. The bounded comparison is complete; the earlier local helper candidate has not been promoted or rerun in this batch. Next: review the small parser failure separately from the extracted transient failure, then select a justified numerical-model correction and repeat accuracy/refinement gates before full-chip qualification. No new hardware or packaging decision is needed.


## Electrical checkpoint — 2026-09-19 10:02 PDT

**Complete-chip electrical qualification remains blocked by the clamp numerical model.** Both 50 ns corner runs complete, but both 25 ns/strict-tolerance runs abort at the 151 µs load transition in `e.x354.ehelper#branch`. No candidate is promoted; no full-chip startup/frame/PVT pass is claimed.

The final filled-chip lumped-capacitance extraction preserves all 4,037 semiconductor records. Its floating-fill reduction passes charge/energy checks and leaves 2,179 capacitors on 279 retained nodes. Distributed wire resistance remains unqualified. [Current results](docs/scaled-electrical-progress.md).

Next: use the saved failing deck to resolve the clamp-helper load-edge failure, then run the gated full-chip startup, repeated frames, refinement and PVT/load checks. `scripts/simulate-filled-chip-baseline.py` is prepared but has not been run; its prerequisites intentionally reject the current failed corner screen. No additional hardware or user decision is needed for this diagnostic work.


## Electrical qualification update — 2026-09-19 09:34 PDT

[New control-resolution and extracted-clamp results](docs/scaled-electrical-progress.md): matched capacitor controls pass the unchanged current limit; the isolated extracted clamp completes and passes 25 ns/tolerance voltage refinement. Both complete-corner capacitance placements now complete at 50 ns. These are diagnostic milestones, **not complete-chip qualification**. Final-GDS extraction and the [remaining electrical gates](docs/full-chip-electrical-plan.md) are open.


Updated **2026-09-19 03:15 PDT**. This document is the current plan; earlier diagnostic plans are [archived](docs/completion-plan-history-2026-09-19.md).

## Frozen first-release scope

- GF180 monochrome 3×3 array, existing 20 × 20 µm photodiode junctions and three-transistor pixels.
- Existing column bias, three-way multiplexer and shared analog output buffer.
- External controller supplies row, reset and column-select timing. External ADC; external bias resistors and reset-voltage source.
- Wire-bonded carrier with a confirmed optical path. Working pad positions are approved; final bond geometry and package remain open.
- No 64×64 expansion, on-chip ADC, new sequencer, or commercial image-quality promise in this release.

Scope is frozen; implementation changes needed to pass review are still allowed. A fabrication-ready package and a measured working camera are separate milestones.

## Current evidence and missing work

The [connected core](docs/integrated-layout.md) passed recorded DRC/LVS, and [earlier electrical tests](docs/integrated-corners.md) passed their stated PVT/sampling screens. This evidence is tied to those models and GDS hashes. The earlier [power-ring assembly](docs/power-ring.md) had power pads only. The [new routed working layout](docs/routed-demonstrator.md) now connects functional signals through local protection; diagnostic signal paths remain disconnected. The complete chip has not passed final electrical or manufacturing sign-off.

## Milestones with concrete exit conditions

| ID | Deliverable / exit condition | Dependency | Status |
|---|---|---|---|
| M0 | Scope, source-backed logical interface, current evidence and gaps in one place | None | Complete; working physical pad numbers assigned; final bond review open |
| M1 | Bounded solver comparison and reproducible expert-review package | Existing smaller clamp | Complete: both timed out at 120 s; local investigation stopped; see [review brief](docs/reviews/clamp-startup-review.md) |
| M2 | Agreed manufacturing/optical route, selected pad cells, physical pad map and bond diagram | Written run/package requirements | Working [24-pad map](docs/pad-proposal.md) approved by the user; provider/run and optical requirements remain open |
| M3 | Place and route all required signal pads, supplies, protection and core; regenerate whole-chip schematic | Working pad arrangement approved; manufacturing M2 remains open | Working routing and central fill complete; main DRC, density/antenna and unique device LVS pass. Final manufacturing qualification remains |
| M4 | Accepted extracted model and repeatable full-chip startup, three-frame scan and ADC-load tests | M1 resolution plus M3 | Blocked by modeling; earlier core results remain reference evidence |
| M5 | Final run-specific DRC/LVS, density, antenna, seal ring, die size/ID, optical keepouts and bond checks | M2–M4 | Working extent passes main DRC, density/antenna and device LVS; run-specific die/seal/ID/optical/bond/CUP checks remain open |
| M6 | Reviewed release archive: GDS, schematics, netlists, PDK/tool versions, pin map, test plan and residual limitations | M4–M5, independent review | Open; user approves any fabrication submission/purchase |
| M7 | Carrier/controller/ADC board and firmware, then measured nine-pixel dark/light response | Interface can start now; silicon for measurement | Open; no measured optical performance yet |

## Stop rule for simulator work

**2026-09-19 follow-up:** New native-point/terminal-ODE evidence justified the separately bounded control-resolution, scaled-clamp refinement and complete-corner placement batches. Their results are in [the electrical progress report](docs/scaled-electrical-progress.md). The two old solver-only failures below remain historical evidence. This does not authorize blind retries or promote the candidate to the final chip.

**Batch finished: both trials timed out; investigation stopped and the review package is prepared. No further solver variants are scheduled.**

The authorized batch was limited to the two solver-only comparisons defined in `scripts/check-bounded-solver.py`: existing 50 ns trapezoidal decks at normal and strict tolerances, replacing KLU with SPARSE. Preserve devices, R/C, waveforms and settings. Each trial has a 120-second watchdog. No retries, tolerance sweeps, capacitor replacement or resistor pruning are part of this batch.

If either trial fails or times out, stop local solver experimentation and prepare the evidence for ngspice/GF180 expert review. Do not resume parameter exploration without a specific new hypothesis from that review or new evidence. If both finish, compare their rail waveforms to the existing 10 µV screen; timestep verification is still required before promotion. Completion alone never qualifies the full corner.

The expert-review package is prepared locally. Sending it requires an explicit instruction to contact others. Independent board/interface/pad planning continues while M4 is blocked.

## Electrical acceptance retained from earlier tests

- Three frames, nine samples each, correct brightness ordering.
- ADC-input/HOLD tracking error <0.5 mV versus the matching DC transfer reference.
- Frame-two/three repeatability <50 µV; refinement agreement <10 µV at samples.
- Bias startup within 1% of settled values; evaluate realistic finite supply and selected ADC acquisition load.
- Repeat applicable process, supply and temperature conditions on the accepted assembled model; explain any coverage gaps.
- Preserve photodiode optical assumptions and extraction approximations explicitly. These are engineering screens, not measured camera specifications.

## Independent work to advance now

Use [the interface baseline](docs/demonstrator-interface.md) and working pad map to draft the controller/carrier schematic. Use [the manufacturing questions](docs/manufacturing-review.md) to resolve optical access and packaging before freezing the pad ring. Track requests requiring external confirmation separately from work blocked by simulation.

The next implementation milestone is **M4/M5: resolve the accepted electrical model and final manufacturing requirements**. The [filled working layout](docs/filled-demonstrator.md) has passed its scoped physical checks. Do not expand the sensor while these gates remain open. No completion date is promised until external review and manufacturing constraints are known.
