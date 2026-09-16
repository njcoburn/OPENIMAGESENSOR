# Physical supply ring and sensor power connections

This checkpoint assembles the installed GF180 I/O macros into a **1.110 × 1.010 mm power-ring test vehicle** and places the unchanged 3×3 sensor inside it. This is a development layout, not the proposed full-slot camera die.

## What is placed

- One `gf180mcu_fd_io__dvdd` and one `gf180mcu_fd_io__dvss` bond pad.
- Four `gf180mcu_fd_io__cor` corner cells.
- 125 `gf180mcu_fd_io__fill10` cells, maintaining the continuous supply stripes.
- Six parallel metal-2 connections at each supply pad's core-facing edge.
- In the separate `ring_sensor_power` assembly, the existing sensor is translated by (420, 385) µm and connected through a metal-3 VDD route and metal-4 ground route. The long added routes are 4 µm wide.

The foundry macros are copied without device-geometry edits. The supply pads join the core and I/O stripes into one analog supply domain. The four corners contain eight additional clamps: **ten clamps in total**, compared with the two-clamp electrical test earlier. The filler model contains 32 MOS-capacitor units per instance; the complete reference includes every filler. Replacing fillers with signal pads later changes both placement and decoupling.

[Foundry supply/corner documentation](https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/power.html) describes the clamps. Actual device counts and parameters come from the installed library model and extracted layout, not from a hand-estimated capacitor.

## Independent physical connectivity

The KLayout checker uses only overlap of metal 1–5 and vias 1–4. It does **not** join disconnected labels with matching names. It probes every supply-label location in every placed macro, the two ring-facing terminals, and the sensor supply terminals. It also checks that the positive supply and ground belong to different physical nets.

[LayoutToNetlist API](https://www.klayout.de/doc/code/class_LayoutToNetlist.html) supplies the net tracing. This is a metal-connectivity check; it does not replace device LVS.

## Connecting-wire extraction

An isolated copy of the actual added route shapes is extracted in Magic, retaining its two endpoint resistances and metal capacitance. The isolation means its capacitance is not a complete ring-to-core coupling extraction. The simulation explicitly references the isolated wires' substrate capacitance to core ground.

The initial 1.2 µm routes extracted as 10.8526 Ω (VDD) and 16.3276 Ω (ground). Widening the long routes to 4 µm and moving the landing outside the existing fill boundary reduced these to 5.14704 Ω and 7.19454 Ω. These values include the connecting geometry and via arrays; they exclude resistance inside the ring macros and inside the already-extracted sensor.

A passive-wire extraction initially omitted all resistors even though its lumped resistance was nonzero. The working script uses finite-area terminal labels, disables network simplification, and sets `extresist threshold 0`. The exported SPICE must contain both endpoint resistors before it can be used. Earlier output with no resistors is not treated as an ideal-wire result.

[Magic resistance-extraction reference](https://www.opencircuitdesign.com/magic/commandref/extresist.html) describes the thresholds and distributed network extraction. Full-ring extraction is a separate job; completion and validation must be established from its logs and exported model before any full-ring RC claim.

## Electrical screening

The load-test script combines all installed supply/corner/filler schematic models with the extracted connecting-wire RC. The board model retains 0.5 Ω source resistance, 2 nH series inductance, and 100 nF decoupling with 0.1 Ω ESR and 1 nH ESL. A 33 kΩ core load is supplemented by 100 µA pulses with 10 ns edges. The source ramps over 1 ms, with a 200 µs hold before loading is assessed.

This tests startup and supply/ground response at nominal and hot conditions. It is **not** a three-frame camera scan and **does not include ring-metal resistance** unless a separately verified full-ring model is explicitly substituted. Earlier camera sampling results therefore remain separate evidence.

## Verification boundaries

The development KLayout selection is `all,-antenna,-density,-cup`, matching the earlier recorded configuration. Density, antenna, CUP, full-slot dimensions, seal ring, chip ID, optical openings, bonding rules, ESD and package qualification are separate. No zero-marker report here is a complete wafer.space precheck.

Signal pads and their routing are not yet implemented. The sensor's signal ports remain unbonded. No fabrication or ESD-readiness claim is made from this power-only assembly.

## Reproduction

```sh
bash scripts/run-tools.sh bash scripts/build-power-ring.sh
bash scripts/run-tools.sh bash scripts/check-power-assembly.sh
bash scripts/run-tools.sh python3 scripts/check-power-ring-connectivity.py
bash scripts/run-tools.sh python3 scripts/check-power-ring-connectivity.py --assembly
bash scripts/run-tools.sh bash scripts/extract-power-leads.sh
bash scripts/run-tools.sh python3 scripts/evaluate-power-ring.py --practical
bash scripts/run-tools.sh python3 scripts/evaluate-power-ring.py --practical --fine --hot-only
bash scripts/run-tools.sh python3 scripts/report-power-ring.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The optional `scripts/extract-power-ring-unsimplified.sh` preserves the resistor mesh without in-tool reduction and reuses the first extraction's `ring_flat.ext`. Both the GDS geometry and that intermediate file must belong to the same checkpoint. Failed, unfinished, or unvalidated extraction outputs must not replace a verified simulation model.

### Extraction and convergence status

Four full-ring extraction variants were stopped without a complete RC export: flattened, unsimplified flattened, metal-only flattened, and macro-hierarchical. Their intermediate files and logs are retained in the checkpoint; none supplies the electrical results above. The macro-hierarchical variant also produced warnings that need resolution before use. The next extraction task is to partition and validate the ring network while preserving all abutting rail connections.

The strict direct load test timed out after 900 seconds. The completed nominal/hot tests use `reltol=1e-4`, `abstol=1e-12 A`, and `chgtol=1e-14 C`. This is a separate ring load experiment; earlier pixel/camera tolerances are unchanged. A finer time-step comparison is recorded separately when complete. Wire resistance remains at nominal temperature in these tests.

`build-power-ring.sh` performs flat device LVS without distributed resistance extraction. The optional `extract-power-ring*.sh` scripts reproduce experimental full-ring extraction attempts and may run for a long time without exporting a model. Do not include unfinished outputs in camera simulation.

## Restore the saved evidence

The local checkpoint is `checkpoints/power-ring/evidence.tar.gz` with a SHA-256 manifest alongside it. It contains the GDS, extracted lead model, verification logs, load-test waveforms, and stopped full-ring extraction evidence. Extract it into a separate review directory to avoid overwriting current work:

```sh
mkdir -p /tmp/power-ring-review
tar -xzf checkpoints/power-ring/evidence.tar.gz -C /tmp/power-ring-review
```

Use the pinned image in `scripts/run-tools.sh` for regeneration. The source sensor and other dependencies are in the preceding repository checkpoints; this archive supplements those checkpoints. No Docker installation or tool upgrade was required.

### Completed load-test results

| Condition | Maximum active core-supply drop | Maximum ground rise | 1% rail screen |
| --- | ---: | ---: | --- |
| 27 °C, 3.3 V | 2.567 mV | 1.438 mV | Pass |
| 125 °C, 3.0 V | 2.451 mV | 1.373 mV | Pass |

The hot case with a 50 ns requested time step agrees with the 100 ns run to **0.0353 µV** at core VDD and **0.000009 µV** at core ground on a common 100 ns grid after startup. The comparison limit is 10 µV. This checks time-step sensitivity under the practical tolerances; it does not establish strict-tolerance convergence or optical/camera performance. Both strict direct and strict exact-interface diagnostic runs timed out at 900 seconds.
