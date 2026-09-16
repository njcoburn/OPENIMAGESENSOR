# Revised buffer: startup sequencing and drive margin

## What changed

- Reset **all pixel rows for 20 µs at startup**, then retain the existing rolling-reset timing. This initializes the sensing nodes before the otherwise unreset rows spend milliseconds exposed to photocurrent.
- Increase the ideal buffer-reference current from **20 to 40 µA**, keeping PMOS geometry unchanged.
- Keep the 100 pF board load, 20 pF sampling capacitor and 5 µs acquisition window.
- Do **not** add the tested mux-precharge circuit: it did not resolve the cold failure.

The startup pulse is represented by ideal row-control voltage sources. Actual control logic must implement this behavior. It is not a fabricated reset-controller verification.

## Diagnostic evidence

The isolated buffer completed a 0–0.1 V input sweep at ss/−40 °C with a simple load and with the board/bond-wire model. Removing the bond-wire inductance, readout parasitics or array parasitics individually did not cure the original connected-chain failure. A real NMOS mux-precharge switch holding OUT near 0.8 V also failed at essentially the same time.

At the original failure, two illuminated but not-yet-reset sensing nodes were about −0.40 V relative to their anodes. Adding an all-row startup reset allows the original extracted chain to complete at the same corner at both 20 and 40 µA. This supports the startup sequence as the remedy without claiming to identify the simulator's exact internal failure mechanism. No additional mux-precharge reference is required.

At fs/125 °C with the original startup sequence, increasing reference current from 20 to 30, 40 and 60 µA changes sampled error from about 0.967 to 0.194, 0.179 and 0.145 mV respectively. 40 µA is the revised candidate; actual reference-generation accuracy and drift remain unverified.

## Validation and layout

The revised candidate is tested over the same 24-case matrix: five MOS process sections × four temperatures with the typical diode, plus fast/slow diode endpoints at typical MOS. The screening target is tightened to **0.5 mV** for both output and sampling-capacitor tracking, with correct brightness ordering required. Each case has its own loaded DC transfer reference.

All **24 revised cases pass**, with a largest original-step error of **0.194 mV** and mean VDD power of about **266 µW**.

The cold slow-process case and largest-error revised case are repeated at a 0.05 µs step and 1e-5 relative tolerance. The refined cold and worst-case errors are approximately 0.130 and 0.193 mV; sampled outputs change by at most 0.0052 mV. Results, power and numerical comparisons are in [buffer-hardened-corners.json](../simulations/buffer-hardened-corners.json) and [the notebook](overview.html#buffer-hardening).

A standalone three-PMOS layout matches [the buffer circuit](../circuits/output-buffer.spice). It includes floating density fill and passes Magic DRC, full GF180 KLayout DRC and Netgen LVS. GDS, extracted connectivity and reports are in `checkpoints/output-buffer/`; the GDS hash is recorded in `simulations/buffer-layout-verification.json`.

The layout has not yet been RC-extracted into these simulations or physically joined to the readout. No pad/ESD, output pin/package design, real ADC or optical characterization is implied. Interconnect parasitics and load values remain nominal and references ideal. The original qualified readout BIAS-capacitance approximation is unchanged.

## Reproduce

Run the following within the pinned tools image using `bash scripts/run-tools.sh` before each command:

```bash
python3 scripts/buffer-hardening.py
python3 scripts/buffer-cold-followup.py
python3 scripts/buffer-precharge-test.py
python3 scripts/buffer-startup-diagnostic.py
python3 scripts/buffer-hardened-corners.py
python3 scripts/verify-hardened-buffer.py
bash scripts/build-buffer.sh
python3 scripts/report-buffer-hardening.py
python3 scripts/build-overview.py
```

Generated testbenches, DC curves, full waveforms and logs remain under `build/buffer-hardening/`. Historical test scripts retain the earlier 20 µA candidate; the revised corner script explicitly applies 40 µA and startup reset. Numerical success-cache keys include the generated deck and relevant source hashes. Failed runs retain their logs and do not receive a success marker.

Next: extract the buffer layout, repeat the combined checks, and then integrate readout/buffer routing and pad/ESD circuitry.
