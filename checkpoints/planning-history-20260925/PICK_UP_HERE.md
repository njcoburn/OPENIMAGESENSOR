# Pick up here — 64×64 development

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

## Earlier: isolated physical capture column qualified — 2026-09-25

**The selected column passes all 48 nominal/hot transients and physical checks.**
Worst tracking error is **176.560 µV** against 500 µV; timestep difference is
**0.318 µV** against 10 µV; COL-shunt placement sensitivity is **0.0125 µV**.
Routing revisions reduce the largest layout–schematic shift from 2140.397 to
**482.228 µV**, passing the additional 500 µV comparison screen.

Independent single-model SPARSE simulations resolve the earlier transient
blocker without relaxing error tolerances. The selected layout uses 2 µm supply
rails, distributed vias and 0.6 µm buffer/output rails. Both main DRC checks and
both LVS paths pass; transistor/capacitor devices are unchanged. Raw negative
COL-shunt corrections and the tested placement approximation remain documented.

**Next:** implement the shared 64-column bank with physical supplies, clocks,
references and output bus; attach the extracted row and repeat all 64 output
checks. Then address repeated/multirow capture and real drivers. This qualification
uses an imposed column input/supply, typical devices and nominal wire RC.
Broader corners, startup, noise and manufacturing gates remain open; frame rate
remains undecided.

Selected layout: `build/capture-column-routed-v8-20260925/column.gds`.
Selected matrix: `build/capture-column-matrix-routed-v8-20260925`.
[Report and reproduction](docs/capture-column-qualification.md) ·
`simulations/capture-column-qualification.json` ·
`checkpoints/capture-column-qualification/`.
Earlier evidence and uncommitted work are preserved. No simulation remains
running. No release GDS, carrier, commit or push changed.

## Earlier: first physical capture column — 2026-09-25

**Docker/WSL access is restored.** The isolated seven-transistor/eight-MIM column
passes Magic and KLayout main DRC and both direct/resistor-collapsed LVS. Its
66.4 × 678.24 µm extent fits the column width before bank integration. Extracted
capacitor-device measurements match the model at 27/125 °C: 40.0075/40.0425 pF.
The 2 fF MIM option is a development candidate, not a manufacturing selection.

**Transient qualification remains open.** The nominal single-thread 100 ns
trapezoidal fixture aborts at 1.400010 ms; other bounded solver/refinement attempts
are incomplete. Raw extraction also needs a documented COL-shunt capacitance
placement approximation whose sensitivity is not yet qualified. Next isolate
the schematic/device/RC transient behavior and close matched-column accuracy and
refinement before building the full peripheral bank.

Accepted physical run: `build/capture-column-v2-20260925`; capacitor control:
`build/capture-capacitance-v3-20260925`. See the
[physical-column report](docs/physical-capture-column.md) and
`simulations/physical-capture-column.json`. Failed/development attempts and prior
checkpoints are preserved. No release layout, carrier, commit or push changed.
No simulation remains running. Read-back-verified evidence is archived under
`checkpoints/physical-capture-column/`; restore into an empty scratch directory.

## Earlier: capture-column preparation — 2026-09-24

Prepared the seven-transistor column and three conditional eight-plate MIM
storage banks. All 512 repeated transistor/capacitor elements match across the
64-column source fixture. Shared references and the external bias fixture are
separate subcircuits. The model arithmetic includes fringe and temperature
terms; plate dimensions target 40 pF at 25 °C. No manufacturing option is selected.

**Blocked physical work:** Docker reports WSL integration unavailable; Magic,
ngspice and Netgen are not available on the host PATH. No new DRC, LVS, extraction
or transient result is claimed. No simulation was launched. Restore Docker
Desktop/WSL integration, then implement and verify the first physical column
using [the tile plan](docs/capture-tile-plan.md). Keep separate bottom-metal
islands for the storage plates and join them through upper metal.

[Preparation and reproduction](docs/capture-column-preparation.md) ·
`checkpoints/capture-column-preparation/preparation.json` ·
`scripts/prepare-capture-column.py`. Previous evidence and uncommitted work are
preserved. The latest electrical qualification remains the grid-readout result
below; no commit or push was performed.

## Latest: full readout on the physical power grid — 2026-09-24

**All 64 outputs pass at both 27 °C and 125 °C on the extracted M5-grid row.** Worst total errors are **173.457/289.658 µV** against 500 µV; 200→100 ns output differences are **3.897/3.703 µV** against 10 µV. All four transients complete through 2.7 ms. Sampled controls, brightness ordering and reverse-biased capture diode states pass. Independent capture targets and selected first/last/worst output references agree within 10 nV when DC settling is doubled.

This closes the full serial-readout check left open by the earlier row power-grid investigation. The pixel/row model retains all 4,378 extracted resistors and 2,353 capacitors. Storage and readout periphery remain schematic; both device temperatures use nominal wire RC. This is a tested single row, not full 64×64 or tapeout qualification.

**Next:** follow the [physical capture/readout tile plan](docs/capture-tile-plan.md): implement and verify one column with actual storage capacitors, then the 64-column bank with extracted peripheral supplies, clocks and output routing. Follow with repeated/multirow operation and real drivers. Wire/process corners, full-chip startup, noise and manufacturing gates remain open. Frame rate remains undecided.

[Results and scope](docs/grid-readout.md) · `simulations/grid-readout.json`. Evidence: `checkpoints/grid-readout/`; earlier checkpoints are retained. No release GDS, carrier, commit or push changed in this stage.

No simulation remains running. Commands, runner snapshots, model/deck hashes, all four traces and both sets of 64 output references are retained under `build/grid-readout-20260924`. Restore the new checkpoint into an empty scratch directory if ignored build evidence is missing; preserve previous checkpoints and uncommitted work.

Accepted reference runs are `27-100-matched-parallel/r1c64-rc-port` and `125-100-matched/r1c64-rc-port` within that build root. The first nominal reference batch was deliberately stopped to increase worker concurrency; its supervisor error and partial evidence are retained. The manifest selects the completed replacement, which reused seven finished references only after exact deck checks. Reference settling is independently verified at 200/400 µs.

## Earlier: physical row power-grid improvement — 2026-09-24

**The new extracted upper-metal grid reduces the nominal row-enable VDD loss from 354.350 to 42.574 mV (88%).** The 125 °C device-temperature run peaks at 34.516 mV. Both complete through capture, where local VDD loss is 4.091/4.093 mV instead of roughly 34.5 mV. Nominal 1→0.5 ns edge refinement changes per-pixel peaks by at most 0.000257 µV; the original-rail SPARSE/KLU control agrees within 3.013 µV.

The same pixel/capture circuit and timing are retained. The physical candidate uses 8 µm M5 VDD/ground straps and distributed 3×3 via arrays. Magic and KLayout main DRC report zero errors; direct and resistor-collapsed LVS match uniquely. No added metal overlaps the 64 drawn photodiode junctions. Maximum VDD/ground path resistance falls from 259.6/298.5 to 52.9/91.7 Ω.

Independent capture acquisition errors are 329.203/398.914 µV at the storage nodes; doubling DC-reference settling from 200 to 400 µs gives identical targets. **These are not final serial-output errors.** The new grid has not yet repeated the full 64-output 500 µV accuracy / 10 µV timestep gates. The earlier full-readout passes still apply to the earlier 2 µm-rail layout.

**Next:** run complete nominal/hot readout and refinement on `build/row-power-grid-20260924`, using SPARSE (the new mesh is slow with KLU), then matching capture/output references. After that, implement physical storage/peripheral supplies/clocks and test shared multirow routing. Wire-temperature/process corners, startup, full 64×64 and tapeout gates remain open. The present hot test keeps nominal extracted wire R+C. No release GDS, carrier, commit or push changed in this stage.

[Detailed measurements and exact scope](docs/row-power.md). Machine-readable results: `simulations/row-power.json`. Evidence checkpoint: `checkpoints/row-power/`; the earlier array-recovery checkpoint is unchanged. No simulation remains running; both temporary watchdogs and their original supervisors have exited.


## Earlier: full-row capture recovery — 2026-09-24

The revised **64-column simultaneous-capture readout passes** 64/64 matched samples at both 27 °C and 125 °C. Maximum total errors are **171.295/289.919 µV** against 500 µV; 200→100 ns differences are **4.317/4.439 µV** against 10 µV. All sampled control checks pass. The old exposure gradient and late bright-pixel saturation are absent in these captured-row tests.

The circuit uses 40 pF stores, 500 kΩ BIAS, 12.4 kΩ PREF, 10 µs acquisition and 20 µs slots. Pixels and row wiring are extracted R+C; storage capacitors and periphery remain schematic. The original serial row still misses numerical refinement (~11 µV); its old tracking results remain provisional.

Wider 2 µm rails pass DRC/both LVS and reduce the original circuit's peak row loss from 101 to 24 mV. **The new storage load needs a distributed power grid:** nominal row-enable loss peaks at 354 mV, settling to 34.5 mV at capture; modeled analog current averages 8.1 mA. The capacitor bank budgets roughly 1.3–2.6 mm² before layout overhead. A simple non-overlapped 64×64 schedule budgets ~10.5 frames/s; frame rate remains undecided.

**Next:** implement/extract a capture/readout tile with physical capacitors, distributed supplies and clock routing, then check repeated/multirow captures and broader corners. Full 64×64, nonlinear startup/protection, full-chip R+C and tapeout gates remain open. No release GDS or carrier revision was made. No simulation remains running.

[Measured results, rejected candidates and scope](docs/array-recovery.md) · [Tapeout readiness](docs/tapeout-readiness.md). Evidence: `simulations/array-recovery.json` and `checkpoints/array-recovery/`. No commit/push was performed for this stage.

Read `docs/array-recovery.md` first. The selected primary results are `build/array-strip-capture40-klu-{27,125}-matched-20260924/r1c64-rc-port`; accepted nominal 200 ns refinement is the fresh `capture40-klu-27-200-long` run. All partial/aborted/time-limited and superseded attempts have retained evidence and are excluded. The optional SPARSE equivalent-network full transients were deliberately stopped; only the algebraic/serialized network audit is claimed. The nominal watchdog supervisor has exited and no process remains suspended. `python3 scripts/status-strip-runs.py` is a read-only progress/result helper. Restore the new checkpoint into an empty scratch directory if ignored build evidence is missing; preserve earlier checkpoints and existing uncommitted work.

# Earlier handoff — GF180 3×3 camera

Updated **2026-09-24 08:25 PDT** (America/Los_Angeles).

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


## Earlier: staged integration and full-frame success — 2026-09-21

**The full extracted 3×3 normal-operation candidate now completes a frame to 4.25 ms, with all nine pixels in the expected brightness order.** Only the 2 V / 1 Ω reset reference was rewritten as an electrically equivalent Norton source. The full chip model, all fifteen clamp domains, supply, control timing and tolerances are unchanged. The first six samples match the original failed trace within 0.060 µV. The 1 µs maximum-step rerun also completes all nine samples; maximum difference from 5 µs is 2.778 µV.

Staged shared-readout, buffer, ADC-load and finite-supply tests also pass on 3×3 and 4×4 array-core PEX models. The rail-diode control revealed a small numerical failure resolved by the same equivalent-source rewrite. The earlier stage-7 watchdog and other failed controls are retained.

**Next:** repeated full-chip frames and frame stability, matched DC transfer/settling reference, load/PVT checks, nonlinear startup and distributed wiring resistance. This is a first normal-operation imaging result, not fabrication qualification; MOS capacitors remain bias-frozen. No simulation remains running.

[Detailed report](docs/staged-integration.md), `simulations/staged-integration.json`, and verified evidence in `checkpoints/staged-integration/`.


## Earlier: physical array extension tests — 2026-09-20

**3×3, 4×3, 3×4 and 4×4 unfilled physical arrays all pass DRC/device LVS and complete three frames in both device-only and C-only PEX simulations.** Every sampled pixel has the expected brightness ordering. These use 100 Ω control drivers and independent column loads, without shared readout/pads/clamps/fill or distributed wiring resistance. An initial ideal-driver C-only 3×3 failure is retained separately. The original full-chip failure is unresolved; no simulation remains running.

[Results and exact scope](docs/array-extension.md), `simulations/array-extension.json`, and `checkpoints/array-extension/`. Next: integrate the shared readout into this parameterized, working array baseline, then restore supply/pad/clamp blocks in stages. Do not treat these core passes as complete-camera qualification.


## Earlier: shared-circuit and source-equation investigation — 2026-09-20

**Original third-row failure remains unresolved. No simulation is running.**

The restored three-row camera/readout with the original 2 Ω supply completes to 3.28 ms with zero or one clamp timing domain. Seven domains reach 3.23002000688 ms before a 300 s watchdog; this is not an explicit abort. Restoring all fifteen domains reconstructs the original model byte for byte.

A **different, early ideal-supply failure** at 1.220000078 ms reproduces with no clamp domains in 0.87 s. Changing only the reset reference from its 2 V + 1 Ω source/resistor pair to the identical terminal-current equation lets that 317-record control finish in 0.62 s. The same change completes the all-domain ideal-supply control. This demonstrates numerical representation sensitivity in the short control, not the cause or resolution of the original third-row event.

A separate full-model/original-supply test with the nine control drivers in equivalent Norton form reaches 3.19800404613 ms, then times out at 300 s. Four retained samples agree within 0.151 µV, but it never reaches the target failure; no fix is promoted.

Read [the shared-circuit report](docs/shared-circuit.md) and `simulations/shared-circuit.json`. Exact decks/traces/substitutions are in `build/shared-circuit/`, preserved in `checkpoints/shared-circuit/evidence.tar.gz.part-*`. The archived local ngspice 46 build exactly reproduces the all-domain ideal-supply failure and is available for matched diagnostic instrumentation. Docker remains running.

## Earlier: standalone row investigation — 2026-09-20

The internal-capture rerun reproduced the original full-chip abort exactly: 17,764 points and all 56 shared vectors match, with 52 added internal vectors. Failure remains at 3.270020000138615 ms; 1,217.47 s runtime, no timeout.

**All three rows have identical local device/resistor records after renaming (34 per row).** Wiring capacitances and illumination differ. The captured reset sense voltages/currents have no obvious large excursion, but the third-row trace ends before settling.

**All 12 standalone reset tests complete**, including three rows with devices, added capacitance, added input-pad protection, and third-row finer-step/finite-supply controls. Maximum isolated sense checkpoint difference at 5 µs versus 100 ns steps is below 0.06 µV. These controls hold shared columns/reference at DC and AC-ground remote coupling plates; the finite-supply test restores only the original 3.3 V/2 Ω source. They do not reproduce shared-chip feedback or qualify a frame. No causal device or fix is established.

Read [the step-by-step report](docs/standalone-row.md). Evidence and reproducible helpers are in `checkpoints/standalone-row/evidence.tar.gz` and its manifest; all outputs remain under `build/standalone-row/`. No simulation remains running. Docker container `openimagesensor-vnc` is running.

## Where we stopped

Finish the **nine-pixel monochrome demonstrator first**, then consider 64×64. The filled chip layout and prototype test boards exist. **The final assembled chip is not electrically qualified or ready for fabrication.** Earlier core simulations must not be presented as full-chip passes.

| Area | Current evidence | Remaining work |
|---|---|---|
| Filled chip layout | Main DRC (excluding CUP), density/antenna, device LVS and 4,566 connectivity checks pass within documented scope | Run/package-specific signoff and manufacturing review |
| Final extracted capacitance | 4,037 semiconductor records retained; floating-fill reduction checked for charge/energy; 2,179 capacitors on 279 retained nodes | Distributed wiring resistance remains unqualified |
| Stock final-chip DC | Passes with unused-pad `.nodeset` initial guesses; supply 3.299839 V, current 80.401 µA | DC alone does not establish imaging or startup |
| Normal-operation transient candidate | Replaces only 1,680 MOS capacitors with their capacitance at measured settled bias | Three frames complete; frame 2→3 change 5.733 µV; matched DC readout references checked. Bias range checked over three frames |
| Pad protection/startup | Isolated controls and some candidates pass; strict corner refinement fails | Resolve nonlinear clamp model separately; no accepted startup/ESD qualification |
| KiCad fixture | 40 × 40 mm removable carrier and tester; saved native DRC/pin-net checks pass | ERC, analog behavior, mechanical/bonding review and ADC timing |

Earlier full-frame attempts were **manually stopped**, not reported as successful runs:

- `frame-100ns`: projected runtime exceeded the watchdog; no frame result.
- `frame-5000ns`: persistent time stagnation near **3.23002 ms**, second-row turn-off.
- `frame-5000ns-gear`: persistent time stagnation near **3.17001 ms**, second-row select rise.
- These are zero-based row 1 in the scripts. Earlier failed OP attempts include testbench setup errors; the final `op-100ns` stock-model DC result passes.

## Latest switching diagnostic

The unchanged KLU/trapezoidal candidate **crosses the reported row-switching stall and completes to 3.24 ms** in 1,166.94 seconds. This is a two-row diagnostic, not a complete frame. Its first 14,326 saved points exactly reproduce the shorter attempt. The solver takes extremely small steps around row turn-off; six-digit progress messages conceal accepted subnanosecond movement. Do not diagnose a permanent stall from repeated rounded log messages alone.

Streaming capture now retains controls, supply/output, clamp timing nodes, pixel voltages and sampling-switch currents even after a watchdog stop. The six captured samples have the expected brightness ordering. All 16 MOS-cap terminal pairs remain within the C(V) approximation screen over this interval. Neither result substitutes for the missing third row or a DC transfer reference.

The matched 100 ns row-edge control moves the slow region to the correspondingly shifted falling-edge endpoint (3.23020 ms) and times out after 1,200 seconds. No timing change is promoted. See [the full diagnostic report](docs/functional-camera-diagnostic.md) for final run classifications, plots and setup failures.

## Latest full-frame attempt

`nominal-frame-stream` crossed the earlier slowdown, then **aborted at 3.270020000138615 ms** after 1,263.39 s (17,764 accepted points). It did not hit the 3,600 s watchdog. ngspice reports “Timestep too small”, requesting 6.25e-18 s and naming `bdrive_row1#branch`. The endpoint coincides with the third-row reset falling edge (`Vr2`); row-1 select is already low. This does not prove which device causes the failure. Six samples are retained; the third row is missing. [Results and plots](docs/streamed-frame.md).

Three captured-state static-reference method probes from the completed two-row diagnostic converge; their largest held-minus-reference error is 0.167640 mV, below the 0.5 mV nominal screen. These probes do not establish nine-pixel accuracy. Reference/analyzer helpers are prepared, and the full-frame analyzer rejects incomplete input.

## First task when returning

**Instrument the fast matched numerical failure/control pair before another long full-chip attempt.**

1. Read `docs/shared-circuit.md`. The sub-second pair is `no-clamps-ideal-short-20260920` (abort) versus `no-clamps-ideal-norton-reset-20260920` (complete), under `build/shared-circuit/`. Their reset-reference terminal law is identical. Their ideal supply is deliberately different from the original circuit; do not conflate the two failure events.
2. Use an isolated instrumented ngspice build to record Newton residuals, rejection reason and device convergence near 1.22 ms. Keep installed tools and original source builds unchanged; establish matched unmodified/instrumented behavior before interpreting logging. Local ngspice 46 source and an unmodified binary remain under `build/ngspice-version-comparison/`.
3. Explain/minimize this numerical sensitivity, then test the supported change on the original finite-supply full-chip third-row event. Preserve time-zero history, timing/tolerances and baseline evidence. No source rewrite is an accepted camera fix yet.
4. Once a full transient completes through 4.25 ms, check all nine captured states against matched references, numerical refinement, repeated frames and PVT/load. Startup/protection, distributed wire-R, ADC-specific, board and manufacturing gates remain separate.

The generic sample/hold fixture is not an ADS1115 model. No new hardware decision is required for the next diagnostic.

## Find the important files

- `checkpoints/streamed-frame/evidence.tar.gz`: failed full-frame attempt, raw trace, failure plots, static-reference method probes and reproduction helpers; see its README and manifest.
- [Team overview](docs/overview.html), [changelog](CHANGELOG.md), [dated next-step history](NEXT_STEPS.md).
- [Functional candidate](docs/functional-camera.md), [full electrical plan](docs/full-chip-electrical-plan.md), [filled chip](docs/filled-demonstrator.md).
- [wafer.space version audit](docs/wafer-space-version-audit.md): inspected PDK model files match; a version upgrade alone is not the fix.
- [Matched ngspice 46/47 comparison](docs/ngspice-version-comparison.md): both stock extracted tests fail; a separate v47 multiplier parsing issue has a [public issue draft](docs/reviews/ngspice47-cap-multiplier-issue.md). Nothing has been posted.
- [Tiny Tapeout / wafer.space / JKU references](docs/gf180-shuttle-references.md): useful pad precedents, not proof that our analog transient passes.
- [KiCad projects and Windows instructions](hardware/carrier/README.md), [carrier fixture HTML](docs/carrier-fixture.html).
- `scripts/prepare-functional-pad-model.py`, `freeze-functional-pad-model.py`, `simulate-functional-camera.py`, `analyze-functional-camera.py`, `report-functional-camera.py`.
- `checkpoints/functional-camera-diagnostic/evidence.tar.gz` and `manifest.json`: streamed raw traces, exact models/decks, setup/watchdog failures, matched slew control, plots and analysis. Restore to an empty scratch directory; see its README.
- `checkpoints/functional-camera/evidence.tar.gz` and `manifest.json`: stock OP, failed attempts, exact decks/models, logs, reversible node aliases and capacitor provenance. No completed frame waveform exists.
- `checkpoints/filled-electrical-baseline/evidence.tar.gz`: condensed source model and extraction/reduction audits.

## Resume in the existing checkout

```sh
cd /home/njcoburn/code/OPENIMAGESENSOR
git status --short
bash scripts/start-vnc.sh
# If the existing container is stopped:
# docker start openimagesensor-vnc
```

Open <http://localhost:8080/vnc.html?autoconnect=true&resize=scale> and `docs/overview.html`. Docker Desktop must be running. The checkout is mounted at `/foss/designs`; files saved there live in the host repo. Container-local installations and desktop session state are not Git checkpoints.

The pinned OSIC image is recorded in `scripts/run-tools.sh` and `scripts/start-vnc.sh` (digest ending `...be143537a`). The working toolchain uses ngspice 46 and GF180MCU D. Isolated ngspice 46/47 comparison builds do not replace the working simulator. See [Docker setup](docs/docker-setup.md). Windows KiCad 7 or newer opens the projects directly; preserve their local footprint libraries.

## Restore evidence after a fresh clone

The `build/` folder is intentionally ignored. Restore to an **empty scratch directory**, never over the existing checkout:

```sh
mkdir -p /tmp/ois-resume-20260919/baseline /tmp/ois-resume-20260919/functional
tar -xzf checkpoints/filled-electrical-baseline/evidence.tar.gz -C /tmp/ois-resume-20260919/baseline
tar -xzf checkpoints/functional-camera/evidence.tar.gz -C /tmp/ois-resume-20260919/functional
```

The baseline archive has a `filled-electrical-baseline/` prefix; the functional archive uses repository-relative `build/`, `scripts/`, `docs/` and `simulations/` paths. Inspect these and verify the manifests before selectively restoring missing `build/` artifacts. The tracked `checkpoints/clamp-review/package/init/.spiceinit` supplies the simulation compatibility settings. The final pixel map is tracked in `simulations/final-chip-pixel-map.json`.

The runners refuse to overwrite an existing `result.json`. Preserve archived results and use distinct diagnostic run names/directories. Only run `analyze-functional-camera.py` after a transient reports `completed: true`; it deliberately rejects these incomplete runs. Do not regenerate KiCad boards over manual edits.

## Suggested instruction for the next session

> Read PICK_UP_HERE.md, docs/readout-followup.md and docs/tapeout-readiness.md. Conditional timing/bias and unused-pad termination proposals have completed selected frames and refinement. Preserve their scope: the existing carrier has not adopted them, and combined PVT, startup/full-R+C, real ADC and release gates remain open. Establish the target size/frame rate and actual load before selecting interface hardware and target-length scaling tests.
