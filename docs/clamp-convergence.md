# Full camera-plus-clamp transient verification

## Working direct-connection configuration

The nominal (27°C, 3.3 V) and hot (125°C, 3.0 V, diode_ff) camera-plus-clamp simulations now complete three full frames. The sensor, physical local protection, foundry clamp models, ADC loads and supply connections are unchanged.

The production configuration uses:

```spice
.options gmin=1e-17 abstol=1e-12 reltol=5e-5 chgtol=1e-16 trtol=3 method=gear
```

Use a 100 ns transient step, a 1 ms supply ramp and a 200 µs post-ramp reset hold. The coarse-run watchdog is 1200 seconds instead of 600 seconds. The completed direct runs took approximately 786 seconds nominal and 834 seconds hot in this session. Runtime depends on the machine and concurrent work; exceeding a watchdog remains a failed/incomplete run.

The [ngspice manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) defines ABSTOL as the absolute current-error tolerance and gives 1 pA as its default. At the previous 10 fA setting, this combined circuit exhibited very slow numerical convergence around switching events. The validated setup changes both current tolerance and runtime allowance; these experiments do not establish that either change alone is necessary. A shorter time limit also hid the distinction between a slow run and a run that could complete. The diagnosis is based on controlled experiments, not an identified simulator source-code defect.

Using the simulator default alone is not evidence of accuracy. We check all 27 samples, repeatability, a finer timestep, and agreement with independent strict-tolerance results. The raw semiconductor models, GDS and extracted RC values were not adjusted to obtain a pass.

## Checks and acceptance limits

The generated [HTML section](overview.html#clamp-convergence) and [machine-readable summary](../simulations/clamp-convergence-verification.json) contain the final comparison table and plots.

- Three frames, nine samples in each; no first-frame substitution for a full run.
- Sampling and tracking error below the existing **0.5 mV** limit, relative to the DC transfer curve at the actual column input.
- Correct dark/medium/bright ordering in every row and frame.
- Startup reference deviation below **1%**.
- Frame-two to frame-three output change below an explicit **50 µV** screen. The completed coarse direct runs measured 0.21 µV nominal and 0.31 µV hot.
- Maximum sample/held-voltage difference below **10 µV** for numerical convergence comparisons.
- Finer independent check: 50 ns with the original 10 fA current tolerance and tighter relative tolerance of 1e-5. An additional direct 50 ns experiment was stopped unfinished after this stronger cross-check passed; it supplies no pass or fail verdict.

Earlier strict no-clamp waveforms are a valid output reference for these ideal-rail cases: an ideal voltage source fixes the rail regardless of the additional clamp current. This reference argument does not apply to a finite-impedance board supply.

## Independent strict-tolerance formulation

The following testbench-only interface makes the clamp connection algebraically explicit:

```spice
Eclamp CLAMPDRIVE 0 VDD 0 1
Vclamp CLAMPDRIVE CLAMPRAIL 0
Fclamp VDD 0 Vclamp 1
Xsupply CLAMPRAIL 0 sensor_supply_pads
```

`Eclamp` enforces the same clamp voltage as VDD. The zero-volt source measures clamp current; `Fclamp` draws that same current from VDD. The interface therefore satisfies `Vout = Vin` and `Iin = Iout`. The controlled sources exchange equal and opposite power. It is a rearrangement of the numerical equations, not a proposed silicon buffer.

The full nonlinear clamp pair remains present. The nominal and hot runs of this formulation complete at the original **10 fA** absolute-current tolerance. The strict hot refinement additionally uses a 50 ns step and `reltol=1e-5`, and records the rail voltages and interface currents. Transient comparison bounds account for the saved waveform precision. Production runs use the original direct connection.

The finite-source port diagnostic compares DC and complex AC loading from 1 Hz to 1 GHz. At 1 Ω, the two formulations agree within a mixed **1 pA + 10 ppm** current comparison. At 1 kΩ, numerical differences reach a few picoamperes and exceed that deliberately strict screen. The initial relative-only criterion also failed at tiny currents. These failures are retained and reported; this diagnostic is not an ESD/leakage qualification or a reason to replace the direct model.

## Reproduce

Use the existing pinned tools image and restored sensor/pad checkpoints described in [the pad checkpoint notes](pad-closure.md).

```sh
# Production: nominal and hot, original direct supply-pad connection.
bash scripts/run-tools.sh python3 scripts/simulate-clamp-frames.py

# Independent formulation, original strict current tolerance.
bash scripts/run-tools.sh python3 scripts/simulate-clamp-frames.py --adapter
bash scripts/run-tools.sh python3 scripts/simulate-clamp-frames.py \
  --adapter --condition hot --step-us .05 --monitor

bash scripts/run-tools.sh python3 scripts/report-clamp-convergence.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Successful runs are reused only when the generated deck and model fingerprint match. A completed diagnostic can seed a run only after exact deck comparison apart from output paths. Failed/partial runs never seed a successful cache entry.

`diagnose-clamp-transient.py` retains the unsuccessful solver, initialization, iteration, integration, current-tolerance and supply experiments. `check-clamp-interface.py` is an additional numerical diagnostic; it intentionally returns a failing screen when the stringent 1 kΩ comparison is not met. It is separate from the production verification commands above.

## Scope and continuation

This resolves the tested nominal/hot multi-frame imaging simulation. It does not establish full MOS process-corner coverage, optical response, ESD stress survival or whole-chip signoff. The high-voltage MOS model section remains typical, and the ADC is still a generic load.

The next model should couple the camera to a finite board supply/regulator and then incorporate the complete pad-ring extraction. The established 1 ms soft-start and post-ramp reset hold remain the starting assumptions. Existing layout hashes and prior failed evidence remain part of the checkpoint.
