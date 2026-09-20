# Construction reduction and device-aware patch tests

Recorded **2026-09-18 13:17 PDT**.

![Network and buffer comparisons](assets/network-investigation.png)

The two-layer error is caused by construction-time reduction in these controls. Turning off final simplification does not disable ResDoneWithNode, which performs series, parallel and triangle reductions as the graph is built. Instrumentation retains 24 resistors for the 20-via control and 360 for the 300-via control. Independent matrix and ngspice solves agree on their unreduced resistance.

Both implementations of triangle-to-star conversion in ResTriangleCheck add 0.5 to each new floating-point branch resistance in milliohms. A separate six-line candidate removes those additions while retaining normal reduction. Its one-resistor outputs match the unreduced networks within 2e-6 relative, including printed precision, and recover the expected falling resistance when more vias are added. This confirms the cause on these two layouts; it is not broad qualification of all reduction cases.

The reader patch was tested separately on the actual output-buffer extraction and a synthetic parent containing two copies of that extracted cell. Each child has three PFETs, 19 extracted resistors and 150,473 capacitor records. Device parameters, capacitor connectivity/values and hierarchy are preserved. Capacitor names and order vary between runs, so comparisons use normalized multisets. The standalone diagnostic must apply the PDK's scalegrid 1 10 startup setting; omitting it changes device diffusion areas/perimeters. The corrected unmodified export matches the saved original buffer netlist after normalization.

Direct fill-heavy RC transient attempts use a 90-second watchdog, and their status is retained separately. Passing transient evidence uses the project's existing audited Schur capacitance reduction: eliminate 21,085 charge-neutral floating fill nodes and retain 276 capacitors. The capacitor network is unchanged by the reader patch; the raw baseline matches the previously audited source. No artificial shunt is added to these reduced-model tests.

All four reduced-model transients complete: baseline and reader-patched exports, each in the single-buffer and two-instance configurations. Conditions are nominal process, 27 °C default temperature, 3.3 V supply, 40 µA reference per buffer, a 0.7-to-0.9 V input step, 100 pF load and 6 µs duration. The maximum baseline/patched output difference is about 0.05 µV; the 100 µV comparison limit is a regression screen, not an ADC accuracy specification. The second hierarchical instance has a static 0.8 V input. These tests do not establish corner, noise, startup or whole-camera performance.

The reader and triangle candidates remain separate diagnostic builds. Installed tools, production netlists and layout files are unchanged. Next: combine the two corrections in one isolated build, re-extract representative device-aware blocks, and repeat topology/LVS and corner/transient checks before adopting any tool change. Then resume device-aware ring RC, including the outstanding substrate and negative-capacitance checks.

## Construction results

| Via control | Normal Ω | Unreduced Ω | Triangle candidate Ω |
| --- | ---: | ---: | ---: |
| two_end_columns | 0.106148000 | 0.105148036 | 0.105148000 |
| all_cuts | 0.118443000 | 0.093837201 | 0.093837100 |

## Direct raw-network attempts

- buffer, baseline: **failed_or_timeout**. Command '['ngspice', '-b', '/foss/designs/build/network-investigation/device-export/buffer/baseline.cir']' timed out after 89.99997384799644 seconds
- buffer, patched: **failed_or_timeout**. Command '['ngspice', '-b', '/foss/designs/build/network-investigation/device-export/buffer/patched.cir']' timed out after 89.99998210603371 seconds
- hierarchy, baseline: **failed_or_timeout**. Command '['ngspice', '-b', '/foss/designs/build/network-investigation/device-export/hierarchy/baseline.cir']' timed out after 89.99998475500615 seconds
- hierarchy, patched: **failed_or_timeout**. Command '['ngspice', '-b', '/foss/designs/build/network-investigation/device-export/hierarchy/patched.cir']' timed out after 89.9999800499645 seconds

The direct attempts included a 1e12 Ω numerical shunt per node; the passing reduced tests did not. No direct raw-network pass is inferred from export-preservation checks.

## Source and patches

- [Pinned triangle-reduction source](https://github.com/RTimothyEdwards/magic/blob/381714e2d5debf2ded71c5a6b6604e6b936422cf/resis/ResMerge.c#L612), with a second branch at line 747.
- [Triangle candidate](../patches/magic-8.3.664-triangle-offset.patch).
- [Instrumentation only](../patches/magic-8.3.664-construction-trace.patch).
- [Previously tested reader patch](../patches/magic-8.3.664-resistor-reader.patch).

## Reproduce

Start from the [export-diagnostic checkpoint](extraction-diagnostics.md) and its configured source checkout. The build script requires the pinned commit and a clean source tree, uses the existing local build configuration, and restores the source after saving diagnostic binaries. No system installation is performed.

```sh
bash scripts/run-tools.sh bash scripts/build-network-diagnostic.sh
bash scripts/run-tools.sh python3 scripts/run-network-trace.py
bash scripts/run-tools.sh python3 scripts/run-network-trace.py --fixed
bash scripts/run-tools.sh python3 scripts/solve-construction-trace.py
bash scripts/run-tools.sh python3 scripts/verify-construction-networks.py
bash scripts/run-tools.sh python3 scripts/check-device-export.py
bash scripts/run-tools.sh python3 scripts/audit-device-export.py
bash scripts/run-tools.sh python3 scripts/check-reduced-device-export.py
bash scripts/run-tools.sh python3 scripts/report-network-investigation.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The direct raw-network audit may take four 90-second watchdog intervals. The reduced regression reuses the audited buffer capacitance matrix only after verifying the raw source hash and normalized baseline netlist; it preserves the resistor/device topology and substitutes the newly exported resistor values.

`checkpoints/network-investigation/evidence.tar.gz` contains inputs, trace outputs, netlists, waveforms, logs, scripts and candidate patches. The manifest verifies SHA-256 hashes. Diagnostic executables and the source checkout are omitted; binary hashes and the source commit are recorded. Extract into a separate directory. No upstream issue or PR has been submitted. These are local investigation results, not fabrication signoff.
