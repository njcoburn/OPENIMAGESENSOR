# Next steps — 3×3 demonstrator

## Latest: three-frame and nominal readout checks — 2026-09-24

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


## Shared-circuit numerical investigation — 2026-09-20

Shared camera/readout tests cross the third-row reset with zero or one supply-clamp domain; seven domains time out near the earlier row turn-off. A separate ideal-supply failure now reproduces in under a second and disappears when only the reset reference is expressed with the same terminal-current equation. This is numerical sensitivity in a different early control, not a resolved original third-row failure. The full-model nine-driver rewrite also times out before the target event. [All ten outcomes and scope](docs/shared-circuit.md).

Next: instrument the fast failed/completed pair, then test a supported change on the original finite-supply circuit. Exact evidence is archived in `checkpoints/shared-circuit/`; no simulation remains running.

## Standalone row investigation — 2026-09-20

All three extracted rows have identical local device/resistor records after renaming. All 12 isolated reset tests complete with staged capacitance/pad protection, third-row finite-supply and finer-step controls. The full-chip internal capture reproduces the earlier failure exactly; no causal device or fix is established. Shared circuitry and charge history remain outside the standalone checks. [Step-by-step results](docs/standalone-row.md).

Next: restore shared column/readout and supply/clamp circuitry in stages to minimize the failure. Exact inputs/results and the internal full-chip trace are archived in `checkpoints/standalone-row/`. No simulation remains running.

**Resume here:** [Project handoff — 2026-09-20](PICK_UP_HERE.md). Stock final-chip DC passes; complete-frame simulation and fabrication qualification remain open.

## Streamed nine-pixel attempt — 2026-09-20

The unchanged frame attempt crosses the earlier slowdown but aborts at **3.27002 ms** after 21.06 minutes, before third-row readout. Six samples and 17,764 points are preserved. This is an explicit timestep failure, not a watchdog stop. The failure coincides with the third-row reset fall; ngspice names `bdrive_row1#branch`, which does not by itself establish the cause. [Results](docs/streamed-frame.md).

Next: internal gate/device capture around this transition and one justified correction, then a completed nine-pixel transient, matched references and refinement. Three preliminary static-reference probes pass the 0.5 mV screen; no full-frame pass is claimed. Updated the overview and archived the exact evidence.

## Row-switching capture — 2026-09-20

The unchanged candidate completes a 3.24 ms streamed diagnostic in 1,166.94 s, crossing the previously reported row-turn-off stall. Six samples and the captured MOS-cap ranges are checked; no complete frame exists. The matched row-slew control shifts the slow region with the falling-edge endpoint; no timing change is promoted. [Results](docs/functional-camera-diagnostic.md).

Next: one unchanged nominal frame through 4.25 ms with streaming output, original bias/history and an explicit 3,600 s watchdog. Then check nine samples, matched DC settling and numerical refinement before repeated frames or PVT. See the handoff for commands and checkpoint restoration.


## Normal-operation candidate — 2026-09-19 13:46 PDT

Nominal frame attempt did not complete; qualification remains open. Stock-model DC bias passes with unused-pad initial guesses. See [results and exact next checks](docs/functional-camera.md). No hardware decision is needed for the next simulation checks.


## Shuttle-reference review — 2026-09-19 13:02 PDT

Tiny Tapeout uses the same foundry pad families; JKU reports working silicon and its historical supply-pad netlists match ours after naming normalization. No exact clamp-transient fix found. Recommendation: define a validated normal-operation pad interface model for camera functional tests, while retaining separate protection/startup requirements. No acceptance gates changed. [Details](docs/gf180-shuttle-references.md).

## Matched simulator comparison — 2026-09-19 11:30 PDT

Built ngspice 46 and 47 with matching options in an isolated project folder. Both capacitor controls pass the independent current/charge checks. The unextracted stock corner fails at startup in 46 and fails parsing in 47. Both extracted stock-model cases fail at startup. A PDK-free reproducer isolates a separate v47 explicit-capacitor-multiplier parser failure (`m=1/8/70`); omitting the multiplier passes. **A simple upgrade does not resolve the qualification blocker.**

[Results and plot](docs/ngspice-version-comparison.md) · [Small public issue draft](docs/reviews/ngspice47-cap-multiplier-issue.md). Nothing has been posted and the working PDK/simulator/layout remain unchanged. The bounded comparison is complete; the earlier local helper candidate has not been promoted or rerun in this batch. Next: review the small parser failure separately from the extracted transient failure, then select a justified numerical-model correction and repeat accuracy/refinement gates before full-chip qualification. No new hardware or packaging decision is needed.


## wafer.space setup audit — 2026-09-19 11:09 PDT

The correct process and supported pad library are installed. Newer template model files and pad geometry match ours; version mismatch alone does not explain convergence. Next: controlled stock-model/simulator comparison before redesigning pads. [Exact comparison and scope](docs/wafer-space-version-audit.md).

## Electrical checkpoint — 2026-09-19 10:02 PDT

**Complete-chip electrical qualification remains blocked by the clamp numerical model.** Both 50 ns corner runs complete, but both 25 ns/strict-tolerance runs abort at the 151 µs load transition in `e.x354.ehelper#branch`. No candidate is promoted; no full-chip startup/frame/PVT pass is claimed.

The final filled-chip lumped-capacitance extraction preserves all 4,037 semiconductor records. Its floating-fill reduction passes charge/energy checks and leaves 2,179 capacitors on 279 retained nodes. Distributed wire resistance remains unqualified. [Current results](docs/scaled-electrical-progress.md).

Next: use the saved failing deck to resolve the clamp-helper load-edge failure, then run the gated full-chip startup, repeated frames, refinement and PVT/load checks. `scripts/simulate-filled-chip-baseline.py` is prepared but has not been run; its prerequisites intentionally reject the current failed corner screen. No additional hardware or user decision is needed for this diagnostic work.


## Electrical qualification update — 2026-09-19 09:34 PDT

[New control-resolution and extracted-clamp results](docs/scaled-electrical-progress.md): matched capacitor controls pass the unchanged current limit; the isolated extracted clamp completes and passes 25 ns/tolerance voltage refinement. Both complete-corner capacitance placements now complete at 50 ns. These are diagnostic milestones, **not complete-chip qualification**. Final-GDS extraction and the [remaining electrical gates](docs/full-chip-electrical-plan.md) are open.

## KiCad fixture checkpoint — 2026-09-19 08:30 PDT

Two editable projects are ready for review: [tester dock and 40 × 40 mm carrier](hardware/carrier/README.md). Native KiCad DRC: zero violations and zero unconnected pads on each; exported schematic pin/net assignments match (186 dock, 44 carrier). No schematic ERC or electrical simulation of the board has been completed.

1. Open both projects in Windows KiCad and run schematic ERC; review pin types, power sources, analog topology and footprint orientation.
2. Review ground return paths/planes, bypass-loop placement and 3D screw/contact clearances. Verify OPA2320 stability and startup, including VRESET tracking and controller back-power paths.
3. Validate a slow ADS1115 single-pixel acquisition sequence. Its millisecond conversion does not match the existing column timing; retain the faster-ADC expansion option.
4. Confirm the selected spring-contact drawing, compressed height and rigid spacer stack. Obtain provider approval of bond fingers, metallization, die attach and loop height before ordering.
5. Select a controller and test the populated dock with a voltage source before attaching a bonded die. Continue the separate external clamp-model review.

The 40 × 40 mm carrier size is accepted. No further user information is required for the current checkpoint; bonding and controller choices are still pending. [Review package](hardware/carrier/openimagesensor-kicad-review.zip).

**Path to a working camera — 19 September 2026:** [Finish the 3×3, characterize the photodiodes, then scale to 64×64](docs/path-to-camera.md). Carrier/interface and manufacturing planning can proceed alongside the clamp-model review.

## Clamp-model local review — 19 September 2026

Audited ngspice’s expanded MOS-capacitor model and tested one algebraically equivalent internal scaling. Both standalone traces complete, but the current comparison fails (2.71 nA versus 0.1 nA); no clamp trial or fix accepted. [Results and specific reviewer questions](docs/clamp-model-review.md). External review has not occurred; further sweeps remain stopped.

## Filled working demonstrator — 2026-09-19 03:15 PDT

Regenerated central fill with all nine optical keepouts preserved. Density/antenna and main KLayout DRC report zero violations; device LVS matches uniquely; all 4,566 connectivity checks pass. [Evidence and reproduction](docs/filled-demonstrator.md). Next: resolve the clamp-model review, qualify post-fill electrical behavior, and confirm run/bonding requirements. The local simulator stop rule remains active; this is not a fabrication release.

## Routed working demonstrator — 2026-09-19 02:57 PDT

13 functional signal paths routed through local protection; seven supply/return pads connected. Metal connectivity: 4566 checks, PASS. Main KLayout DRC: 0 markers. Magic DRC: 0. Device LVS unique match: True. Four diagnostic signal paths remain disconnected; fill and final sign-off are open. [Evidence](docs/routed-demonstrator.md). Next: close physical findings and regenerate/verify fill; retain the stop on simulator parameter experiments.

## Pad-placement proposal — 2026-09-19 02:12 PDT

Created a 24-pad custom-carrier proposal, coordinate CSV, labeled diagram and separate unrouted GDS. All 19 core ports are represented. Packaging, diagnostic loading and protection choices remain open; no routing or sign-off claimed. [Review](docs/pad-proposal.md). Historical next action: pad-map review. The user subsequently approved local routing; see the newer routed checkpoint above.

Updated **2026-09-19 01:59 PDT**.

Start with [COMPLETION_PLAN.md](COMPLETION_PLAN.md), the current source of milestones and stopping rules.

1. Read the final bounded-solver result and [expert-review brief](docs/reviews/clamp-startup-review.md). Do not start another parameter sweep after this batch stops.
2. Resolve [manufacturing/optical questions](docs/manufacturing-review.md); use the [19-port logical interface](docs/demonstrator-interface.md) to draft the physical pad map.
3. Implement signal pads and routing after the macro/package choices are reviewed. The current ring has power pads only.
4. Resume full-chip electrical and physical sign-off only with an accepted model and assembled interface.

Historical handoffs follow; their “next” instructions are superseded by the plan above.

---

# Next steps — resume the GF180 image sensor

## MOS-capacitor isolation handoff — 2026-09-19 01:49 PDT

24/24 simple capacitor transients complete; 0/4 initial isolated-clamp transients complete. Integration follow-up: 1/2 complete; refinement: 0/2 pass. [Evidence](docs/moscap-branch.md). Next: investigate solver conditioning and the behavioral-capacitor equations in this reproducer; the trapezoidal candidate failed refinement and is not accepted.

## Corner-interface handoff — 2026-09-19 01:32 PDT

DC/AC interface comparison: NOT VERIFIED. Full-corner ramp/load transients: NOT VERIFIED. [Evidence](docs/corner-interface.md). Next: resolve full-corner startup before integrated 3×3 qualification.

**Handoff recorded: 2026-09-16 13:11 PDT (America/Los_Angeles, UTC−07:00)**

**UTC: 2026-09-16 20:11**

## Reduced-RC handoff — 2026-09-19 01:11 PDT

Four reductions pass current/energy and 16 DC checks; six short placement transients plus six refinements complete. Full-corner DC-start transient fails in a nonlinear MOS-capacitor model. Supply-ramp completion: False. Next: Test the voltage/current-preserving interface already used in the earlier clamp-convergence work around the corner macro, and verify its terminal equivalence. Resolve the MOS-capacitor startup abort before refining the full-corner load comparison and integrating the 3×3 model. [Detailed result](docs/charge-reduction.md).

## Charge-reference handoff — 2026-09-19 00:42 PDT

User confirmed **3×3 demonstrator first**. Generated 8 reference models: unchanged R/devices, original capacitance-pair matrix preserved, and 16 ngspice charge checks pass. Native export remains unaccepted. Next: quantify lumped-capacitor anchor sensitivity, validate reduction of resistor-only nodes, then run corner/integrated 3×3 and ADC-load transients. [Report](docs/charge-reference.md) · [Completion plan](COMPLETION_PLAN.md).

## Capacitance handoff — 2026-09-19 00:28 PDT

Isolated area-sign patch removes all negative C entries from four coupons; 2 LVS and 16 DC checks pass. Internal partition sums match incident coupling within 59.79 ppm. Exported charge still fails: coupling is retained and also added as substrate shunts. Next: fix that accounting and compare original versus R-collapsed capacitance matrices before any camera requalification. [Report](docs/capacitance-candidate.md) · [Completion plan](COMPLETION_PLAN.md).

## Ring-section handoff — 2026-09-18 23:55 PDT

Completed matched filler/corner extraction, 4 LVS checks and 32 DC solves. Corner capacitance still has explicit negative-energy witnesses; do not run camera qualification with this model. Next: trace signed capacitance redistribution from `.ext` through `.res.ext`, check total charge conservation, and make a minimal regression before any repair or transient use. [Evidence](docs/ring-candidate.md).

## Combined candidate handoff — 2026-09-18 14:06 PDT

Completed fresh buffer/readout extraction with both patches; 4/4 LVS and 80/80 short corner transients pass. Next: extract a representative ring section with this candidate, audit substrate connections and negative capacitances, then validate DC and reduced RC behavior. Do not yet replace installed Magic or production netlists. [Evidence](docs/combined-patch.md).

## Latest continuation update — 2026-09-18 13:17 PDT

Confirmed the two-layer discrepancy in construction-time triangle-to-star reduction: six half-milliohm additions change the DC result. A separate candidate removing them matches the unreduced graph within 2e-6 relative on 20- and 300-via controls. Six raw graph solves pass independent ngspice checks. [Evidence](docs/network-investigation.md).

The reader patch preserves all device, capacitor and hierarchy records after applying the PDK startup grid (`scalegrid 1 10`). Four nominal buffer/hierarchy transients pass with the previously audited charge-neutral fill reduction; maximum output change is about 0.05 µV. All four direct fill-heavy RC attempts timed out at 90 seconds and are retained as non-passes.

**Next:** combine the reader and triangle corrections in an isolated build, re-extract representative device-aware blocks, and repeat topology/LVS and process/temperature/transient checks before any tool adoption. The two candidates were tested separately, not as a combined production tool. Then resume ring RC with substrate-coupling and negative-capacitance gates. Installed tools and production netlists are unchanged; no upstream issue/PR was submitted.

## Earlier continuation update — 2026-09-18 12:28 PDT

The Magic 8.3.664 resistor reader adds 0.5 milliohm to each parsed resistor. A one-line isolated patch removes it across all five rail stacks; a matched unmodified build reproduces installed exports. Both builds' exports pass ngspice. The full stack is 0.0891035 Ω raw/patched versus 0.0990837 Ω original. [Patch, source and reproducible evidence](docs/extraction-diagnostics.md).

The two-layer issue is separate and remains open: adding vias from 20 to 300 with unchanged metal raises raw Magic resistance from 0.106148 to 0.118443 Ω, while the spatial model falls from 0.105155 to 0.093853 Ω. No extraction workaround is validated.

**Next:** inspect the two-layer contact/tile network before reduction and make a minimal source-level regression. Broaden the reader patch to device-aware hierarchical RC tests before adopting it. Installed tools and production netlists are unchanged. The ignored build directory contains both diagnostic executables; the checkpoint records source commit, patch, binary hashes, inputs and results. No upstream issue or PR has been sent.

## Earlier continuation update — 2026-09-18 11:09 PDT

Full-width M5 electrode faces give 0.1142857 Ω, matching the analytic 20 × 7 µm strip and raw Magic extraction. The narrow-probe discrepancy is removed for this controlled M5 measurement. For three or more layers, raw Magic and the fine spatial model agree within 0.013%. Each exported resistor gains about 0.0005 Ω, adding approximately 11.2% to the rail-face equivalent resistance. All five exports pass independent ngspice solves, confirming their numerical behavior. [Results and commands](docs/rail-faces.md).

**Next:** isolate the two-layer Magic anomaly (M4 addition increases extracted resistance) and inspect the raw-to-SPICE resistor conversion. Establish a validated layered DC reference before device-aware RC and full-ring transient work. Keep probe-access resistance separate from the intrinsic rail; the measured configuration difference is not a universal correction. Existing Docker tools suffice for these diagnostics.

## Earlier continuation update — 2026-09-18 08:30 PDT

Isolated the real VDD rail and added M4, M3, M2 and M1 with their vias. The discrepancy is already present in M5-only geometry at the abrupt 0.4 µm probe-lead / 7 µm rail transition. The refined M5 mesh gives 0.577681 Ω (last change 0.057%); Magic gives 0.514286 Ω, matching a simple series-strip estimate. The full isolated Magic model reproduces the earlier VDD result. Five exports pass ngspice and network topology checks. [Evidence](docs/rail-isolation.md).

**Correction:** Magic rejects negative threshold syntax. These results use accepted threshold zero, canonical `include VDD_B`, and `extresist all`, with no duplicate resistor node pairs. Historical checkpoint archives remain intact.

**Next:** measure at full-width rail faces to remove probe access resistance. Verify the M5-only body against the analytic strip resistance, then add layers/vias and seek an independent field-solver or validated transition model. Do not treat the present Magic model as an absolute DC standard: its M4 addition increases resistance, violating the expected passive-network trend. Full RC, substrate coupling and negative capacitance remain open.

## Earlier continuation update — 2026-09-18 07:45 PDT

Matched terminal positions close the analytic straight-strip discrepancy. Three mesh sizes now quantify bend and via-bridge differences, with all DC stitching checks passing. The real filler measurement-plane hypothesis leaves approximately 12–18% difference from the earlier Magic control. [Results and commands](docs/geometry-controls.md).

**Next:** isolate a single real filler rail and its probe transition. Compare M5-only, connected metal layers and the via network incrementally; refine the spatial mesh to establish absolute DC convergence. Do not assume a finite electrode is equivalent to a Magic point terminal in complex geometry. Device-aware RC, corner ground coupling and negative capacitance remain later gates. Existing Docker tools suffice.

## Earlier continuation update — 2026-09-16 18:53 PDT / 2026-09-17 01:53 UTC

Terminal calibration found and corrected electrode half-cell resistance in the independent DC reference. Four analytic strips pass at two mesh sizes; corrected filler stitching and 1 µm ngspice checks pass. Via-edge-aligned refinement completes but absolute resistance still differs from Magic by about 10–15%. [Evidence and commands](docs/terminal-calibration.md).

**Next:** match the terminal measurement planes, then isolate bends, multi-layer overlap and via resistance with small controls. Keep Magic negative-threshold/canonical selection diagnostic only: indiscriminate forcing produced duplicate resistors. Do not advance to full-ring RC qualification yet. Corner ground coupling and negative capacitance remain open. No additional tools are needed for this next experiment.

## Earlier continuation update — 2026-09-16 15:38 PDT

The distributed DC boundary benchmark passes: all 81 intervals are retained, with 4,593 seam ports at the finest mesh. A two-part SPICE model passes ngspice at the 1 µm mesh. See [the comparison](docs/filler-stitch.md).

**Scope:** this is an independent conductor-only numerical reference, not a stitched Magic RC model. Absolute resistance still changes with refinement and differs from Magic; the finer ngspice attempt timed out.

**Next:** benchmark and refine the electrode/probe-lead treatment, reconcile the Magic/reference discrepancy, then transfer the boundary interface into device-aware RC sections. Resolve corner ground coupling and negative capacitance before full-ring camera simulation.

## Earlier continuation update — 2026-09-16 14:52 PDT

The small-section experiment is complete: four coupons extract in under 29 seconds and pass the documented DC/topology and device-LVS checks. See [results and limitations](docs/ring-sections.md). The models include external measurement leads; they are not bare macro-edge resistances.

**Next:** define multiport abutment boundaries and compare a stitched two-filler model with the monolithic two-filler coupon. Then resolve the corner substrate-ground connection and negative capacitance entries before whole-ring transient simulation. The earlier full-ring extraction blocker is narrowed, not fully resolved.

## Start here

1. Read the [README](README.md), [changelog](CHANGELOG.md), and [physical-ring notes](docs/power-ring.md).
2. Open [the HTML notebook](docs/overview.html) with its adjacent `docs/assets/` directory available. GitHub previews the README images; it does not execute the notebook's interactive slider.
3. Use Docker Desktop with WSL integration and the pinned image in `scripts/run-tools.sh`. See [Docker/VNC setup](docs/docker-setup.md). No host `.venv` is required.

```sh
# From the repository root, with Docker running:
bash scripts/run-tools.sh ngspice --version
bash scripts/start-vnc.sh
```

The desktop is normally at `http://localhost:8080/vnc.html?autoconnect=true&resize=scale`. The checkout is mounted at `/foss/designs`; save work there so it stays on the host.

## Current verified baseline

| Item | Current evidence |
| --- | --- |
| Sensor core | Connected 3×3 core; 20 × 20 µm photodiodes, 80 × 50 µm pixel pitch; 37 MOS devices and nine diodes |
| Proposed larger camera | 64×64 at 40 µm pitch remains a planning concept, not a routed design |
| Physical power ring | 1.110 × 1.010 mm; two supply pads, four corners, 125 fillers; ten clamps |
| Physical checks | Ring Magic DRC: 0; configured ring/assembly KLayout DRC: 0; ring device LVS: unique match; 10,948 assembly continuity probes pass |
| Connecting-wire RC | VDD 5.14704 Ω; ground 7.19454 Ω; isolated-route capacitance model |
| Ring load screen | Nominal/hot pass; maximum supply drops 2.567/2.451 mV; finer hot cross-check passes |
| Full-ring distributed RC | **Unfinished and unvalidated** |
| Signal pads | **Not yet placed/routed into this ring** |

The ring load screen uses ring **schematic devices plus extracted connecting wires**. It is not full-ring extracted camera verification. Earlier 24-condition core and nominal/hot camera-plus-clamp passes remain separate checkpoints.

## 1. Resolve full-ring extraction first

**Goal:** obtain a tractable, physically connected ring interconnect model without losing rail continuity or silently omitting resistors.

- Review `build/power-ring/pex*` evidence restored from the ring archive. Flattened, unsimplified, metal-only, and macro-hierarchical attempts did not export a complete validated model. The hierarchical attempt also emitted warnings.
- Investigate extraction of smaller macro/rail sections with explicit boundary terminals, then assemble them using the real placements and abutments. Preserve the actual parallel supply paths, corner connections, pad straps, and substrate assumptions.
- Start with one filler or corner and a two-cell abutment before repeating a whole-ring job. Put bounded runtimes around experiments and retain incomplete status rather than accepting partial output.
- Use `scripts/check-power-ring-rc.py` as an audit starting point. It currently expects a flat model; hierarchical assembly requires an appropriate flattening/audit extension.

**Exit checks:** every intended bond-to-core path has finite nonzero extracted resistance; VDD and ground stay distinct; resistor-network current balance passes; shorting only extracted metal resistors preserves device LVS; capacitance and substrate treatment are documented; no stale or zero-resistor output is accepted as a successful extraction.

## 2. Simulate the complete camera with ring parasitics

- Combine validated ring RC, actual connecting-wire RC, and the existing extracted sensor core. Avoid double-counting devices or capacitance.
- Retain all ten clamps and filler decoupling. Start with the existing assumed board supply and generic ADC load, then substitute selected board/package/ADC models when available.
- Begin nominal, then hot; use the 1 ms soft-start and 200 µs post-ramp reset hold as the starting sequence.
- Complete three frames, all nine pixels per frame. Measure output/HOLD error, brightness ordering, startup bias, rail movement, and frame repeatability.
- Reuse the documented screens where applicable: sampling error <0.5 mV, startup reference deviation <1%, frame-two/three change <50 µV, and numerical comparison <10 µV. Explain any changed criterion before using it.
- Investigate strict-tolerance ring-load timeouts separately. A finer-step agreement under practical tolerances does not prove strict-tolerance convergence.

**Exit checks:** complete finite waveforms, all samples pass, independent time-step/tolerance checks, documented model scope. Add metal-temperature effects before claiming interconnect temperature coverage.

## 3. Add the signal pads and complete the small test die

- Freeze a pin table for analog output, bias/reference connections, row/reset/mux controls, supplies, grounds, and test access from the actual schematic ports.
- Reuse the evaluated foundry analog-pad/local-protection candidate where appropriate; evaluate control-pad types and voltage domains explicitly.
- Replace reserved fillers with pads, route the signals, and recheck decoupling/startup because filler count and pad loading change.
- Run full assembly device LVS, physical connectivity, extraction, and the applicable DRC configuration. Keep coupon checks distinct from full-die checks.

**Exit checks:** complete schematic-to-pad connectivity, clean applicable layout checks, and camera simulations including pad loading and routed parasitics.

## 4. Move from a test vehicle toward fabrication

- Confirm current wafer.space slot, pad/bonding, seal-ring, chip-ID, density, antenna, CUP, and submission requirements against the selected run.
- Resolve optical access, metal/fill clearance above junctions, packaging/window/lens, and wire-bond carrier details.
- Characterize photodiode optical response, dark current, noise, mismatch, and usable dynamic range; the current illumination model is assumed photocurrent.
- Choose the actual off-chip ADC, acquisition timing, board regulator, and controller; then assess frame rate and larger-array architecture.
- Scale beyond 3×3 only after these interfaces and extraction are reliable. Revisit pixel pitch and area budgets before treating the 64×64 concept as a commitment.

## Files and reproduction

- [Ring generator](layout/power-ring.py), [build/check flow](scripts/build-power-ring.sh), [load-test runner](scripts/evaluate-power-ring.py).
- [Ring results](simulations/power-ring-verification.json), [model and reproduction notes](docs/power-ring.md).
- [Integrated-core notes](docs/integrated-layout.md), [corner matrix](docs/integrated-corners.md).
- [Pad notes](docs/pad-layout.md), [clamp convergence](docs/clamp-convergence.md), [board supply](docs/board-supply.md).
- [Ring checkpoint manifest](checkpoints/power-ring/manifest.json) and `checkpoints/power-ring/evidence.tar.gz`; earlier dependencies remain in their respective checkpoint directories.

Archives supplement the source tree. Inspect or restore them into a separate directory first, verify their manifests, and copy only the required generated artifacts into the checkout. Several archives overlap and contain earlier source snapshots: do not blindly unpack all archives over current sources. `scripts/restore-checkpoint.py` restores the original size-study checkpoint only, not every later checkpoint.

```sh
mkdir -p /tmp/power-ring-review
tar -xzf checkpoints/power-ring/evidence.tar.gz -C /tmp/power-ring-review

# Once the relevant generated models/dependencies are available:
bash scripts/run-tools.sh python3 scripts/report-power-ring.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The full rebuild commands are in `docs/power-ring.md`. Full-ring extraction scripts are experimental and can run for a long time without producing a usable model. The ordinary ring build keeps device LVS separate from distributed RC extraction.

For each next checkpoint, update the changelog, this handoff date/status, README pictures, and HTML notebook; save numerical results and failed-run status alongside successful evidence.
