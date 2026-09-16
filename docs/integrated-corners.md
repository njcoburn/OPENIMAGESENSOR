# Connected-layout process and temperature matrix

This extends the three selected checks in the [connected-layout checkpoint](integrated-layout.md) to the agreed 24-case matrix. The physical layout and extracted RC model are unchanged.

## Results

**24/24 cases pass.** Worst HOLD error is **0.20656 mV**, at typical MOS / fast diode / 125 °C, against the 0.5 mV screen. The finer-step run gives **0.20633 mV**; maximum sampled-voltage change is **0.00099 mV**. The cold slow-process refinement changes sampled voltage by **0.00022 mV**. Moving the conserved BIAS/OUT shunts at the worst corner changes sampled voltage by **0.00002 mV** and leaves its passing conclusion unchanged.

Maximum sampled-output change from the corresponding separate-block model is **33.49 mV**, at typical MOS / fast diode / −40 °C. Mean VDD power ranges from **266.00 to 266.65 µW** under the simulated load and ideal references; external timing-driver and ADC power are excluded. These deterministic results do not establish manufacturing yield or optical performance.

## Matrix and acceptance screen

- MOS sections: `typical`, `ff`, `ss`, `fs`, `sf`, each at −40, 27, 85 and 125 °C with `diode_typical` (20 cases).
- Typical MOS with `diode_ff` and `diode_ss` at −40 and 125 °C (four cases).
- A passing case completes the three-frame transient and loaded DC transfer, preserves brightness ordering across all nine pixels, and has both ADC-input and sampling-capacitor tracking errors below **0.5 mV**.
- Cold `ss` and the largest-error condition receive a 0.05 µs / 1e-5 relative-tolerance check. The largest-error condition also receives the alternate BIAS/OUT shunt-placement check.

The ordinary step is 0.1 µs with relative tolerance 5e-5. The reference currents remain ideal at 40 µA for the buffer and 0.5 µA for the column-bias mirror. Startup resets all rows for 20 µs, followed by the established rolling-reset/readout sequence. The external load remains 100 pF board capacitance plus a switched 20 pF sampling capacitor with 5 µs acquisition.

## What these numbers mean

Tracking error is measured against the same corner's loaded DC transfer, with all rows selected, resets asserted and the mux disabled for that calibration only. The imaging transient uses rolling selection. Static DC calibration loading can differ from active readout.

Absolute sampled-output changes relative to the separately extracted blocks are reported independently. The earlier connected-layout checks showed a brightness-dependent shift; low tracking error does not remove the need for calibration.

The raw extraction's negative local BIAS/OUT shunts are handled by conserving each signed net-to-ground capacitance sum at its port. This remains a placement approximation, with an alternate placement tested separately. The earlier device-only and C-only controls remain incomplete at the ideal sampling-switch transition; completing the physical RC matrix does not resolve those diagnostics.

Wire R/C, 3.3 V supply, reference currents, photocurrents and external load stay fixed while device model sections and temperature change. This is not a full MOS×diode×interconnect cross-product, supply-voltage sweep, real bias startup test, noise/mismatch analysis, real ADC qualification or optical characterization. Existing DRC/LVS results apply to the unchanged GDS; no new physical verification run is needed for these simulation-only changes.

## Reproduce and audit

```bash
bash scripts/run-tools.sh python3 scripts/integrated-corners.py
bash scripts/run-tools.sh python3 scripts/check-integrated-corners.py
bash scripts/run-tools.sh python3 scripts/report-integrated-corners.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Start with the [connected-layout build/extraction instructions](integrated-layout.md) if the generated `build/integrated-pex/` models are absent. The runner checks the GDS hash and extracted-device LVS result, and records model/source hashes. Matching successful ngspice decks are cached; the matrix summary is saved after each completed worker.

Results are in [`simulations/integrated-corners.json`](../simulations/integrated-corners.json), the [notebook](overview.html#integrated-corners), and `docs/assets/integrated-corners.png`. Case decks, logs and summaries are archived in `checkpoints/integrated/corners-evidence.tar.gz`, with a SHA-256 manifest. Full waveform files remain under `build/integrated-pex/sim/`.

Next: replace ideal bias/reference interfaces with physical circuits or specified external reference inputs, plan pad/ESD connections, and check startup and supply sensitivity before finalizing ADC timing.
