# Shared output buffer — first candidate

The mux's low input range motivates a PMOS source follower: drain to ground, gate to OUT, source to BUF and bulk to VDD. A PMOS current mirror supplies its source. The mirror reference is an ideal external sink. This shifts the output upward and has non-unity, nonlinear gain; it is not a precision unity-gain amplifier.

The follower uses GF180 `pfet_03v3`, W/L = 20/0.5 µm. The mirror reference and load use 20/2 µm. All three use explicit assumed diffusion geometry and have not been physically laid out. See [output-buffer.spice](../circuits/output-buffer.spice).

## Load experiments

The generic path is BUF → 1 Ω plus 5 nH → PAD (5 pF to ground) → 100 Ω → ADCIN. ADCIN has a 1 MΩ DC load and 100 pF or 1 nF capacitance. These are assumed board/package loads, not measured parameters or a model of a chosen ADC.

The sampled-load test adds 20 pF behind a 100 Ω ideal switch. That capacitor is reset before each acquisition, creating a deliberately demanding charge-transfer event. Control edges are 10 ns. The first test uses 1 µs acquisition; the follow-up uses 5 µs, both ending at the existing 10 µs sampling point inside each 16 µs selection. A real ADC's specified input circuit and timing must eventually replace this approximation.

Tracking error is ADCIN minus the *loaded DC transfer value at the instantaneous mux input*. It excludes the intended follower voltage shift, but includes lag and sampling-load disturbance. This is not an ADC bit-accuracy specification. Optical exposure continues during readout.

## Initial findings

- 20 µA with a static 100 pF load: about 0.182 mV worst error at 10 µs.
- 5 µA with 100 pF: about 148 mV error; too slow at this timing.
- 20 µA with 1 nF: about 268 mV error; too slow at this timing.
- 20 µA with a reset 20 pF sampler and 1 µs acquisition: about 218 mV error. Static capacitive-load success does not establish ADC-drive capability.

**Starting candidate: 20 µA reference, 100 pF board load, and 5 µs acquisition.** The nominal worst tracking error is about 0.204 mV. Use a 1 mV engineering screening limit here, not an ADC accuracy claim. The output is level-shifted to approximately 1.83–2.26 V and total VDD power is about 134 µW. The notebook records the numerical-refinement result and sampling-capacitor error. The 1 nF load and 1 µs acquisition are outside this candidate’s demonstrated operating conditions.

## Reproduce

```bash
bash scripts/run-tools.sh python3 scripts/output-buffer.py
bash scripts/run-tools.sh python3 scripts/check-buffer-acquisition.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Results: [output-buffer.json](../simulations/output-buffer.json). Full generated testbenches, DC sweeps and waveforms: `build/output-buffer/`. Summary plots are embedded in [the notebook](overview.html#output-buffer).

The array and readout use their saved extracted models, including the documented BIAS-shunt approximation. Inter-block connections and buffer wiring are ideal. This is typical-corner electrical simulation only: no noise, mismatch, process/temperature sweep, realistic reference generation, pad/ESD design, optical calibration or buffer layout verification. Mean VDD power includes the ideal reference branches but excludes reset/control driver power.
