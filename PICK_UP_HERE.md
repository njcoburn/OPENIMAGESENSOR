# Pick up here — GF180 3×3 camera

Updated **2026-09-24 00:50 PDT** (America/Los_Angeles).

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

> Read PICK_UP_HERE.md and docs/three-frames.md. The normal-operation full-camera candidate completes three frames and passes the retained repeatability and matched DC readout screens. Continue with a bounded load/process/voltage/temperature matrix, revalidating the bias-frozen capacitor approximation for each condition. Preserve the evidence and keep nonlinear startup, distributed wire resistance and fabrication qualification as separate open gates.
