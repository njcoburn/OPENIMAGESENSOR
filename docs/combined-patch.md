# Combined extraction-patch regression

Recorded **2026-09-18 14:06 PDT**.

Both Magic 8.3.664 corrections are now tested together in an isolated executable. Fresh buffer and column-readout extraction passes **4/4 LVS comparisons** and **80/80 short transients**, covering typical/ff/ss/fs/sf at −40, 27, 85 and 125 °C, at 3.3 V. All 40 baseline/candidate sample comparisons pass the 100 µV regression screen; largest difference: **0.02227 µV**.

![Process/temperature comparison](assets/combined-patch.png)

| Block | MOS devices | Extracted resistors | Raw capacitors | Eliminated floating fill nodes |
|---|---:|---:|---:|---:|
| Buffer | 3 | 19 | 150,473 | 21,085 |
| Column readout | 7 | 75 | 167,677 | 22,908 |

## What was checked

- Fresh GDS extraction with matched baseline and combined reader/triangle patch builds, including the PDK startup grid.
- LVS after resistor-net collapse against each schematic; actual RC networks retained for simulation.
- Buffer: 40 µA reference, 0.7→0.9 V input, 100 pF load, samples at 1.9 and 6 µs. Screen requires finite completed traces, in-rail samples and positive response.
- Readout: 0.5 µA reference, ideal 0.5/0.8/1.1 V columns, sequential 3.3 V selection, 30 pF load. Samples at 5/10/15 µs must be within 10 mV of the selected input.
- Both via controls match their independently solved unreduced graphs within 2 ppm: approximately 0.105148 Ω (20 vias) and 0.0938371 Ω (300 vias). Raw and exported values agree, demonstrating both fixes in the same executable.

## Scope and remaining gates

Fresh extraction is not byte-identical: internal readout terminals are renumbered and some printed capacitances differ slightly. Exact comparison flags are retained in the JSON; LVS is the connectivity gate. Capacitive-only floating fill is eliminated by the existing charge-neutral Schur reduction. The readout's existing BIAS-to-ground capacitance redistribution remains an approximation.

These are short block regressions with ideal references and column drivers, not an integrated camera/ADC qualification. No direct full-fill transient, supply-voltage sweep, mismatch, noise, new DRC or optical characterization is claimed. The 100 µV screen measures regression change, not ADC accuracy. Installed Magic and production GDS remain unchanged. The candidate is not adopted as a production tool.

**Next:** use the candidate on a representative ring section, audit substrate connections and signed capacitances, then compare DC resistance and reduced-RC transients before attempting a full-ring model.

## Reproduce

Use the pinned Docker environment described in the repository setup guide. The matching configured source checkout and baseline build are prepared by `scripts/build-export-diagnostic.sh`; coupon inputs come from the preceding extraction-diagnostics checkpoint.

```sh
bash scripts/run-tools.sh bash scripts/build-combined-diagnostic.sh
bash scripts/run-tools.sh python3 scripts/extract-combined-diagnostic.py
for block in buffer readout; do
  for mode in baseline combined; do
    bash scripts/run-tools.sh python3 scripts/reduce-$block.py --work-dir build/combined-patch/$block/$mode
  done
done
bash scripts/run-tools.sh python3 scripts/check-combined-controls.py
bash scripts/run-tools.sh python3 scripts/check-combined-diagnostic.py
bash scripts/run-tools.sh python3 scripts/report-combined-diagnostic.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Evidence: `checkpoints/combined-patch/evidence.tar.gz`, with SHA-256 manifest. Source commit, patches, exact inputs, binary hashes, netlists, LVS, reduction reports, simulator decks/logs/waves and results are retained. Executables and source checkout are regenerable and omitted.
