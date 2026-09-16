# Step 1 — transistor column bias

The extracted 20 µm 3×3 array now drives three GF180 `nfet_03v3` current sinks, sharing a diode-connected reference transistor. All four bias devices use W/L = 2 µm / 2 µm. Their diffusion geometry is assumed, not extracted. An ideal current source from VDD supplies the reference; designing that reference is still outstanding.

Connections: each sink has drain at its column, gate at BIAS, source and bulk at ground. The reference has gate and drain at BIAS, source and bulk at ground. Each column retains its 1 pF external load. The extracted array itself is unchanged.

## Nominal results

| Load | 80 pA signal | 240 pA signal | Mean VDD power |
|---|---:|---:|---:|
| 1 MΩ resistor | 175.63 mV | 512.22 mV | See JSON |
| 0.25 µA reference | 186.31 mV | 548.48 mV | 0.983 µW |
| 0.5 µA reference | 185.99 mV | 547.43 mV | 1.956 µW |
| 1 µA reference | 185.47 mV | 545.80 mV | 3.902 µW |

Signals are dark-subtracted samples from row 0 in frame 3. All nine outputs preserve brightness ordering. At 0.5 µA reference, sampled sink currents range from 0.495 to 0.504 µA, with sampled column voltages from about 0.439 to 0.989 V. Bias voltage is about 0.710 V.

**Provisional next-stage setting: 0.5 µA.** This leaves both lower- and higher-current alternatives available during mux testing; it is not an optimized operating point. Increasing current shifts the output voltage downward and increases power, with little signal improvement here. The 0.25 µA option remains promising for lower power.

Power is averaged over frame 3, includes the always-on reference branch, and excludes ideal row/reset driver supplies. Rows are selected for only 180 µs of each 3 ms frame; this average must not be used as a continuous-readout power estimate.

The dark output changes about 0.654 mV between 25 and 50 µs after selection at the 0.5 µA setting. Illuminated outputs continue integrating, so their larger late-window change is not a settling error. The plotted transient shows switching behavior; a specified ADC accuracy and an appropriate fixed-input test are needed to establish formal settling time. Brief negative column excursions of about 1.8 mV occur at switching edges in this model.

## Scope and reproduction

Typical process corner, 27 °C, three frames, 3.3 V supply and 2 V reset. No mismatch, noise, temperature/corner sweep, current-reference startup, physical bias layout or actual ADC input model. The prior array DRC/LVS results do not cover these new transistors.

```bash
bash scripts/run-tools.sh python3 scripts/column-bias.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The saved extracted netlist is tracked, so this sweep does not require rerunning extraction. Generated testbenches and full waveforms are under `build/column-bias`; summary metrics and source hashes are in [column-bias.json](../simulations/column-bias.json). The comparison is embedded in [the HTML notebook](overview.html#column-bias).

Next: add the column multiplexer and measure switching disturbance and sampling delay. Keep the output buffer and ADC loading as subsequent stages.
