# First GF180 electrical simulation

Run from the repository root:

```sh
bash scripts/simulate.sh
bash scripts/run-tools.sh python3 scripts/plot-pixel.py
```

The runner mounts this checkout at /foss/designs in a disposable container,
using the locally verified image ID (override with IIC_OSIC_IMAGE). It does
not alter the existing GUI container's Windows project mount.
Verified with ngspice 46 and the installed gf180mcuD PDK on 2026-09-14.
The installed Xschem is 3.4.8RC. xschem/xschemrc selects the GF180 library;
the graphical schematic is xschem/pixel_3t.sch. The simulate script netlists
that schematic and runs the resulting SPICE deck. pixel_3t.spice is retained
as the original standalone experiment.

The test uses 3.3 V GF180 NMOS models, an ideal 1 uA column current sink,
1 pF column load, and a behavioral photodiode with an assumed 10 fF explicit
capacitance. MOS parasitic capacitances are also present. Row select remains
on for this initial integration experiment. Reset starts asserted and releases
at 11 us. The current sink is ideal; practical bias compliance is not validated.

| Photocurrent | Sense at 20 us | Sense at 1 ms |
| --- | --- | --- |
| 0 | 2.90808 V | 2.90734 V |
| 1 pA | 2.77967 V | 2.70530 V |
| 5 pA | 2.73234 V | 2.36445 V |

Waveforms are exported as pixel_0, pixel_1p, and pixel_5p (time, sense,
column voltage). These generated files are ignored by Git.

## Numerical leakage investigation

The initial dark drop was approximately 373 mV over 20 us to 1 ms.
SPICE's default gmin (minimum junction conductance) of 1e-12 S is significant
on a node driven by picoamp currents. A controlled sweep with tightened
current tolerance produced:

| gmin | Dark drop |
| --- | --- |
| 1e-12 S | 373.4 mV |
| 1e-14 S | 4.94 mV |
| 1e-15 S | 1.17 mV |
| 1e-16 S | 0.78 mV |
| 1e-17 S | 0.74 mV |
| 1e-18 S | 0.74 mV |

See numerics.csv; reproduce with `bash scripts/run-tools.sh python3 scripts/check-numerics.py`.
The current baseline uses gmin=1e-17, abstol=1e-16 A, reltol=1e-5.
The schematic and standalone netlist give the same reported endpoint values.
This sweep establishes sensitivity to gmin, not full convergence for every
solver setting or a physical dark-current prediction.

## Limits and next steps

This is an initial electrical experiment, not a validated sensor design.
No GF180 quantum efficiency or measured photodiode dark current is assumed.
MOS source/drain areas and perimeters are currently zero (model defaults),
so geometry-dependent junction leakage and capacitance remain to be added.
The residual dark drift includes modeled circuit behavior and is not a
measurement of a fabricated diode's dark current.

The initial operating point is calculated with reset asserted, separately
for each photocurrent. This weak NMOS reset produces light-dependent starting
levels. Compare each curve to its own reset level; next use repeated finite
reset/exposure cycles to assess repeatability and reset duration.

Next: realistic diffusion geometry, switched row readout, physical column
bias, and reset timing sweeps before layout.

## Watch in VNC

Open http://localhost:8080/vnc.html?autoconnect=true&resize=scale (password abc123).
Container: openimagesensor-vnc. The repository is mounted at /foss/designs.
Restart with `docker start openimagesensor-vnc`.
Open xschem/pixel_3t.sch with the project xschemrc. The desktop is bound to
localhost; the earlier Windows-project container is separate.

The generated plot is pixel-response.png. Binary ngspice traces are raw_0,
raw_1p, raw_5p. The desktop was opened with the schematic and response plot.

## Repeated reset and selected readout

The next experiment lives in `xschem/pixel_cycles.sch`. Run
`bash scripts/simulate-cycles.sh`, then
`bash scripts/run-tools.sh python3 scripts/build-overview.py`.
See [the HTML notebook](../docs/overview.html) for timing, captured schematic,
waveforms, sample voltages, and model limits.

This test switches the row and substitutes a 1 Mohm passive column load for
the original ideal current sink. It runs four 1 ms cycles from explicit zero
initial sensing/source/column voltages. Reset lasts 20 us; row selection spans
920–980 us; samples are taken at 970 us. Exposure continues during readout.
The bright cases settle quickly, but dark output still rises between cycles;
reset duration and longer runs need investigation. Source/drain geometry,
physical photodiode response, and transistor bias remain unvalidated.

## Reset repeatability study

Twenty cycles compare reset supplies of 3.3, 2.2 and 2.0 V and reset durations
of 20 and 100 us. Reset-to-sample time stays fixed at 950 us. Results are in
repeatability.json, with analysis and plots in the HTML overview. The initial
coarse/fine discrepancy is retained in repeatability-initial.json.

Accepted numerical settings add Gear integration, chgtol=1e-18 C and trtol=1.
The 2.0 V reset candidate's 1-to-0.2 us maximum sample difference is 15.25 uV;
0.2-to-0.05 us differs by 3.84 uV at most. Finest-step final-five-cycle spans
are below 1.3 uV. These are deterministic numerical checks with incomplete
physical junction models, not noise or measured sensor specifications.

A separate graphical candidate is xschem/pixel_reset_candidate.sch. It uses
2.0 V at the reset drain, 3.3 V reset gate pulses and the original 3.3 V
source-follower supply. It trades voltage headroom for stronger reset action.
The candidate schematic agrees with the varied-deck study within 5 uV.

## Physical 3×3 array scan

`xschem/array_3x3.sch` instantiates nine `pixel_physical.sch` cells, matching
`build/array_3x3.gds`. The physical pixel uses GF180 diode models and actual
MOS junction areas/perimeters, with no ideal 10 fF placeholder.
`scripts/simulate-array.py` supplies external synthetic photocurrents to
internal sensing nodes and scans three rows, one selected at a time.
The diode model requires the explicit `diode_typical` library section in
addition to the transistor `typical` section.

The normal pattern is [[0,5,15],[15,0,5],[5,15,0]] pA. Three frames produce
approximately 0.934, 0.769 and 0.454 V for dark, dim and bright readings.
The maximum corresponding frame-2/frame-3 difference is about 1.8 uV in the
deterministic schematic simulation. A prior 50 pA input saturated near ground;
that run is retained in `array-saturation-results.json`.

Results: `array-results.json`; testbench and waveforms:
`build/array-sim/{array_tb.spice,wave.txt,run.log}`. The simulation checks
nonoverlapping row selection and correct ordering for every row.

No ADC, thermal/shot noise, calibrated optical efficiency, extracted routing
or fill parasitics are modeled. Test frame timing is not a validated frame-rate
specification. The next task is parasitic extraction and resimulation.
