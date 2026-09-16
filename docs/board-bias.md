# Physical bias interface: two external resistors

This checkpoint replaces both ideal reference-current sources with board resistors and the diode-connected MOS reference devices already present in the extracted sensor. It is a buildable bias interface, not a regulated on-chip current reference. The sensor GDS has not changed.

| Connection | Nominal component | Purpose |
|---|---:|---|
| VDD → BIAS | 5.1 MΩ resistor | Supplies the existing NMOS column-bias reference |
| PREF → ground | 49.9 kΩ resistor | Loads the existing PMOS buffer reference |
| BIAS and PREF → ground | 5 pF each, modeled | Assumed pad/trace capacitance; not a selected capacitor or extracted pad model |

The nominal extracted-core voltages with the old ideal currents were approximately 0.710 V at BIAS and 1.989 V at PREF. Ohm's law gives about 5.18 MΩ and 49.73 kΩ for the original 0.5 µA and 40 µA targets; the chosen nominal resistor values are nearby standard values. The new nominal DC currents are approximately **0.508 µA** and **39.88 µA**.

The on-chip reference transistors turn those resistor currents into gate biases for their existing mirrors. The resistors provide a path away from zero current as supply rises. There is no separate self-biased loop or startup transistor in this candidate. Current depends on supply, transistor characteristics and resistor value, so it must not be described as temperature-compensated or precision-regulated.

## Checks

- **84 DC cases:** five MOS corners × four temperatures × three supplies (60); fast/slow diode endpoints with typical MOS at three supplies (12); independent ±1% resistor-value combinations at nominal, cold/low-supply and hot/high-supply selected conditions (12).
- Supplies: 3.0, 3.3 and 3.6 V. Temperatures: −40, 27, 85 and 125 °C.
- All DC cases converge. Column reference spans **0.412–0.610 µA**; buffer reference spans **31.76–48.37 µA** across the tested combinations. The tolerance cases are selected checks, not a full tolerance × PVT cross-product. Resistor temperature coefficient is not modeled.
- **18 selected power-up/imaging cases:** nominal supply sweep, the previous hot fast-diode cases, a hot mixed-process/low-supply case, measured current extremes including resistor tolerance, 1/100/1000 µs ramps, and a 50 pF per-bias-pin capacitance sensitivity case.
- Acceptance remains correct nine-pixel brightness ordering and both ADC-input and HOLD tracking errors below 0.5 mV. Bias currents must also be within 1% of their steady values during the last 10 µs before the controller starts its scan sequence.

**All 18 selected cases pass.** Worst HOLD error is **0.21595 mV**, at typical MOS / fast diode / 125 °C and 3.0 V. Simulated reference-current deviation at the end of the startup wait is below **0.001%** in every case. Mean VDD power spans **191.99–351.88 µW** across the selected runs; reset-supply generation, controller and ADC power are excluded.

The PDK specifies a nominal 3.3 V supply for low-voltage devices and discusses 10% overshoot and device terminal-voltage limits. The selected 3.0–3.6 V functional sweep is not a reliability or transient-overshoot signoff. See [GF180 chip operating conditions](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_14_1.html).

## Power-up sequence

1. Ramp VDD from zero. The modeled external 2 V reset supply ramps with it.
2. Hold all pixel resets asserted with their high level tracking VDD; row/mux selects stay low.
3. Wait **200 µs after the supply ramp finishes** before beginning the existing timing sequence. Its first 20 µs all-row reset is retained.
4. Run the established rolling reset/readout and 5 µs ADC acquisition. Results use the third frame.

The delay is an external-controller requirement in these tests, not implemented power-on-reset hardware or a proven minimum wait. Illumination remains active during startup. No supply brownout, arbitrary sequencing or incomplete power-down restart has been qualified.

DC tracking calibration uses the same resistor-biased model and supply, all rows selected, reset asserted and mux disabled. Only calibration uses all-row selection; imaging uses rolling selection. The simulated power uses actual VDD(t) × supply current, rather than assuming 3.3 V at every supply setting.

## Scope and remaining work

`circuits/board-bias.spice` is the simulated interface; `xschem/board_bias.sch` shows its nominal connections. The existing 37-MOS/nine-diode core remains extracted and DRC/LVS-clean. Existing BIAS/OUT extraction approximations still apply.

This is not yet a manufactured board or a new on-chip reference layout. VRESET, supply regulation, controller outputs and the ADC sampling model remain idealized. Actual resistor temperature coefficient/noise, pad and ESD leakage, bias-pin leakage, package coupling, mismatch, and supply noise remain unmodeled. In particular, the roughly 0.5 µA column reference needs a leakage budget when pads/ESD are added. A real ADC and PCB parts have not been selected.

As a first budget, 1% of the nominal 0.5 µA reference is only 5 nA. This is a proposed leakage allocation to check against the eventual pad/ESD implementation, not a claim about any available pad cell.

## Reproduce

```bash
bash scripts/run-tools.sh python3 scripts/bias-reference.py
bash scripts/run-tools.sh python3 scripts/check-bias-reference.py
bash scripts/run-tools.sh python3 scripts/refine-bias-reference.py
bash scripts/run-tools.sh python3 scripts/report-bias-reference.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

For the graphical connectivity check:

```bash
bash scripts/run-tools.sh xschem -n -q -x --rcfile xschem/xschemrc -o build/bias-reference -N board_bias.spice xschem/board_bias.sch
python3 scripts/check-board-bias.py
```

Summary files are `simulations/bias-reference-dc.json` and `simulations/bias-reference.json`. Full waves/decks/logs are under `build/bias-reference/`; compact evidence is archived under `checkpoints/bias-reference/`. The [HTML notebook](overview.html#bias-reference) contains the connection diagram, curves and per-case table.

Next: budget and simulate actual bias-pin pad/ESD leakage and capacitance, implement the reset/supply interface, then decide whether this externally adjustable bias approach meets the required image stability or a regulated reference is justified.
