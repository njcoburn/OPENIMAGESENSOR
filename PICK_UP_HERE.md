# Pick up here — GF180 3×3 camera

Updated **2026-09-19 22:39 PDT** (America/Los_Angeles).

## Where we stopped

Finish the **nine-pixel monochrome demonstrator first**, then consider 64×64. The filled chip layout and prototype test boards exist. **The final assembled chip is not electrically qualified or ready for fabrication.** Earlier core simulations must not be presented as full-chip passes.

| Area | Current evidence | Remaining work |
|---|---|---|
| Filled chip layout | Main DRC (excluding CUP), density/antenna, device LVS and 4,566 connectivity checks pass within documented scope | Run/package-specific signoff and manufacturing review |
| Final extracted capacitance | 4,037 semiconductor records retained; floating-fill reduction checked for charge/energy; 2,179 capacitors on 279 retained nodes | Distributed wiring resistance remains unqualified |
| Stock final-chip DC | Passes with unused-pad `.nodeset` initial guesses; supply 3.299839 V, current 80.401 µA | DC alone does not establish imaging or startup |
| Normal-operation transient candidate | Replaces only 1,680 MOS capacitors with their capacitance at measured settled bias | Neither trap nor Gear completes a frame; approximation has no in-run validation yet |
| Pad protection/startup | Isolated controls and some candidates pass; strict corner refinement fails | Resolve nonlinear clamp model separately; no accepted startup/ESD qualification |
| KiCad fixture | 40 × 40 mm removable carrier and tester; saved native DRC/pin-net checks pass | ERC, analog behavior, mechanical/bonding review and ADC timing |

Latest functional attempts were **manually stopped**, not reported as successful runs:

- `frame-100ns`: projected runtime exceeded the watchdog; no frame result.
- `frame-5000ns`: persistent time stagnation near **3.23002 ms**, second-row turn-off.
- `frame-5000ns-gear`: persistent time stagnation near **3.17001 ms**, second-row select rise.
- These are zero-based row 1 in the scripts. Earlier failed OP attempts include testbench setup errors; the final `op-100ns` stock-model DC result passes.

## First task when returning

**Isolate the row-switching stagnation.** Do not start another broad corner sweep or blindly repeat the long runs.

1. Read [functional-camera results](docs/functional-camera.md) and `simulations/functional-camera-attempts.json`. Preserve the saved failed decks/logs.
2. Add incremental waveform capture to a separate diagnostic run so a stalled run retains voltages/currents before the switching edge. Capture row/column controls, supply, output, clamp timing nodes and sampling-switch currents. Keep the established bias/history; cutting directly to the edge could change the circuit state.
3. Use matched circuit controls to isolate the cause. Change one feature at a time, state its physical/numerical justification, and keep all model/tolerance changes explicit. No candidate is currently accepted.
4. Once a complete frame exists, validate all 16 MOS-capacitor terminal-pair voltage ranges against the original C(V), brightness ordering for all nine pixels, a matched DC transfer reference, acquisition error and tighter timestep/tolerance agreement.
5. Run three repeated frames, then process/voltage/temperature and realistic load checks. Recompute and validate any bias-frozen capacitance for each condition.
6. Complete the separate startup/protection investigation, distributed wire-R qualification, ADC-specific sequence, board electrical checks and manufacturing review before fabrication.

The fast sample/hold regression fixture is **not an ADS1115 model**. ADS1115 is for a slower acquisition sequence that still needs validation. There is no selected manufacturing run, wire-bond provider, package or controller. No new user decision is required for the next numerical diagnostic.

## Find the important files

- [Team overview](docs/overview.html), [changelog](CHANGELOG.md), [dated next-step history](NEXT_STEPS.md).
- [Functional candidate](docs/functional-camera.md), [full electrical plan](docs/full-chip-electrical-plan.md), [filled chip](docs/filled-demonstrator.md).
- [wafer.space version audit](docs/wafer-space-version-audit.md): inspected PDK model files match; a version upgrade alone is not the fix.
- [Matched ngspice 46/47 comparison](docs/ngspice-version-comparison.md): both stock extracted tests fail; a separate v47 multiplier parsing issue has a [public issue draft](docs/reviews/ngspice47-cap-multiplier-issue.md). Nothing has been posted.
- [Tiny Tapeout / wafer.space / JKU references](docs/gf180-shuttle-references.md): useful pad precedents, not proof that our analog transient passes.
- [KiCad projects and Windows instructions](hardware/carrier/README.md), [carrier fixture HTML](docs/carrier-fixture.html).
- `scripts/prepare-functional-pad-model.py`, `freeze-functional-pad-model.py`, `simulate-functional-camera.py`, `analyze-functional-camera.py`, `report-functional-camera.py`.
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

> Read PICK_UP_HERE.md and the functional-camera evidence. Continue with a bounded row-switching diagnostic that preserves waveforms before stagnation. Keep the current layout and qualification gates, and report separately what passes, what is a numerical approximation, and what remains unverified.
