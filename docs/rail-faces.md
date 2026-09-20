# Full-width rail-face comparison

Recorded **2026-09-18 11:10 PDT**.

![Rail-face measurements](assets/rail-faces.png)

The M5-only rail agrees with the analytic value 0.04 × 20 / 7 = 0.114285714 Ω at all three mesh sizes. Magic raw extraction agrees to its printed precision. Moving to full-width electrodes removes the large narrow-probe transition discrepancy in this controlled M5 comparison.

The new diagnostic clips every layer to x = 0…20 µm, preserving all interior rectangles, then replaces the external narrow M5 leads with 0.2 µm-long, 7 µm-wide ideal electrode extensions. Their inner faces are x = 0 and 20 µm. Magic label lower-left x coordinates match those planes. Only M5 is directly contacted; lower layers connect through their original vias. These are different electrical boundary conditions, not a physical pad change or proof that arbitrary Magic point terminals equal finite electrodes.

The earlier M5 narrow-lead coupon gives 0.577681 Ω; subtracting the analytic body gives 0.463395 Ω for the configuration difference. Its simple lead-strip contribution is 0.400000 Ω, leaving about 0.063395 Ω beyond that one-dimensional estimate. This is evidence for spreading/access resistance in that geometry; it is not a universal correction to subtract from full-device extraction.

Every exported resistor network is checked for positive resistances, duplicate node pairs, disconnected nodes and agreement with an independent ngspice solve. All spatial meshes pass the stitched/combined 1e-8 relative screen. These checks verify topology and solving; they do not certify geometric extraction accuracy.

For M5–M3, M5–M2 and M5–M1, raw Magic agrees with the 0.05 µm spatial mesh within 0.013%; the last mesh changes are below 0.003%. This is strong numerical agreement for these conductor-only controls, not an independent certification of full RC accuracy. The exports add approximately 0.0005 Ω per resistor (within printed precision), raising the effective rail-face resistance by about 11.2% relative to the spatial model. The full-stack values are 0.0891035 Ω raw, 0.0891144 Ω spatial and 0.0990837 Ω exported.

The M5–M4 Magic diagnostic still increases resistance when passive metal is added, contrary to the spatial-model trend. Raw extraction and exported SPICE must also be distinguished: export changes the individual resistor values, and the total effect depends on network topology. No blanket offset subtraction or production netlist modification is applied.

Next: isolate the two-layer Magic anomaly and inspect the raw-to-SPICE resistor conversion before accepting the layered extraction as an absolute reference. Keep full-ring capacitance, substrate coupling and camera transient qualification behind that check. Production sensor and ring GDS are unchanged.

## Comparison

| Stack | FV 0.05 µm Ω | Magic raw Ω | Magic SPICE Ω | Raw vs FV | Last mesh change |
| --- | ---: | ---: | ---: | ---: | ---: |
| m5-to-m5 | 0.114286 | 0.114286 | 0.114786 | 0.000% | -0.0000% |
| m5-to-m4 | 0.093853 | 0.118443 | 0.118943 | 26.201% | -0.0027% |
| m5-to-m3 | 0.089157 | 0.089146 | 0.099119 | -0.013% | -0.0029% |
| m5-to-m2 | 0.089120 | 0.089109 | 0.099091 | -0.012% | -0.0026% |
| m5-to-m1 | 0.089114 | 0.089103 | 0.099084 | -0.012% | -0.0025% |

## Reproduction

```sh
bash scripts/run-tools.sh python3 scripts/run-rail-faces.py
bash scripts/run-tools.sh python3 scripts/report-rail-faces.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Use the pinned Docker environment and [isolated-rail checkpoint](rail-isolation.md). The three mesh maxima are 0.25, 0.1 and 0.05 µm, with via-edge alignment and a 180-second watchdog per run. Magic uses accepted threshold zero, canonical `include VDD_B`, and `extresist all`. The spatial solves are matrix-only; ngspice independently checks the Magic exports. No new DRC/LVS or full-RC pass is claimed.

The compact `checkpoints/rail-faces/evidence.tar.gz` stores inputs, scripts, raw/exported netlists, logs, results and figures with SHA-256 hashes in `manifest.json`. Large matrices and generated spatial SPICE decks are reproducible and omitted. Extract to a separate folder when restoring. Exact values are in [the JSON summary](../simulations/rail-faces.json).
