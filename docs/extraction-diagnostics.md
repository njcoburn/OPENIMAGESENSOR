# Magic export and two-layer diagnostics

Recorded **2026-09-18 12:27 PDT**.

![Diagnostic comparisons](assets/extraction-diagnostics.png)

The export offset is traced to the resistor reader in Magic 8.3.664: it adds 0.5 to a floating-point resistance expressed internally in milliohms. Removing that addition in a local diagnostic build removes the measured 0.0005 Ω increment. An unmodified build with the same configuration reproduces the installed export resistor by resistor, isolating the one-line change from build differences. The patched build re-exports unchanged raw files and matches their effective resistance in all five stacks; both builds pass independent ngspice checks.

For the full stack, raw and patched resistance are about 0.0891035 Ω, versus 0.0990837 Ω from the unmodified export. This confirms the export cause for these resistor networks. It does not validate the patch for every device, hierarchy or capacitance use case, and does not fix raw geometry extraction.

The two-layer anomaly is independent of export. Keeping both metal shapes fixed and adding vias from the 20-cut end-column subset to all 300 cuts raises raw Magic resistance from 0.106148 Ω to 0.118443 Ω. The spatial model decreases from 0.105155 Ω to 0.093853 Ω. Adding passive connections should not raise DC resistance under the same terminal conditions. This localizes an inconsistency to Magic's raw two-layer via-array modeling. Removing a single cut also fails to eliminate it. The exact internal extraction cause remains open; no extraction patch or layout workaround is validated.

The source was checked out at the exact 8.3.664 release commit. The diagnostic uses a standalone, non-Tcl build because the container lacks Tcl development configuration; an equivalent unmodified build controls for that difference. A serial build avoids a generated-header race seen in the initial parallel attempt. The installed tools, production netlists and sensor/ring GDS were not replaced.

Next: inspect the raw two-layer contact/tile network before reduction and reproduce the failure in a minimal source-level regression. Separately broaden the reader-patch tests to device-aware hierarchical RC before considering adoption. Full-ring RC qualification remains open.

Source: [Magic 8.3.664 resistor reader](https://github.com/RTimothyEdwards/magic/blob/381714e2d5debf2ded71c5a6b6604e6b936422cf/extflat/EFread.c#L598). Diagnostic patch: [one-line change](../patches/magic-8.3.664-resistor-reader.patch).

## Export comparison

| Stack | Raw Ω | Unmodified export Ω | Patched diagnostic Ω |
| --- | ---: | ---: | ---: |
| m5-to-m5 | 0.114286 | 0.114786 | 0.114286 |
| m5-to-m4 | 0.118443 | 0.118943 | 0.118443 |
| m5-to-m3 | 0.089146 | 0.099119 | 0.089146 |
| m5-to-m2 | 0.089109 | 0.099091 | 0.089109 |
| m5-to-m1 | 0.089103 | 0.099084 | 0.089103 |

## Via-array controls

| Geometry | Cut count | Magic raw Ω | Spatial 0.05 µm Ω |
| --- | ---: | ---: | ---: |
| two_end_cuts | 2 | 0.114067 | 0.113080 |
| two_end_columns | 20 | 0.106148 | 0.105155 |
| missing_one_cut | 299 | 0.118470 | 0.093877 |
| all_cuts | 300 | 0.118443 | 0.093853 |

The via subset checks establish unchanged metal geometry. Each spatial control runs at 0.1 and 0.05 µm with exact via-edge alignment and passes stitched/combined comparison below 1e-8 relative. Network audits reject nonpositive resistors, duplicate node pairs and disconnected nodes. All patched/baseline exports and the four installed-tool via controls pass independent ngspice checks. These are conductor-only diagnostic tests; no general PDK, LVS, DRC or full-RC signoff is implied.

## Reproduction

Use the pinned Docker image and the [rail-face checkpoint](rail-faces.md). Fetch the matching source on the host if it is absent:

```sh
git clone --depth 1 --branch 8.3.664 https://github.com/RTimothyEdwards/magic.git build/magic-8.3.664-source
bash scripts/run-tools.sh python3 scripts/run-extraction-diagnostics.py
bash scripts/run-tools.sh bash scripts/build-export-diagnostic.sh
bash scripts/run-tools.sh python3 scripts/report-extraction-diagnostics.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The build helper checks the source commit and requires an unmodified source checkout. It patches only the ignored diagnostic source, saves the patched executable, restores the source line and builds the matching baseline. No system install is performed. The helper uses a repository-local installation prefix. The patched executable and source checkout remain ignored build artifacts; reproduction requires fetching the source, not installing new host tools.

`checkpoints/extraction-diagnostics/evidence.tar.gz` contains the inputs, unchanged raw files, generated netlists, logs, scripts, patch and results. Its manifest records SHA-256 hashes. Large spatial matrices/decks and compiler binaries are reproducible and omitted; binary hashes and source commit are recorded in the summary. Extract checkpoints into a separate directory. No upstream issue, message or pull request has been sent.
