# Terminal calibration and passive extraction controls

> **Correction — 18 September 2026:** Magic rejected the earlier `extresist threshold -1` command; it was not a validated negative-threshold recipe. See [real-rail isolation](rail-isolation.md) for the accepted `threshold 0` + canonical `include` + `extresist all` diagnostic and new audits. Historical exports remain preserved.


Recorded 2026-09-16, 18:53 PDT (2026-09-17 01:53 UTC).

## Outcome

A reference-mesh electrode error is corrected in the opt-in `equipotential` mode. Four full-width M5 strip tests match the analytic ideal-electrode resistance at maximum mesh sizes 1 and 0.1 µm. The historical `legacy` mode remains the default to preserve earlier experiment reproduction; use `--electrode-model equipotential` for new ideal-electrode studies.

![Terminal calibration and mesh refinement](assets/terminal-calibration.png)

Each strip has two full-width electrodes, each 0.2 µm long. For sheet resistance 0.04 Ω/square, the exact resistance is `0.04 × (L − 0.4) / W`. The old scheme included electrode half-cell resistance at the free-metal interface. Corrected distances include only the adjacent free-metal half-cell. This test verifies terminal treatment on uniform straight strips, not accuracy for arbitrary layered geometry.

| Strip L × W (µm) | Exact / corrected (Ω) | Legacy 1 µm (Ω) | Legacy 0.1 µm (Ω) | Magic raw diagnostic (Ω) | Magic SPICE diagnostic (Ω) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10 × 0.4 | 0.960 | 0.980 | 0.970 | 0.980 | 0.9805 |
| 20 × 0.4 | 1.960 | 1.980 | 1.970 | 1.980 | 1.9805 |
| 10 × 2 | 0.192 | 0.196 | 0.194 | 0.196 | 0.1965 |
| 20 × 2 | 0.392 | 0.396 | 0.394 | 0.396 | 0.3965 |

The Magic raw values match `0.04 × (L − 0.2) / W`, the separation of the labels' lower-left x coordinates. Changing label height did not change the extracted results. This supports a different terminal convention for these strips. The observed 0.0005 Ω SPICE increment is recorded without applying a speculative correction to other models.

## Selection controls must not be mistaken for passes

- Area and point labels with threshold zero: only the narrow strips export resistors. The wide strips have zero lumped resistance in `.ext` and are omitted; incomplete four-path models.
- `extresist all` and unrestricted negative threshold: duplicate parallel resistors on every strip; invalid models for this comparison.
- Explicit wide canonical names with threshold zero: no resistors; incomplete.
- Negative threshold plus exactly the four canonical `_B` names: one path per strip. Valid only as this controlled diagnostic. Production extraction is unchanged.

The report asserts these expected failure classifications as well as the successful analytic results. Extraction completion alone is never interpreted as a topology pass.

## Real two-filler coupon

The corrected 1, 0.5 and 0.25 µm meshes all pass stitched/combined resistance comparison below 1e-8 relative difference. The 1 µm hierarchical SPICE model also passes ngspice. Fine runs are matrix-only. A separate 0.5 µm mesh aligned to every via edge completes in about 91.5 seconds, with 6,715 boundary ports and 1,115,338 / 1,122,053 combined / stitched nodes.

Absolute resistance remains mesh-sensitive, and the corrected 0.25 µm values remain about 10–15% above the earlier Magic control. Via-edge alignment alone does not close the gap. These values include coupon probe leads. See the [machine-readable results](../simulations/terminal-calibration.json) and HTML table for exact values. No device, substrate or capacitance qualification is implied.

## Reproduce

Use the pinned Docker image and prerequisites in [the preceding benchmark](filler-stitch.md). No host scientific `.venv` is required.

```sh
bash scripts/run-tools.sh python3 scripts/prepare-terminal-calibration.py
bash scripts/run-tools.sh python3 scripts/run-terminal-calibration.py --part calibration
bash scripts/run-tools.sh python3 scripts/check-magic-terminal-selection.py
bash scripts/run-tools.sh python3 scripts/run-terminal-calibration.py --part filler
bash scripts/run-tools.sh timeout 180 python3 scripts/compare-filler-stitch.py --step-um 0.5 --electrode-model equipotential --align-vias --skip-spice
bash scripts/run-tools.sh python3 scripts/report-terminal-calibration.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Evidence is in `checkpoints/terminal-calibration/evidence.tar.gz`, with SHA-256 hashes in `manifest.json`. It includes geometry, Magic exports/logs, control matrices, all corrected filler matrices, terminal maps, results and the independently solved 1 µm hierarchical netlist. Larger fine-grid SPICE decks are reproducible but omitted from the archive. The preceding checkpoint supplies parent geometry and earlier diagnostics. Do not overwrite an active checkout when restoring archives; inspect/extract into a separate directory first.

## Next experiment

1. Match terminal measurement planes explicitly on the same strip and coupon geometry; compare finite-area ideal electrodes with Magic's observed label-coordinate behavior.
2. Add single bends, two-layer overlap and single-via controls to locate the remaining solver discrepancy. Check via current distribution and spatial convergence separately from partition agreement.
3. Only after those controls pass, carry the 81-interval interface into device-aware sections. Resolve corner substrate-ground coupling and negative capacitance before full-ring transient validation.
