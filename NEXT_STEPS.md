# Next steps — resume the GF180 image sensor

**Handoff recorded: 2026-09-16 13:11 PDT (America/Los_Angeles, UTC−07:00)**

**UTC: 2026-09-16 20:11**

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
