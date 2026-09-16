# Coupled camera and board supply

This step replaces the ideal VDD connection with an assumed passive board network:

```text
upstream ramp ── Rsource ── 2 nH ── VDD ── extracted camera and supply clamps
                                    │
                                  0.1 Ω
                                    │
                                   1 nH
                                    │
                                  100 nF
                                    │
                              ideal common ground
```

Nominal (27°C, 3.3 V) and hot (125°C, 3.0 V, diode_ff) use 0.5 Ω source resistance. A hot 5 Ω case tests sensitivity to a weaker supply. These are explicit engineering assumptions; no selected regulator or measured board is represented. The upstream ramp remains 1 ms, followed by 200 µs reset hold. The full nonlinear supply clamps stay connected directly to the die rail.

The runner reuses the qualified three-frame simulation and evaluates all 27 samples. DC transfer references include the same supply network. Rail extrema use all saved points, and sample changes relative to the ideal-supply baseline are reported separately. The passive network also applies during the DC sweep. Existing external reset supply and control-source assumptions remain in place; ground bounce and controller supply coupling are not included.

## Reproduce

```sh
bash scripts/run-tools.sh python3 scripts/simulate-board-supply.py
bash scripts/run-tools.sh python3 scripts/simulate-board-supply.py --case hot --step-us .05 --timeout 2400
bash scripts/run-tools.sh python3 scripts/report-board-supply.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The first command uses two workers and a 1800-second watchdog per ngspice invocation. Use `--case nominal`, `--case hot`, or `--case hot_stress` to run one case. A successful unchanged deck/model fingerprint can reuse its saved waveform. Failed or unfinished cases are preserved and cannot seed successful cache entries.

Results: `simulations/board-supply.json`; raw decks, waves, and logs: `build/clamp-frames/board_*`; shareable plots and tables: `overview.html#board-supply`. The checkpoint archive includes this step's scripts and raw results and identifies the preceding clamp-convergence archive for model dependencies.

## Screens and limitations

- Sampling and tracking error below 0.5 mV versus the board-network DC reference.
- Correct brightness ordering in each row of all three frames.
- Startup bias deviation below 1%, as in the prior test.
- Rail error below 1% during the final startup hold and imaging; this is a declared engineering budget, not a foundry limit.
- Frame-two to frame-three output change below 50 µV.
- Output differences versus ideal rails are reported, not hidden by the supply-aware transfer reference.

The previously qualified numerical setup is 1 pA absolute current tolerance, relative tolerance 5e-5, Gear integration, and 100 ns step. That prior accuracy check used ideal rails; it does not by itself establish convergence of the new finite-supply network. The additional hot run uses 50 ns and relative tolerance 1e-5; the report compares all 27 output and held samples against a declared 10 µV numerical-agreement screen. Rail extrema can remain more sensitive to unresolved fast edges than sampled pixel outputs; this comparison is not package-level ringing signoff.

Only typical MOS is covered here. This is not complete PVT, a package model, pad-ring extraction, regulator-loop stability, or ESD qualification. The inherited runner's power field uses die voltage and source current; with stored energy in the new network it should not be interpreted as instantaneous die power. Next work is a selected board regulator/package model and the physical pad-ring supply/ground interconnect.
