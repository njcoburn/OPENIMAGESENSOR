# Output buffer process/temperature screen

Candidate: 20 µA PMOS follower reference, 0.5 µA readout reference, 3.3 V supply, 100 pF board load and a reset 20 pF sampling capacitor with 5 µs acquisition. The extracted array and qualified extracted readout remain connected through ideal wires; the buffer is schematic-only.

## Matrix and acceptance

- MOS process sections `typical`, `ff`, `ss`, `fs`, `sf` at −40, 27, 85 and 125 °C, with `diode_typical`: 20 cases.
- Typical MOS with `diode_ff` and `diode_ss` at −40 and 125 °C: four extra cases.
- Each case reruns the complete three-frame scan and a loaded DC buffer transfer sweep at its own corner and temperature.
- Screening criteria: maximum absolute output tracking error **and** sampling-capacitor error below 1 mV; correct dark/medium/bright ordering across all nine third-frame samples. A simulation failure is reported separately from an electrical failure.

The installed PDK supplies the model sections. Mixed MOS corners use its provided fs/sf parameter sets. This selection screens individual effects but does not cover every combination of MOS, diode and interconnect process corners.

Tracking error subtracts the loaded static transfer voltage at the instantaneous mux input. It measures dynamic lag and sampling disturbance, not the source follower's intentional voltage shift. Output-voltage ranges are recorded separately; a fixed room-temperature calibration is not established by small tracking errors.

## Fixed quantities and limits

Device temperature changes with `.temp`. Extracted wire R/C, the qualified lumped BIAS shunt, package/load estimates, ideal current references, supply, timing and assumed photocurrent remain fixed. Reference-current temperature drift and startup are not modeled. The diode models respond electrically to temperature, but this is not an optical responsivity/dark-current characterization of fabricated photodiodes.

No supply variation, interconnect corners, mismatch/Monte Carlo, noise, ESD/pad circuits, real ADC model, buffer-layout parasitics or full-chip routing is included. The 1 mV limit is an engineering screen, not a claim of ADC resolution or a qualified operating-temperature rating.

## Reproduce

```bash
bash scripts/run-tools.sh python3 scripts/buffer-corners.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The sweep runs up to four independent ngspice jobs, each restricted to one thread. Completed waveform calculations can be reused only when the generated testbench and recorded source/model hashes match. Incomplete cases remain visible in the report.

[Results JSON](../simulations/buffer-corners.json) includes all case metrics, source/model hashes and scope. Generated decks, DC sweeps, waveforms and logs remain under `build/buffer-corners/`. The comparison plot and table are embedded in [the notebook](overview.html#buffer-corners).

## Initial sweep result and numerical follow-up

The original sweep completed 23 of 24 cases; all completed cases passed. The largest original sampling error was 0.885 mV at `fs`, 125 °C, with the typical diode section. Across completed cases the sampled output range extended from about 1.67 to 2.40 V; total VDD power stayed about 134.0–134.3 µW because the reference currents were held ideal and fixed.

The `ss`, −40 °C case encountered a timestep failure during the initial idle interval, before the first readout. Smaller-step, alternate-integration and operating-point-initialization retries retain their logs separately under `build/buffer-corners/`. This is an inconclusive case, not a demonstrated electrical pass or failure. The latest HTML/JSON records any subsequent diagnostic results; the original evidence is preserved.

A separate smaller-step/tighter-tolerance run checks the largest completed error case:

```bash
bash scripts/run-tools.sh python3 scripts/check-worst-buffer-corner.py
```

The retry utility accepts `--early` to record an independent diagnostic without overwriting the main summary, and `--trap`, `--op` or `--gmin` for explicitly recorded solver alternatives. These options are numerical investigations, not process-corner changes. Do not treat an incomplete full-chain run as qualified merely because a different solver configuration or a standalone stage converges.

## Final conclusion for this screening run

**23/24 original-step cases completed and passed.** The cold slow-process case remains inconclusive after all four numerical retry configurations. A simulation abort is not evidence of a fabricated-device failure, but it cannot count as a pass.

The completed hot mixed-process refinement (`fs`, 125 °C) gives **0.967 mV** sampling error at a 0.1 µs step and relative tolerance 5e-5. Sampled voltages changed by **0.0836 mV** from the original run, larger than the remaining 0.0331 mV margin to the screen limit. A further 0.05 µs / 1e-5 run aborted numerically at about 5.98 ms. Therefore comfortable hot-corner margin is **not established**.

Before buffer layout, investigate the idle-state numerical failure and increase sampling margin—then rerun the affected checks. This report does not approve the buffer for layout or fabrication. The finer diagnostic can be reproduced with `scripts/refine-buffer-margin.py`; its failure result is preserved explicitly in the JSON.
