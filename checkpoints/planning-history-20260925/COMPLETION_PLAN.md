# 3×3 demonstrator completion plan

## Current: physical bank routing reinforced — 2026-09-25

**Both 64-column routing revisions and their small controls pass Magic/KLayout
main DRC and both LVS paths.** The selected bank adds supply straps, distributed
column feeds, reference feeds beside their devices and reinforced CBUF branches.
All 450 MOS devices, 512 MIM plates and 327 connected ports are preserved.

All 16 selected nominal/hot DC controls complete. Across 1.2–2.0 V, the worst
physical–ideal static buffer shift falls from **5.331 to 1.320 mV** (about 75%).
The supply/reference-only intermediate reaches 2.223 mV. At nominal 1.2 V,
spatial span falls from 4.688 to 1.519 mV. Some higher-input cases favor the
intermediate layout; these are DC comparisons, not matched output accuracy.
All 48 baseline/intermediate/selected records were independently read back and
ideal references reproduce exactly. Thirteen contraction controls identify
CBUF resistance as the main remaining common-offset contributor in the baseline.

The selected coupled reset test **times out during initialization at 180 s**,
with no complete transient records or readout samples. It does not establish
whether the later reset-edge slowdown is resolved. More routing increases the
extracted resistor count from 8,941 to 23,883; runtime remains a separate gate.

**Next:** address residual shared-supply/reference spatial shifts and coupled
solver initialization, then independent capture/output references, all 64
samples, nominal/hot timestep and shunt-placement comparisons. Route physical
row-to-bank joins before multirow/driver work. Full readout, startup, wire/process
corners and manufacturing qualification remain open.

Selected: `build/capture-bank-c64-v5-20260925`.
[Measurements, tradeoffs and reproduction](docs/bank-reinforcement.md) ·
`simulations/bank-reinforcement.json` · `checkpoints/bank-reinforcement/`.
No simulation remains running. Earlier checkpoints and uncommitted work are
preserved. No release GDS, carrier, commit or push changed.

## Earlier: shared-bank routing diagnosis — 2026-09-25

**Docker/WSL access is restored.** Eight direct-DC resistance-contraction controls
identify VDD and PREF routing as contributors to nominal equal-input spatial
spread. Ground/BIAS-only contractions have little effect. Idealizing supplies
and references together removes the spread but leaves a **2.199 mV common
buffer offset**. These are diagnostic models, not a new physical layout or an
accuracy pass. All 16 prior DC traces were read back; the repeated full-RC
control reproduces every saved voltage/current exactly.

The ideal-wire bank coupled to the extracted row crosses reset release and
reaches 0.25 ms in 107.8 s. The physical-bank Gear attempt times out during DC
initialization at 120 s with no complete transient records; it does not resolve
the earlier reset-edge slowdown. Neither test reaches capture/readout.

**Next:** revise VDD distribution and reference feed paths, then repeat physical
checks and extracted static comparisons. Investigate the remaining common offset
and coupled solver runtime; retain independent capture/output targets, all 64
samples, nominal/hot, timestep and placement checks before qualification.
Physical row-to-bank joins and multirow/driver work remain open.

[Routing diagnosis, controls and reproduction](docs/bank-routing.md) ·
`simulations/bank-routing.json` · `checkpoints/bank-routing/`.
No simulations remain running. Existing layouts, checkpoints and uncommitted
work are preserved. No release GDS, carrier, commit or push changed.


## Earlier: shared 64-column physical bank — 2026-09-25

**The bank passes Magic/KLayout main DRC and both LVS paths:** 450 MOS devices,
512 MIM plates and 327 distinct connected ports. Extraction retains 8,941
resistors and 7,005 parasitic capacitors. Five parallel 8 µm M5 straps per supply
replace a rejected unslotted wide-strap control. The extent is 5.198 × 0.86504 mm.

**Electrical qualification remains open.** All 16 isolated uniform-input DC
controls complete at 27/125 °C. Largest physical–ideal buffer shift is 5.331 mV
within 1.2–2.0 V (6.973 mV in the separate 0 V reset diagnostic); equal-input
spatial variation needs shared power/reference investigation. The coupled SPARSE run
initializes through transient-assisted fallback; bounded readout/runtime checks
are not an accuracy pass. The 600 s watchdog ends at 0.200255 ms
near reset release, before capture; no readout samples are obtained. Raw negative
shunts on 66 nets require a new near/far placement check.

**Next:** investigate shared power/reference routing and coupled solver runtime,
then independent capture targets, all 64 matched output references, nominal/hot
refinement and placement sensitivity. Physically route the row-to-bank joins
before repeated/multirow and driver qualification. Current block connections
are ideal terminal links; full-array, startup and manufacturing gates stay open.

Selected bank: `build/capture-bank-c64-v2-20260925`.
[Measurements, exact run status and reproduction](docs/capture-bank.md) ·
`simulations/capture-bank.json` · `checkpoints/capture-bank/`.
Earlier evidence and uncommitted work are preserved. No release GDS, carrier,
commit or push changed. No simulation remains running.

## Earlier: isolated physical column qualified — 2026-09-25

The [selected capture column](docs/capture-column-qualification.md) passes all
48 nominal/hot simulations, both main DRC checks and both LVS paths. Worst
tracking error is 176.560 µV; timestep difference is 0.318 µV. The documented
COL-shunt approximation has 0.0125 µV sampled placement sensitivity, and the
layout–schematic shift is at most 482.228 µV over the tested conditions.

Next implement the shared 64-column peripheral bank and qualify it with the
extracted row, then repeated/multirow operation and real drivers. Broader
corners, startup, noise, manufacturing option and frame rate remain open.

## Earlier physical work — 2026-09-25

The [isolated capture column](docs/physical-capture-column.md) passes both main
DRC and both LVS checks; extracted MIM capacitance/leakage controls pass at
27/125 °C. Transient accuracy/refinement and the COL-shunt approximation remain
unqualified. Close these before extending the physical peripheral bank. The
latest full-row electrical qualification remains the result below.

## Latest: full readout on the physical power grid — 2026-09-24

**All 64 outputs pass at both 27 °C and 125 °C on the extracted M5-grid row.** Worst total errors are **173.457/289.658 µV** against 500 µV; 200→100 ns output differences are **3.897/3.703 µV** against 10 µV. All four transients complete through 2.7 ms. Sampled controls, brightness ordering and reverse-biased capture diode states pass. Independent capture targets and selected first/last/worst output references agree within 10 nV when DC settling is doubled.

This closes the full serial-readout check left open by the earlier row power-grid investigation. The pixel/row model retains all 4,378 extracted resistors and 2,353 capacitors. Storage and readout periphery remain schematic; both device temperatures use nominal wire RC. This is a tested single row, not full 64×64 or tapeout qualification.

**Next:** follow the [physical capture/readout tile plan](docs/capture-tile-plan.md): implement and verify one column with actual storage capacitors, then the 64-column bank with extracted peripheral supplies, clocks and output routing. Follow with repeated/multirow operation and real drivers. Wire/process corners, full-chip startup, noise and manufacturing gates remain open. Frame rate remains undecided.

[Results and scope](docs/grid-readout.md) · `simulations/grid-readout.json`. Evidence: `checkpoints/grid-readout/`; earlier checkpoints are retained. No release GDS, carrier, commit or push changed in this stage.

## Earlier: physical row power-grid improvement — 2026-09-24

**The new extracted upper-metal grid reduces the nominal row-enable VDD loss from 354.350 to 42.574 mV (88%).** The 125 °C device-temperature run peaks at 34.516 mV. Both complete through capture, where local VDD loss is 4.091/4.093 mV instead of roughly 34.5 mV. Nominal 1→0.5 ns edge refinement changes per-pixel peaks by at most 0.000257 µV; the original-rail SPARSE/KLU control agrees within 3.013 µV.

The same pixel/capture circuit and timing are retained. The physical candidate uses 8 µm M5 VDD/ground straps and distributed 3×3 via arrays. Magic and KLayout main DRC report zero errors; direct and resistor-collapsed LVS match uniquely. No added metal overlaps the 64 drawn photodiode junctions. Maximum VDD/ground path resistance falls from 259.6/298.5 to 52.9/91.7 Ω.

Independent capture acquisition errors are 329.203/398.914 µV at the storage nodes; doubling DC-reference settling from 200 to 400 µs gives identical targets. **These are not final serial-output errors.** The new grid has not yet repeated the full 64-output 500 µV accuracy / 10 µV timestep gates. The earlier full-readout passes still apply to the earlier 2 µm-rail layout.

**Next:** run complete nominal/hot readout and refinement on `build/row-power-grid-20260924`, using SPARSE (the new mesh is slow with KLU), then matching capture/output references. After that, implement physical storage/peripheral supplies/clocks and test shared multirow routing. Wire-temperature/process corners, startup, full 64×64 and tapeout gates remain open. The present hot test keeps nominal extracted wire R+C. No release GDS, carrier, commit or push changed in this stage.

[Detailed measurements and exact scope](docs/row-power.md). Machine-readable results: `simulations/row-power.json`. Evidence checkpoint: `checkpoints/row-power/`; the earlier array-recovery checkpoint is unchanged.


## Earlier: full-row capture recovery — 2026-09-24

The revised **64-column simultaneous-capture readout passes** 64/64 matched samples at both 27 °C and 125 °C. Maximum total errors are **171.295/289.919 µV** against 500 µV; 200→100 ns differences are **4.317/4.439 µV** against 10 µV. All sampled control checks pass. The old exposure gradient and late bright-pixel saturation are absent in these captured-row tests.

The circuit uses 40 pF stores, 500 kΩ BIAS, 12.4 kΩ PREF, 10 µs acquisition and 20 µs slots. Pixels and row wiring are extracted R+C; storage capacitors and periphery remain schematic. The original serial row still misses numerical refinement (~11 µV); its old tracking results remain provisional.

Wider 2 µm rails pass DRC/both LVS and reduce the original circuit's peak row loss from 101 to 24 mV. **The new storage load needs a distributed power grid:** nominal row-enable loss peaks at 354 mV, settling to 34.5 mV at capture; modeled analog current averages 8.1 mA. The capacitor bank budgets roughly 1.3–2.6 mm² before layout overhead. A simple non-overlapped 64×64 schedule budgets ~10.5 frames/s; frame rate remains undecided.

**Next:** implement/extract a capture/readout tile with physical capacitors, distributed supplies and clock routing, then check repeated/multirow captures and broader corners. Full 64×64, nonlinear startup/protection, full-chip R+C and tapeout gates remain open. No release GDS or carrier revision was made. No simulation remains running.

[Measured results, rejected candidates and scope](docs/array-recovery.md) · [Tapeout readiness](docs/tapeout-readiness.md). Evidence: `simulations/array-recovery.json` and `checkpoints/array-recovery/`. No commit/push was performed for this stage.

## Earlier: extracted 64-pixel row and column tests — 2026-09-24

The confirmed next target is **64×64; frame rate remains undecided**. The 1×64 and 64×1 unfilled strips and their 1×3/3×1 controls pass DRC and both direct-device and resistor-collapsed LVS. Explicit extraction retains 3,829 wire resistors in the long row and 3,015 in the long column, plus coupling capacitance. Maximum row-select path resistance is 1,178 Ω; long-column path resistance is 754 Ω.

All 12 fixed-sense settling comparisons complete. Both long strips also complete **64 normal-integration samples each**. At 30 µs acquisition / 50 µs slots, worst matched DC tracking error is **189.827 µV** for the row and **226.992 µV** for the column. Sampled local VDD loss reaches **12.661 mV** and **0.384 mV**, respectively. Largest sample difference across timestep/placement checks is **20.350 µV**; all below 10 µV: **False**.

Full readout-waveform local VDD losses reach about **101 mV (row)** and **36 mV (column)** at switching events, larger than the sample-time drops above. These are nominal strip-fixture results; shared peripheral/driver supply routing is not included.

**Numerical qualification remains open for long-row imaging:** 200→100 ns changes samples by 17.054 µV; 100→50 ns changes them by 20.350 µV. Both exceed the retained 10 µV criterion. The row's imaging tracking numbers are provisional; the much larger exposure-skew finding persists.

**Exposure limitation:** the 64-column row keeps integrating during a 3.15 ms first-to-last readout span. Ten late 240 pA samples forward-bias their photodiodes; equally illuminated 80 pA pixels change from about 2.144 V to 1.664 V across the row. A readout-settling pass is not a usable uniform-exposure camera mode. Faster readout, a different exposure schedule, or capture/parallel-readout architecture is needed.

**Scope:** nominal unfilled strips with schematic readout, finite 100 Ω driver abstraction and 2 Ω supply impedance; no full-array peripheral routing, pads/clamps/fill or corner qualification. Column RC preserves all extracted resistance but explicitly consolidates small negative reset shunts; a second placement is checked during reset/integration. Some initial DC solves use transient-assisted fallback, so startup remains open. Actual ADC timing, full-chip R+C and tapeout gates remain open. No release GDS or carrier revision was made. No simulation remains running.

**Next:** resolve long-row imaging refinement and design the 64×64 exposure/addressing/readout architecture and choose its ADC/load and timing budget, then verify an intermediate tile with shared routing. Retain separate startup/full-chip RC and manufacturing release gates. The 50 µs diagnostic slot is not a chosen frame-rate specification.

[Results and plot](docs/array-strips.md) · [Tapeout readiness](docs/tapeout-readiness.md). Machine-readable evidence: `simulations/array-strips.json`; full read-back-verified checkpoint: `checkpoints/array-strips/`. Exact scripts and excluded fixture-development attempts are archived.

## Earlier: tested readout and cold-pad interface proposals — 2026-09-24

**The combined heavy-load proposal completes 27 samples over three frames:** maximum tracking error **461.383 µV**, frame-two/three drift **5.620 µV**, selected-screen pass **True**. First-frame 1 µs → 500 ns refinement changes samples by **0.278 µV**. The explicit condition is 470 pF board / 100 pF sampling load, 30 µs acquisition / 50 µs column slots, 12.4 kΩ external PREF resistor, and 100 kΩ pulldowns on P10/P11/P12/P15. Initial DC supply current is 248.259 µA (~0.819 mW), versus ~80.4 µA for the original interface.

**Both previously blocked cold conditions complete a first frame with explicit 100 kΩ unused-pad terminations.** The FF/−40 °C/3.6 V condition also completes 27 samples at the original load/timing/PREF setting: tracking **152.650 µV**, drift **5.336 µV**, timestep-refinement difference **0.300 µV**. The warm termination control differs from the original warm outputs by 0.228 µV. The old floating-pad cold failures remain preserved.

Slower timing alone passes the larger sampling capacitor but misses the heavy board/combined load screen (0.651/0.759 mV). Two intermediate PREF choices (24.9/16.5 kΩ) also miss it (0.578/0.503 mV); those failed candidates are retained. No screen threshold or solver accuracy tolerance was relaxed.

**These are conditional interface proposals, not an adopted carrier or die revision.** The existing carrier still has 49.9 kΩ at PREF/R2 and leaves the four pads unbonded. The high-load proposal was checked at nominal process/supply/temperature; it is not the complete combined-interface PVT matrix. Startup, full distributed wire R+C, actual ADC timing, run-specific physical signoff and optical/package/manufacturing confirmation remain open. No simulation remains running.

**Tapeout / scaling:** the 3×3 is a useful normal-operation simulation demonstrator, not tapeout-ready. A working small pixel array does not qualify arbitrary growth. At the current pitch, 64×64 budgets 5.12 × 3.20 mm for the array alone and direct controls would grow to 192 nets. Target-length row/column RC checks and scalable addressing/readout are needed before full-array implementation. The user has selected **64×64 as the next array target**; frame rate is undecided. Whether first silicon is the demonstrator or the larger camera remains open.

**Next:** choose the actual load/ADC and release target, review/adopt a corresponding interface implementation, then run its required combined corners and close startup/full-R+C gates. Next scaling tests: extract 1×64 and 64×1 structures with realistic drivers, readout and supplies; measure settling, droop and coupling to inform the frame-rate choice. Do not represent current tests as full tapeout qualification.

[Measured follow-up](docs/readout-followup.md) · [Concrete interface proposal](docs/readout-interface-proposal.md) · [Unused-pad connections](docs/unused-pad-termination-proposal.md) · [Tapeout readiness and scaling](docs/tapeout-readiness.md). Evidence: `checkpoints/readout-followup/`.

## Earlier: bounded load and operating-corner screen — 2026-09-24

**Five of the initial eight conditions pass the first-frame screen.** These are the 100 kΩ output load, 3.0 V and 3.6 V supplies, SS/125 °C/3.0 V, and FS/125 °C. Worst matched DC error among those passes is **207.923 µV**, below 500 µV. The hot-corner 1 µs → 500 ns refinement changes samples by **0.303 µV**, below 10 µV.

The **100 kΩ load completes 27 samples over three frames**: frame-two/three drift **5.550 µV**, tracking error **191.889 µV**, overall selected-screen pass **True**. This is selected loaded repeatability, not repeated-frame coverage of every operating corner.

**Capacitive-load limit found:** the 470 pF board / 100 pF sample load completes but misses the 5 µs acquisition accuracy requirement (348.813 mV worst error). Separate board-only and sample-only increases also fail (66.278 mV and 201.063 mV). Combined-load sample refinement agrees within 5.701 µV, supporting a settling limitation.

**Cold coverage remains open:** FF/−40 °C/3.6 V and SF/−40 °C time out at the stock nonlinear-capacitor DC solve, with a singular-matrix warning at unused pad NC_P10. They are not electrical passes or demonstrated hardware failures. Isolated pad controls reproduce the numerical warning; an added 1 TΩ path is diagnostic only and is not promoted into the camera model.

Each completed condition has newly computed corner/bias-specific frozen MOS capacitors, stock/frozen DC agreement, in-run capacitance bounds and matching DC references. No tolerances were relaxed. **Startup and full distributed resistance-plus-capacitance qualification remain open.** No simulation remains running.

**Next:** establish the actual external capacitive-load/readout-timing budget and validate a supported slower acquisition or output-drive change; resolve cold unused-pad DC conditioning before rerunning the cold camera cases. Then expand operating-corner combinations and repeated-frame/refinement coverage. Do not treat this bounded screen as full PVT or fabrication qualification.

[Detailed report and plots](docs/camera-operating-corners.md), `simulations/camera-operating-corners.json`, and verified evidence in `checkpoints/camera-operating-corners/`.

## Earlier: three-frame and nominal readout checks — 2026-09-24

**The full extracted 3×3 camera completes three consecutive frames: 27/27 samples.** Brightness ordering passes: True; control-state checks pass: True. Frame-two/three maximum change is **5.733 µV** against the retained **50 µV** screen (pass).

All 27 matching DC references were checked. Maximum HOLD tracking error is **167.766 µV**, and ADCIN error is **166.826 µV**, against the **500 µV** screen (pass). Sampled bias agreement within 1%: True.

The model is unchanged from the successful single-frame run; only stop time changed to 10.25 ms. It retains the equivalent reset source, all clamp domains, full-layout wiring capacitance and a 1 µs maximum step. Constant illumination was repeated. Reset voltages and capacitor bias ranges are recorded; this is not changing-scene, startup, optical/noise, full-RC or fabrication qualification.

**Next:** Run a bounded full-chip load/process/voltage/temperature matrix, revalidating the frozen-capacitor approximation at each operating condition. Nonlinear startup and distributed wire resistance remain separate gates. No simulation remains running.

[Report and waveforms](docs/three-frames.md), `simulations/three-frames.json`, and verified evidence in `checkpoints/three-frames/`.


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
