# Pad verification configuration and supply-clamp candidate

## Resolving the CUP findings

The earlier full-deck run reported 87 CUP.3 markers in the original library pad. The pad geometry is unchanged. The current wafer.space [precheck source](https://github.com/wafer-space/gf180mcu-precheck/blob/main/precheck.py) and [project-template configuration](https://github.com/wafer-space/gf180mcu-project-template/blob/main/librelane/config.yaml) both select:

```
all,-antenna,-density,-cup
```

They run density and antenna separately. Applying that selection to the existing interface using our installed deck gives zero main-DRC violations, zero density violations, and zero antenna violations. The original unfiltered report remains intact with 87 CUP.3 markers. This resolves the development-flow discrepancy; it does not demonstrate that CUP.3 itself passed or approve a bonding process.

This is **not a full wafer.space precheck**: the small interface coupon is not a complete slot-sized die and has not passed die-size, ID, pad-mask, or other whole-chip submission checks. The downloaded source snapshots and hashes are in `checkpoints/pad-closure/references/`. The deployed shuttle's PDK and configuration must be rechecked at submission time.

## Proposed supply arrangement

Use one foundry `gf180mcu_fd_io__dvdd` and one `gf180mcu_fd_io__dvss` as the first analog-domain supply-pad pair. Tie their core/IO stripes into the same 3.3 V AVDD and AVSS domain used by the analog pads and local protection. `circuits/sensor-supply-pads.spice` specifies the exact electrical connections. A complete ring may need more supply pads and corners; each additional clamp changes startup current and rail capacitance.

This is an electrical candidate, not a newly routed pair or a completed ring. It does not route a 5 V supply into the sensor. The [foundry supply-pad documentation](https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/power.html) describes clamps inside supply and corner pads. The published library operating conditions and ESD data do not, by themselves, qualify this application to a 3.3 V thin-oxide sensor.

The pinned OCD split-voltage references at commit `6e0e354a78793339a4a004a6d9c08990d0eee3e4` include separate core-supply pads, but their clamp schematic still uses `nfet_06v0`/`pfet_06v0`. The analog pad steers to DVDD/DVSS. Merely selecting that library is not evidence of a lower, thin-oxide-safe protection voltage. Snapshots of these schematics are retained as references, not installed into the PDK.

## Simulator compatibility

The unmodified supply-pad model initially failed because its total multi-finger width exceeded the model's bin range. The documented width-per-finger behavior is enabled using a local `.spiceinit`:

```
set ngbehavior=hsa
set wnflag=1
```

The [ngspice manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) describes using W/nf for bin selection in HSPICE compatibility mode. The 120 µm/two-finger PMOS selects at 60 µm; the 4 mm/80-finger NMOS selects at 50 µm. No transistor widths, multiplicities or PDK files were changed to bypass the error. The failed original deck/log are preserved.

## Evaluated scope

- 324 DC conditions: three resistor sections × three MOS-capacitor sections × three diode sections × four temperatures × three supplies (3.0, 3.3, 3.6 V).
- The high-voltage MOS model section is typical. These passive-device sweeps are not a complete high-voltage MOS process-corner qualification.
- 24 ideal-voltage ramp tests: 10 ns, 1 µs, 100 µs and 1 ms nominal-condition ramps plus selected passive-corner/temperature endpoints. Peak supply current includes capacitor charging and clamp conduction. An ideal source can supply unrealistic current; its peak is a diagnostic, not a hardware rating.
- 18 finite-source tests: 0.5/5 Ω upstream impedance, 100 nF decoupling, a 33 kΩ representative load, three temperatures and three ramp times, with res_ss/moscap_ss/diode_ff. This is not a selected regulator model or an extracted package.
- Matched imaging controls with and without the pair at nominal and hot conditions. Both use the same HSPICE compatibility settings, physical local protection model, extracted sensor and finite-transition ADC model. The supply ramp is 1 ms with 200 µs reset hold afterward. Their rails are ideal; finite-source behavior is checked separately.

The fast-ramp clamp response makes the earlier 1 µs ideal sensor-supply ramp an unsuitable board-design assumption for this pair. A 1 ms soft-start is the candidate evaluated here, not a measured minimum ramp time. Retain the post-ramp reset hold; actual power-good timing should follow the board rail.

## Numerical follow-up and power-up results

The strict finite-source run completed 10/18 cases; eight hit numerical failures. The original logs and partial waveforms are retained. Repeating the same circuits with `abstol=1e-12 reltol=1e-4` completed all 18, with all rails settled after the 200 µs wait. This tolerance setting is for the board-supply sensitivity test, not the DC leakage measurement. In the ten cases completed by both settings, final rail voltages agree at the saved precision. The largest peak-current difference is 41.6 µA on an approximately 0.324 A fast-ramp peak (about 0.013%).

All six 1 ms finite-source cases kept the main clamp gate below 0.188 V. Maximum source current was 0.4302 mA, including decoupling-capacitor charging and the representative load; maximum source-to-rail drop was 2.151 mV. Fast-ramp cases can still activate the clamp strongly even though they eventually settle: the 1 µs runs show up to 1.631 V source-to-rail drop with the specified finite impedance. A startup-settlement pass does not make a fast ramp a good board choice.

The original camera-plus-clamp scans reached their 600 s limit; matched controls passed. The follow-up uses identical adjusted settings in both variants (`abstol=1e-13 reltol=1e-4`), with separate output directories. The generated HTML and JSON report the completed results and retain failures. The absolute-current tolerance is 0.1 pA for this comparison, versus 1 pA in the separate supply test. No failures are treated as passes. A separate charge-tolerance experiment retains the original current/relative tolerances and changes only `chgtol` from 1e-16 to 1e-14 C. Finally, a bounded first-frame comparison retains all original numerical settings but measures the first complete nine-pixel scan. That test does not replace the three-frame repeatability check; all attempts are archived separately.

## First-frame sampling result

All four first-frame scans passed: nominal 27°C/3.3 V and hot 125°C/3.0 V, each with and without the clamp pair. Worst sampling error with the pair was 0.16035 mV nominal and 0.22053 mV hot, below the existing 0.5 mV screen. Brightness ordering and startup-reference checks passed. Maximum matched output difference was 0.380 µV. Rails are ideal in these camera comparisons, so this does not include supply-impedance coupling.

The longer coupled transient remains an open numerical verification item. A successful first frame must not be presented as a three-frame repeatability pass.

## Remaining qualification

Normal-voltage SPICE simulations cannot establish HBM/CDM protection, pulse heating/current capacity, package overshoot or thin-oxide survival. The remaining ESD question is the allowable transient voltage at the protected core devices for the chosen clamp, rail layout, assembly and target ESD stress. Resolve that using the accepted library/foundry guidance and qualified stress characterization; do not label the camera ESD-qualified based on these results.

## Reproduce

```sh
bash scripts/run-tools.sh bash scripts/check-pad-wafer-space.sh
bash scripts/run-tools.sh python3 scripts/evaluate-supply-clamps.py
bash scripts/run-tools.sh python3 scripts/check-clamp-supply.py
bash scripts/run-tools.sh python3 scripts/check-clamp-supply-practical.py
bash scripts/run-tools.sh python3 scripts/check-clamp-imaging.py
bash scripts/run-tools.sh python3 scripts/check-clamp-imaging-practical.py
bash scripts/run-tools.sh python3 scripts/check-clamp-imaging-charge.py
bash scripts/run-tools.sh python3 scripts/check-clamp-imaging-one-frame.py
bash scripts/run-tools.sh python3 scripts/report-pad-closure.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The script/checkpoint names distinguish the interface's published-rule-selection checks from earlier full-deck results. Generated decks, logs, waveforms and report inputs are archived with SHA-256 hashes. No earlier sensor or pad GDS is modified by this step.
