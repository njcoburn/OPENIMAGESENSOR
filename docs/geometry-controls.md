# Matched terminal positions, bends and vias

> **Correction — 18 September 2026:** Magic rejected the earlier `extresist threshold -1` command; it was not a validated negative-threshold recipe. See [real-rail isolation](rail-isolation.md) for the accepted `threshold 0` + canonical `include` + `extresist all` diagnostic and new audits. Historical exports remain preserved.


Recorded **2026-09-18 07:45 PDT**.

![Comparison and via geometry](assets/geometry-controls.png)

## Method and outcome

The straight 10 × 2 µm M5 strip retains 0.2 µm full-width ideal electrodes. Their inner faces are x = −4.8 and +4.8 µm. Magic label rectangles start at those x coordinates, unlike the previous test. Both raw Magic and the finite-volume model now agree with `0.04 × 9.6 / 2 = 0.192 Ω` at all three mesh sizes. A 0.0005 Ω export increment remains in each of these Magic SPICE controls; no general offset correction is applied.

The other controls are a two-turn M5 bend, a bridge through M4 with one via at each end, and the same bridge with three vias at each end. Every raw/exported Magic control must contain exactly one resistor between the intended terminals. The explicit canonical-net/negative-threshold recipe is retained only for these diagnostics. DRC, capacitance and devices are outside the scope.

| Control | Magic raw Ω | FV 0.05 µm Ω | Difference | Last mesh change |
| --- | ---: | ---: | ---: | ---: |
| straight | 0.192000 | 0.192000 | 0.000% | 0.000% |
| bend | 0.232000 | 0.237083 | 2.191% | -0.128% |
| via_bridge | 9.254500 | 9.306893 | 0.566% | -0.033% |
| wide_via_bridge | 3.254500 | 3.256333 | 0.056% | -0.032% |

The FV matrices use exact via-edge alignment and maximum steps of 0.2, 0.1 and 0.05 µm. Stitched and combined networks agree below 1e-8 relative error on every run. These runs use matrix solves; no independent ngspice pass is claimed. The smaller last-step changes are evidence of refinement behavior, not a certified continuum error bound. Neither method is established as ground truth for the bend/via shapes.

## Real filler measurement-plane hypothesis

Keep all metal and via geometry fixed. Replace the original small terminal patches with full lead-width (0.4 µm) electrodes: left x = [−2.2, −2.1] µm, right x = [21.9, 22.2] µm. Their inward faces match the earlier Magic labels' lower-left x coordinates. This does not establish equivalence of finite-area and point terminals in arbitrary geometry. At maximum mesh step 0.25 µm:

| Rail | Matched-plane FV Ω | Earlier Magic Ω | Difference |
| --- | ---: | ---: | ---: |
| VDD | 0.561278 | 0.499084 | 12.46% |
| VSS | 0.561922 | 0.498746 | 12.67% |
| DVDD | 0.532081 | 0.451211 | 17.92% |
| DVSS | 0.532138 | 0.451234 | 17.93% |

Terminal positioning alone does not resolve the real coupon gap. The next experiment should isolate a single real rail/probe transition, then add connected layers and vias incrementally. Absolute DC convergence, corner ground coupling and negative capacitance remain open before full-ring RC validation.

## Reproduce and restore

Use the pinned Docker environment and parent geometry from [terminal calibration](terminal-calibration.md).

```sh
bash scripts/run-tools.sh python3 scripts/run-geometry-controls.py
python3 scripts/prepare-matched-filler.py
bash scripts/run-tools.sh timeout 180 python3 scripts/compare-filler-stitch.py --geometry-file build/geometry-controls/filler-matched.json --output-dir build/geometry-controls/filler-matched-0.25 --step-um 0.25 --electrode-model equipotential --skip-spice
bash scripts/run-tools.sh python3 scripts/report-geometry-controls.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The checksummed `checkpoints/geometry-controls/evidence.tar.gz` contains the inputs, exports, logs, matrices, plots and summaries. Fine SPICE decks are reproducible and omitted to reduce archive size. SHA-256 hashes are in `manifest.json`. Extract into a separate directory to avoid overwriting active work. The parent checkpoints retain the original filler and Magic reference. No sensor or ring layout edits were required.
