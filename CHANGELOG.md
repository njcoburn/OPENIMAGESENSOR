# Changelog

## Project handoff and complete checkpoint — 2026-09-19 22:39 PDT

- Added [PICK_UP_HERE.md](PICK_UP_HERE.md) with the latest status, precise switching-edge blockers, ordered next tasks, Docker/KiCad startup guidance and archive restoration instructions.
- Checkpointed all accumulated work since `0eec653`: routed/filled 3×3 chip, pad/interface proposals, extraction and charge-conservation investigations, simulator/model controls and patches, reports/plots, manifests and diagnostic archives. Historical entries below retain their original results and limitations.
- Included native KiCad carrier/tester projects, local libraries, mechanical/BOM information, saved checks and review exports; board electrical/mechanical qualification remains open.
- Added the wafer.space setup audit and direct Tiny Tapeout, JKU, ISHI-KAI and wafer.space references to the overview. Inspected newer PDK models match the installed models; reference projects do not establish our transient qualification.
- Added the measured-bias functional-camera candidate: stock final-chip DC passes; 1,680 MOS capacitors are frozen only for the separate normal-operation experiment, with all other records retained. Trap and Gear attempts stall at row-switching edges and were manually stopped. No full-frame, startup, PVT, distributed-R or ADC qualification is claimed.
- Preserved matched ngspice 46/47 evidence and unsent public issue drafts. Updated README navigation and the HTML overview; no issue or review packet has been posted.
- This commit is an engineering checkpoint, not a fabrication release. Large evidence archives are intentional; Docker images, caches and regenerable build directories remain excluded.

## Matched simulator comparison — 2026-09-19 11:30 PDT

Built ngspice 46 and 47 with matching options in an isolated project folder. Both capacitor controls pass the independent current/charge checks. The unextracted stock corner fails at startup in 46 and fails parsing in 47. Both extracted stock-model cases fail at startup. A PDK-free reproducer isolates a separate v47 explicit-capacitor-multiplier parser failure (`m=1/8/70`); omitting the multiplier passes. **A simple upgrade does not resolve the qualification blocker.**

[Results and plot](docs/ngspice-version-comparison.md) · [Small public issue draft](docs/reviews/ngspice47-cap-multiplier-issue.md). Nothing has been posted and the working PDK/simulator/layout remain unchanged. The bounded comparison is complete; the earlier local helper candidate has not been promoted or rerun in this batch. Next: review the small parser failure separately from the extracted transient failure, then select a justified numerical-model correction and repeat accuracy/refinement gates before full-chip qualification. No new hardware or packaging decision is needed.


## Electrical checkpoint — 2026-09-19 10:02 PDT

**Complete-chip electrical qualification remains blocked by the clamp numerical model.** Both 50 ns corner runs complete, but both 25 ns/strict-tolerance runs abort at the 151 µs load transition in `e.x354.ehelper#branch`. No candidate is promoted; no full-chip startup/frame/PVT pass is claimed.

The final filled-chip lumped-capacitance extraction preserves all 4,037 semiconductor records. Its floating-fill reduction passes charge/energy checks and leaves 2,179 capacitors on 279 retained nodes. Distributed wire resistance remains unqualified. [Current results](docs/scaled-electrical-progress.md).

Next: use the saved failing deck to resolve the clamp-helper load-edge failure, then run the gated full-chip startup, repeated frames, refinement and PVT/load checks. `scripts/simulate-filled-chip-baseline.py` is prepared but has not been run; its prerequisites intentionally reject the current failed corner screen. No additional hardware or user decision is needed for this diagnostic work.


## Electrical qualification update — 2026-09-19 09:34 PDT

[New control-resolution and extracted-clamp results](docs/scaled-electrical-progress.md): matched capacitor controls pass the unchanged current limit; the isolated extracted clamp completes and passes 25 ns/tolerance voltage refinement. Both complete-corner capacitance placements now complete at 50 ns. These are diagnostic milestones, **not complete-chip qualification**. Final-GDS extraction and the [remaining electrical gates](docs/full-chip-electrical-plan.md) are open.

## Removable KiCad sensor fixture — 2026-09-19 08:30 PDT

- Added native KiCad 7 tester and removable 40 × 40 mm die-carrier projects, embedded symbols, local footprints, BOMs and mechanical coordinates.
- Implemented underside pogo contacts, optical aperture, local carrier bias resistors, disabled-by-default timing buffers, dual analog buffer and ADS1115 with faster-ADC expansion.
- Routed both boards and corrected native DRC findings: zero final violations/unconnected pads; schematic pin/net comparison passes. Saved reports with file hashes, PDF schematics and layout previews.
- Added Windows/Docker instructions, ADC timing limitations, assembly requirements and remaining qualification steps. Updated the HTML overview and top-level README. No fabrication release or external publication.

## Clamp-model local review — 19 September 2026

Audited ngspice’s expanded MOS-capacitor model and tested one algebraically equivalent internal scaling. Both standalone traces complete, but the current comparison fails (2.71 nA versus 0.1 nA); no clamp trial or fix accepted. [Results and specific reviewer questions](docs/clamp-model-review.md). External review has not occurred; further sweeps remain stopped.

## Filled working demonstrator — 2026-09-19 03:15 PDT

Regenerated central fill with all nine optical keepouts preserved. Density/antenna and main KLayout DRC report zero violations; device LVS matches uniquely; all 4,566 connectivity checks pass. [Evidence and reproduction](docs/filled-demonstrator.md). Next: resolve the clamp-model review, qualify post-fill electrical behavior, and confirm run/bonding requirements. The local simulator stop rule remains active; this is not a fabrication release.

## Routed working demonstrator — 2026-09-19 02:57 PDT

13 functional signal paths routed through local protection; seven supply/return pads connected. Metal connectivity: 4566 checks, PASS. Main KLayout DRC: 0 markers. Magic DRC: 0. Device LVS unique match: True. Four diagnostic signal paths remain disconnected; fill and final sign-off are open. [Evidence](docs/routed-demonstrator.md). Next: close physical findings and regenerate/verify fill; retain the stop on simulator parameter experiments.

## Pad-placement proposal — 2026-09-19 02:12 PDT

Created a 24-pad custom-carrier proposal, coordinate CSV, labeled diagram and separate unrouted GDS. All 19 core ports are represented. Packaging, diagnostic loading and protection choices remain open; no routing or sign-off claimed. [Review](docs/pad-proposal.md). Next: obtain the selected run/package requirements and close the pad-map review before routing.

## Completion reset — 2026-09-19 01:59 PDT

Frozen the 3×3 first-release scope, replaced stale completion instructions with milestone exit conditions and a two-trial solver stop rule, documented all 19 core ports and board timing assumptions, and prepared manufacturing/optical questions. README now leads with the 3×3 target. Signal pads are explicitly identified as unfinished. Final solver results and an unsent expert-review package accompany this checkpoint.

## MOS-capacitor isolation — 2026-09-19 01:49 PDT

24/24 simple capacitor transients complete; 0/4 initial isolated-clamp transients complete. Integration follow-up: 1/2 complete; refinement: 0/2 pass. [Evidence](docs/moscap-branch.md). Next: investigate solver conditioning and the behavioral-capacitor equations in this reproducer; the trapezoidal candidate failed refinement and is not accepted.

## Corner-interface evaluation — 2026-09-19 01:32 PDT

DC/AC interface comparison: NOT VERIFIED. Full-corner ramp/load transients: NOT VERIFIED. [Evidence](docs/corner-interface.md). Next: resolve full-corner startup before integrated 3×3 qualification.

This log summarizes engineering checkpoints. Simulation passes apply to the stated model and test conditions; they do not establish optical performance, manufacturing yield, or fabrication readiness.

## 2026-09-19 01:11 PDT — Verified resistor reduction and placement probes

Reduced four reference networks with preserved capacitance/device records and 16 DC comparisons. Added AC/load-step comparisons, half-step refinements, and retained failed full-corner startup attempts. Supply-ramp completion: False. [Report](docs/charge-reduction.md).

## 2026-09-19 00:42 PDT — Charge-conserving reference and confirmed 3×3 scope

Built and independently audited 8 lumped-C/distributed-R reference models; all 16 ngspice charge checks pass. Preserved exact R/device records, recorded every capacitor anchor, and retained the spatial-placement limitation. User confirmed the 3×3 demonstrator as the first release. [Report](docs/charge-reference.md).

## 2026-09-19 00:28 PDT — Area-sign fix and charge-accounting regression

Added an isolated one-line Magic area correction: 4 coupons now have no negative C, with 2 LVS and 16 DC checks passing. Eight independent small-control AC checks confirm a separate exported common-mode capacitance excess. Recorded both outcomes, archived evidence, and added a completion plan. [Report](docs/capacitance-candidate.md).

## 2026-09-18 23:55 PDT — Ring-section candidate audit

Fresh baseline/combined full and metal coupons; 4 LVS and 32 DC checks pass. Negative-energy witnesses reject the corner parasitic capacitance network. Added plot, preserved diagnostics, dated next steps and checksummed evidence. [Report](docs/ring-candidate.md).

## 2026-09-18 14:06 PDT — Combined extraction candidate

Fresh buffer/readout extraction, four LVS passes, 80 corner transients and two via controls pass. Added isolated build, reusable reducer paths, plots and archived evidence. [Report](docs/combined-patch.md).

## 2026-09-18 — Triangle-reduction cause and device-aware reader regression

Recorded **2026-09-18 13:17 PDT**. [Report](docs/network-investigation.md).

- Instrumented construction-time reductions and independently solved normal, unreduced and corrected graphs for two via arrays.
- Identified six half-milliohm additions in triangle-to-star conversion; a separate candidate restores unreduced DC resistance within printed precision.
- Preserved device parameters, capacitor connectivity/values and hierarchy in reader-patch exports of the actual output buffer and a two-instance fixture.
- Matched the PDK startup grid and verified the normalized baseline against the saved original buffer netlist.
- Four nominal reduced-RC transients pass with about 0.05 µV maximum output change. Four direct fill-heavy runs timed out; no raw-network transient pass is claimed.
- Updated documentation, plots and a checksummed checkpoint. Combined-patch qualification remains pending; production tools/netlists/layouts are unchanged.

## 2026-09-18 — Export-reader cause confirmed and via-array anomaly localized

Recorded **2026-09-18 12:28 PDT**. [Results and source reference](docs/extraction-diagnostics.md).

- Traced the per-resistor export increment to the Magic 8.3.664 floating-point resistor reader at pinned commit `381714e2d5debf2ded71c5a6b6604e6b936422cf`.
- Built isolated patched and unmodified executables with matched configuration. All five unchanged raw inputs export without the offset after the one-line patch; the baseline reproduces installed exports.
- Passed independent ngspice checks for both export variants and four via-array controls.
- Demonstrated the separate two-layer raw-extraction inconsistency by adding vias to unchanged metal. The exact extraction cause remains open.
- Added plots, reproducible build/test scripts, the diagnostic patch and a checksummed checkpoint. Installed tools, production netlists and layout files were not changed.

## 2026-09-18 — Full-width rail-face measurements

Recorded **2026-09-18 11:09 PDT**. [Results](docs/rail-faces.md).

- Replaced narrow measurement leads with ideal full-width M5 electrode faces on five diagnostic metal stacks, clipping to the two-filler x extent while preserving interior shapes.
- Verified the M5 body against the analytic 0.1142857 Ω strip resistance; raw Magic agrees to printed precision.
- Found raw Magic / spatial-model agreement within 0.013% for three or more layers; identified a roughly 0.0005 Ω per-resistor export increment producing about 11.2% equivalent-resistance increase. The two-layer anomaly remains open.
- Passed DC partition checks at three mesh sizes per stack and independently verified all five Magic exports with ngspice.
- Added a comparison plot, notebook/README update, dated handoff and compact checksummed evidence checkpoint. Production layout files are unchanged.

## 2026-09-18 — Isolated real rail and probe-access investigation

Recorded **2026-09-18 08:30 PDT**. [Results](docs/rail-isolation.md).

- Isolated the VDD-connected conductor component and added M4 through M1 incrementally, preserving the real metal and via shapes.
- Completed three mesh sizes per stage and two extra M5-only refinements. The discrepancy precedes the vias and strongly implicates the abrupt probe-to-rail transition.
- Verified five Magic exports against ngspice, audited topology and reproduced the earlier full-coupon VDD resistance.
- Identified a diagnostic inconsistency: adding M4 increases Magic resistance while the spatial model decreases. Absolute DC accuracy remains unqualified.
- Corrected the earlier negative-threshold interpretation after finding Magic usage errors. New accepted-syntax runs and logs are retained.
- Updated the notebook, README, handoff and compact checksummed checkpoint; production layout files are unchanged.

## 2026-09-18 — Matched terminal, bend and via controls

Recorded **2026-09-18 07:45 PDT**. [Experiment and limitations](docs/geometry-controls.md).

- Aligned the straight-strip measurement positions; analytic, mesh and raw Magic resistance agree at 0.192 Ω.
- Added a two-turn M5 path and M4/M5 bridges with one or three vias per transition, audited against duplicate/missing resistor paths and three mesh sizes.
- Verified DC stitching for every control and the real matched-plane filler. These new runs use matrix solves, with no new ngspice claim.
- The filler discrepancy remains approximately 12–18%; terminal matching alone does not resolve absolute resistance.
- Added comparison plots, documentation and a checksummed checkpoint. Physical sensor and ring layouts are unchanged.

## 2026-09-16 — Terminal calibration and extraction controls

Recorded **2026-09-16 18:53 PDT / 2026-09-17 01:53 UTC**. [Details](docs/terminal-calibration.md).

- Corrected ideal-electrode half-cell resistance in an explicit mesh mode; preserved legacy reproduction.
- Passed four analytic strip controls at two mesh sizes, corrected filler DC stitching and the 1 µm independent ngspice check.
- Isolated missing passive nets and duplicate parallel resistors in Magic selection controls; retained canonical negative-threshold extraction as a diagnostic only.
- Completed via-edge-aligned refinement. Absolute resistance convergence and the approximately 10–15% Magic discrepancy remain unresolved.
- Added plots, notebook/README updates, reproducible scripts and a checksummed evidence checkpoint. Sensor and ring geometry were not modified.

## 2026-09-16 — Distributed two-filler DC stitching benchmark

Recorded **2026-09-16 15:38 PDT**. See [method and limits](docs/filler-stitch.md).

- Enumerated all 81 conductor intervals across the actual two-filler boundary and verified exact metal coverage and via ownership in the two partitions.
- Built independent combined and stitched conductor-only finite-volume DC models from geometry, using nominal sheet/via values from the installed PDK. The finest mesh preserves 4,593 individual seam ports.
- Passed the 1e-8 relative stitching screen on four meshes and exported hierarchical two-part resistor SPICE models. The 1 µm model passes an independent ngspice DC check.
- Retained the finer ngspice 120-second timeout separately. Fine-mesh matrix results complete; absolute resistance remains mesh-sensitive and differs from the earlier Magic control.
- This validates DC partition construction, **not stitched Magic RC/device extraction**. Capacitor, substrate and full-ring camera qualification remain open.
- Added plots, JSON summaries, exact matrices, terminal maps, netlists and a checksummed archive. Sensor and ring geometry are unchanged.

## 2026-09-16 — Small ring-section extraction experiment

Recorded **2026-09-16 14:52 PDT**. See [the experiment notes](docs/ring-sections.md).

- Extracted one filler, two abutted fillers, a corner, and a corner-plus-filler with bounded runtimes; all corrected full-device exports finish in under 29 seconds.
- Added conductor-only controls, 830 physical macro-label probes, terminal connectivity/isolation checks, and sparse resistor-network current-balance checks.
- All four device LVS checks pass after shorting extracted resistor networks. Corner LVS uses the actual ring's tied analog supply domain; filler LVS preserves four ports.
- Preserved invalid dual-export and internal-terminal diagnostics. Narrow external probe leads resolve the missing-terminal checks; reported resistance includes those leads.
- Found semiconductor ground coupling in corner extraction, up to about 27% full/control resistance differences, and negative capacitor entries in corner exports. These models are not yet qualified for full-ring stitching or camera transient simulation.
- Added actual M5 geometry views, resistance comparison plots, JSON results, reproduction scripts, and a checksummed checkpoint. The sensor and ring GDS are unchanged.

## 2026-09-16 — Extracted camera, pads, and physical supply ring

Recorded **2026-09-16 13:11 PDT (America/Los_Angeles, UTC−07:00)**. This entry consolidates the work since commit `a87383d`; individual experiments were performed across the preceding sessions.

### Pixel array and extracted readout

- Added resistance/capacitance extraction of the 20 µm photodiode 3×3 array, with schematic, capacitance-only, and RC comparisons.
- Added column bias, a column multiplexer, and a shared output buffer, including layouts, extraction scripts, and off-chip ADC load simulations.
- Investigated cold idle/startup convergence and hot sampling margin. Revised the buffer reference to 40 µA and added an all-row startup reset; retained diagnostic failures and follow-up evidence.
- Connected the array, readout, and buffer in a physical test core: **37 MOS devices and nine photodiodes**, with passing recorded Magic/KLayout DRC and unique Netgen LVS.
- Completed the connected-core **24-condition process/temperature matrix**: all RC cases pass the 0.5 mV sampling screen; worst HOLD error is approximately **0.207 mV**. Wire R/C remains nominal and bias references are ideal in this matrix.

### Bias, pads, and board interface

- Added an external-resistor bias candidate: 5.1 MΩ from VDD to BIAS and 49.9 kΩ from PREF to ground. Recorded 84 DC and 18 selected startup/imaging cases; worst sampling error is approximately **0.216 mV**.
- Researched foundry GF180 pad macros and wafer.space/Tiny Tapeout references; evaluated analog-pad leakage, loading, and local protection candidates.
- Laid out a local protection cell with a nominal **149 Ω** poly resistor and extracted its capacitance. Recorded selected imaging checks and pad-wrapper LVS.
- Distinguished the untouched pad's 87 CUP.3 findings from the wafer.space-configured coupon checks, which exclude CUP and reported zero main, density, and antenna markers. These are different verification scopes.
- Evaluated foundry supply clamps, soft-start, and reset hold. Completed nominal/hot three-frame camera-plus-clamp runs with all 27 samples per run passing and worst sampling error approximately **0.221 mV**, corroborated by independent numerical checks.
- Added assumed board supply resistance, inductance, and local decoupling, including a weaker-supply sensitivity case and a finer hot simulation. These earlier camera tests use the supply-pad pair, not the new complete physical ring.

### Physical supply ring checkpoint

- Built a **1.110 × 1.010 mm** development ring from two supply pads, four corners, and 125 foundry filler cells; included all **ten clamps** and filler decoupling in the schematic model.
- Placed the unchanged 3×3 sensor inside the ring and routed power/ground using 4 µm trunks and bridges to the existing core buses.
- Recorded **zero ring Magic DRC violations**, **zero configured KLayout DRC violations on ring and assembly**, and a **unique flat ring device LVS match**.
- Independently checked metal/via connectivity: **10,948 assembly probes pass**, with no supply-to-ground short.
- Extracted the actual connecting-wire RC. Widening routes reduced total added resistance from **27.1802 Ω to 12.34158 Ω**: VDD **5.14704 Ω**, ground **7.19454 Ω**.
- Completed nominal/hot ring load tests using foundry schematic devices plus extracted connecting wires. Maximum core-supply drop: **2.567 mV nominal**, **2.451 mV hot**; both pass the declared 1% rail screen.
- The finer hot run agrees within **0.036 µV at core VDD** on the common comparison grid, below the 10 µV numerical screen.

### Incomplete work retained explicitly

- Four full-ring distributed RC extraction variants were stopped without a complete validated model. Their logs/intermediates are preserved; none is substituted for a verified camera model.
- Strict direct and exact-interface ring-load diagnostics timed out after 900 seconds. The completed ring load tests use the documented practical tolerances.
- Ring-metal resistance, complete assembly coupling, signal-pad routing, and full camera simulation with the physical ring remain outstanding.
- Ring DRC uses `all,-antenna,-density,-cup`. No complete die precheck, ESD stress, optical response, package, or fabrication qualification is claimed.

### Documentation and reproducibility

- Expanded the living [HTML notebook](docs/overview.html) with layouts, plots, comparison tables, assumptions, and failed-run evidence.
- Added source circuits, layout generators, simulation/check/report scripts, JSON results, GDS/netlist checkpoints, and checksummed evidence archives.
- Updated the top-level README with actual assembly and performance pictures, alongside the original labeled pixel, array schematic, and camera concept.
- Added the dated [continuation plan](NEXT_STEPS.md). The pinned Docker workflow remains the supported environment; no new host virtual environment was required.

## Earlier committed checkpoints

- **`a87383d` — Architecture and resolution overview:** README camera concept, area planning, grayscale resolution comparison, and HTML slider.
- **`8d76ff3` — Labeled layout and schematic:** README views of the larger photodiodes, pixel transistors, and 3×3 Xschem hierarchy.
- **`be0a047` — Verified GF180 arrays and Docker workflow:** single-pixel/repeatability work, 3×3 array schematics/simulations, 5/10/20 µm diode-size layout comparisons, local DRC/LVS, saved evidence, and Docker/VNC reproduction.
- The original gdsfactory prototype remains in [test.py](test.py); later verified layout work is under [layout/](layout/).
