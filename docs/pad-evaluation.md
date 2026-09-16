# Analog-pad functional evaluation

This checkpoint evaluates the installed `gf180mcu_fd_io__asig_5p0` on the extracted 3×3 sensor. It does not change its GDS or qualify an ESD pad ring. See the [living report](overview.html#pad-evaluation) for plots and results.

## Reproduce

Run from the repository root using the pinned tools image:

```sh
bash scripts/run-tools.sh python3 scripts/evaluate-pads.py characterize
bash scripts/run-tools.sh python3 scripts/evaluate-pads.py dc
bash scripts/run-tools.sh python3 scripts/evaluate-pads.py pad-only
bash scripts/run-tools.sh python3 scripts/evaluate-pads.py secondary
bash scripts/run-tools.sh python3 scripts/evaluate-pads.py secondary-smooth
bash scripts/run-tools.sh python3 scripts/check-pad-refinements.py
bash scripts/run-tools.sh python3 scripts/report-pad-evaluation.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The runner reuses the previous board-bias/extracted-core simulation engine. The existing extracted core and board-bias prerequisites must be present. Failed ideal-switch simulations are expected evidence, not passing tests. Read status and `screen_pass` in every result JSON; a simulator process exit by itself is not a pass.

## Evaluated topology

The installed pad netlist is copied with its license into `checkpoints/pad-evaluation/analog-pad.spice`. Original library and copied-cell SHA-256 hashes are recorded in `simulations/pad-characterization.json`. Four instances attach to BIAS, PREF, VRESET and BUF. DVDD/VDD connect to the sensor supply, DVSS/VSS to ground for these functional experiments. These connections do not establish that a 5 V library is qualified at 3.3 V or that its protection clamps suit thin-oxide devices.

The secondary candidate places 100 Ω between each package pin and a local diode pair, then connects that node to the core through a zero-volt current meter. Each diode has 12 µm² area and 26 µm perimeter. This is an area/perimeter model candidate; the ideal resistor has neither a poly layout nor process variation. Local diodes connect to the core rails. The original pad, including its rail MOS capacitor, is retained.

Bias-current comparison uses current entering the core after all protection leakage. Transient startup metrics use external resistor currents, following the previous board-bias experiment. Each simulated power-up holds reset until 200 µs after the 1 µs supply ramp; results sample frame three. Independent arbitrary supply sequencing and brownout are outside this checkpoint.

Signal capacitance is a 1 kHz small-signal measurement with ideal supply impedance. The 36 isolated-pad conditions sweep all three diode corners, four temperatures and three supplies, with the MOS capacitor corner fixed typical. Leakage is swept in 10 mV steps from zero to supply. Five representative voltages are used for AC measurements. The 168 core DC cases are two candidates across the previous 84-case resistor-bias matrix. Imaging covers five selected corner/temperature/supply combinations, not the entire DC matrix.

## ADC model distinction

Original instantaneous `SW` elements produce timestep failures with the secondary network. The alternative uses behavioral conductance:

```
g = 1e-12 + (0.01 - 1e-12) * (0.5 + 0.5*tanh((Vcontrol - 1.65)/0.1))
I = g * Vterminal_difference
```

This retains 100 Ω on resistance, 1 TΩ off resistance and existing 10 ns control edges. Two pad-only matched controls quantify the numerical/model change. A hot secondary case is repeated with half the timestep and tighter relative tolerance. Success with this model does not resolve or erase the failed ideal-switch runs, and does not qualify a real ADC.

## Evidence

- `simulations/pad-characterization.json`: isolated-pad leakage and capacitance.
- `simulations/pad-dc.json`: actual core bias currents and differences from the unpadded baseline.
- `simulations/pad-pad-only.json`, `pad-secondary.json`, `pad-secondary-smooth.json`: transient results and failures.
- `simulations/pad-refinements.json`, `pad-evaluation-summary.json`: controls and numerical checks.
- `checkpoints/pad-evaluation/evidence.tar.gz` and `manifest.json`: generated decks, logs, waveforms, source scripts and results with SHA-256 checksums.

The [GF180 analog-pad requirements](https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/analog.html) describe additional secondary protection. Meeting its stated resistor/perimeter starting values is insufficient to claim HBM/CDM performance. Clamp design, return paths, physical current capacity, layout, optical leakage and package effects require further work.
