# Connected 3×3 sensor layout

The 20 µm photodiode array, seven-NMOS column-bias/multiplexer block and three-PMOS output buffer are now physically connected. The array retains its 80 × 50 µm pixel pitch. Readout sits below the array; the buffer sits to its right. The filled region is approximately 336 × 243 µm. This is an electrical test core, not a pad-equipped die.

## Connections and optical access

Metal 3 trunks and Metal 4 cross-routes connect COL0–2 and the mux output. Shared VDD and ground buses are 2 µm wide. The array uses its existing distribution trunks; the readout and buffer have new supply/ground branches. VRESET, row/reset/select controls, BIAS, PREF and BUF remain top-level terminals for external sources or future circuits. COL0–2 and OUT are also exported as observation terminals, not bond pads.

The nine 20 × 20 µm junctions retain the existing 26 × 26 µm fill exclusion regions. New Metal 4 routes are checked against those regions. No optical efficiency or packaging performance is inferred from this geometric check.

## Verification and extraction

The final filled GDS passes both Magic and the installed full GF180 KLayout DRC deck with zero violations. Netgen finds a unique match to `circuits/integrated.spice`: 34 NMOS, three PMOS and nine photodiodes. This checks the connected design rather than relying on separate block reports.

Magic flattens and extracts the entire filled layout, including inter-block routes. Capacitive-only floating fill is eliminated at zero net charge by a Schur complement; resistors and device terminals remain. Numerical checks cover passivity, symmetry, charge/energy preservation and bounded capacitor truncation.

The integrated extraction has local negative shunts on BIAS and OUT from Magic's capacitance redistribution. The model conserves each affected net's signed capacitance to global ground, placing that total at its port; it retains every resistor and coupling capacitor. This is an explicit placement approximation. A sensitivity model moves those totals to the most resistively distant node on each net. Exact values and audit data are recorded in `reduction.json`.

## Simulation scope

The first connected-layout checks cover nominal conditions, ss / −40 °C, and typical MOS / fast diode / 125 °C, plus a nominal device-only control. These are selected checks, not a repeat of the entire preceding 24-case matrix. They retain the 40 µA buffer reference, 20 µs all-row startup reset and 5 µs acquisition into the generic 100 pF board / 20 pF sampling load.

The subsequent [24-case connected-layout matrix](integrated-corners.md) extends these initial checks without changing the layout.

All three RC conditions pass: maximum HOLD errors are **0.154 mV nominal, 0.138 mV cold and 0.207 mV hot**, below the 0.5 mV screen. Cold/hot finer-step checks change sampled voltage by at most **0.00099 mV**; moving the conserved BIAS/OUT shunts changes it by at most **0.00013 mV** across these three conditions.

Absolute sampled outputs change by up to **26.11 mV nominal** and **32.24 mV hot** relative to the separate-block model. This shift varies with brightness. A nominal sensitivity model retaining all capacitances but reducing every extracted resistor to 10% changes output by only **0.429 mV** relative to full RC. This suggests that the changed capacitance network, including regenerated fill, dominates the larger calibration change; it does not identify individual contributing capacitors.

Tracking error references a loaded DC sweep of the same connected model, with OUT forced, all rows selected, mux selections off and pixel resets on. Shared-supply loading can differ from active readout. Changes in absolute sampled output are reported separately from tracking error. Wire R/C stays nominal across device process/temperature conditions.

The initial all-rows-off cold DC calibration stalled: that setup leaves the column current sinks without normal pixel drive. A one-row-selected calibration also stalled; selecting all rows gives the source followers a DC path and lets the cold sweep converge. This condition is used only for calibration, not for the imaging transient. The device-only transient control stops at the ideal sampling-switch transition (approximately 980.005 µs), including at a 0.05 µs step; it is recorded as incomplete, not a passing electrical control. Extracted-device LVS is independently complete.

The C-only control also stops at the sampling-switch transition. Raising the transient iteration limit and tightening truncation control did not resolve the device-only failure. These unsuccessful diagnostics are retained with the checkpoint; the full-RC and 10%-resistance runs complete.

No pads/ESD, supply ramp, physical reference generator, control logic, real ADC, noise, mismatch, extracted package or optical characterization is included. Those remain separate design and validation work.

## Reproduce

From the repository root:

```bash
bash scripts/run-tools.sh bash scripts/build-integrated.sh
bash scripts/run-tools.sh bash scripts/extract-integrated.sh
bash scripts/run-tools.sh python3 scripts/simulate-integrated.py
bash scripts/run-tools.sh python3 scripts/check-integrated-pex.py
bash scripts/run-tools.sh python3 scripts/report-integrated-pex.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The pinned Docker image and GF180 setup are inherited from `scripts/run-tools.sh`. Saved functional block inputs are in `checkpoints/integrated/`; their hashes and placements are recorded in `placement.json`. Layouts and reports are archived there, with compact extraction models under `pex/`. Generated waveforms remain under `build/integrated-pex/sim/`.

See the [living notebook](overview.html#integrated) and [layout verification data](../simulations/integrated-verification.json).
