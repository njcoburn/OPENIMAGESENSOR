# Final filled 3×3: normal-operation simulation candidate

**Latest — 2026-09-24:** Three consecutive full-camera frames and matching DC readout references are complete. [Current results and scope](three-frames.md). Earlier results below remain historical.

**Latest follow-up — 2026-09-21:** The full extracted candidate completes all nine samples after an electrically equivalent reset-source rewrite. The 1 µs maximum-step rerun also completes all nine samples; maximum difference from 5 µs is 2.778 µV. [Current staged/full-frame evidence](staged-integration.md). The older run descriptions below are retained as history; remaining gates are in the current report.

Updated 2026-09-19 13:46 PDT.

**2026-09-20 follow-up:** the unchanged KLU/trapezoidal candidate completes a streamed diagnostic through **3.24 ms**, crossing the previously reported second-row turn-off stall in about 19.5 minutes. Six samples and the retained capacitor ranges are checked; a complete frame remains unverified. See [switching diagnostics and exact evidence](functional-camera-diagnostic.md). Historical full-frame attempts below retain their original stop classifications.

The stock-model DC operating point completes with every final-chip device and the condensed wiring capacitance retained. Initial voltage guesses (`.nodeset`, released during the DC solve) resolve floating unused-pad initialization. No external resistor or device was added to the chip model.

- Settled supply: 3.299839 V.
- Supply current: 80.401 µA.
- All 16 MOS-capacitor terminal pairs settle near 3.30 V.

For the transient candidate, 1,680 nonlinear MOS capacitors are replaced by their capacitance at that measured bias. The typical foundry equation is `C(V) = area × (0.001107 + 0.00107 tanh(6.25 V − 4.1875))`. Every other netlist record is preserved. This approximation must remain valid throughout the run; it is not suitable for a supply ramp.

## Historical run: frame-5000ns-gear

Completed: **False**. Integration: gear. Maximum timestep: 5000 ns; ngspice also uses smaller adaptive steps. Typical process, 27 °C, constant 3.3 V source with 2 Ω series resistance. Three illumination levels: 0, 80 and 240 pA. External load: bond model, 100 Ω isolation, 100 pF board capacitance, 1 MΩ input and 20 pF sampled capacitor.

Run stopped: Stopped after persistent time stagnation near 3.17001 ms at row 1 select rise; no completed waveform and no qualification pass. No frame result accepted.

## Scope and next steps

This is a nominal **functional candidate**, not complete-chip electrical qualification. The earlier startup gate remains failed; no signoff threshold has been relaxed. The 100 ns preliminary frame was deliberately stopped after its measured runtime projected beyond the watchdog; its saved result is not a solver-convergence failure. The 5 µs trapezoidal run was stopped after persistent time stagnation at the second row turn-off (about 3.23002 ms). Gear integration is a controlled numerical comparison with unchanged device models and tolerances; it still needs timestep refinement.

1. First isolate the row-switching stagnation with a short, incrementally saved transient and matched circuit controls. Neither trap nor Gear has completed this frame, so no capacitor-range or imaging pass is claimed. Once a frame completes, refine the timestep and compare all nine held voltages; run three repeated frames and measure frame-to-frame stability.
2. Establish a matched DC transfer reference for settling error, then check load and process/voltage/temperature variations. Recompute and validate the MOS-cap approximation at each bias/corner.
3. Resolve the nonlinear protection/startup model separately; retain the stock pad geometry and devices.
4. Complete distributed wiring-resistance qualification and the board/ADC-specific conversion sequence. The fast sample fixture is not an ADS1115 model.

## Reproduction

```sh
python3 scripts/prepare-functional-pad-model.py
bash scripts/run-tools.sh python3 scripts/simulate-functional-camera.py op
python3 scripts/freeze-functional-pad-model.py
bash scripts/run-tools.sh python3 scripts/simulate-functional-camera.py frame --step-ns 5000 --method gear
bash scripts/run-tools.sh python3 scripts/analyze-functional-camera.py frame-5000ns-gear
python3 scripts/report-functional-camera.py frame-5000ns-gear
```

Runs refuse to overwrite existing result files. Restore the final filled capacitance extraction first; see the preceding electrical checkpoints. The evidence archive includes decks, waveforms, logs, node aliases, stock OP and capacitor replacement provenance.
