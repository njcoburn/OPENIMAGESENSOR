# Controlled simulator comparison — 2026-09-19

Question: does the ngspice 47 behavioral-capacitor implementation resolve the stock/extracted pad-corner convergence failure while preserving terminal behavior?

## Fixed experiment

- Build release 46 and 47 in the existing OSIC container with matching GCC `-O2`, KLU, no GUI/readline. Preserve installed tools.
- Use the same stock GF180MCU D model files, typical process, 27 °C, and compatibility init for both.
- First compare the locally resolved standalone capacitor control against an independent terminal ODE and integrated charge; retain 100 pA current/10 µV voltage limits, with a 1e-5 charge-relative screen.
- After controls pass, test the unextracted stock foundry corner macro and then the archived extracted nominal corner coupon. Same supply and load fixture, 25 ns maximum step, reltol=1e-7/abstol=1e-14, trapezoidal/KLU.
- Keep the local helper-normalization candidate separate. It does not automatically gain validity from a stock-model pass.
- Each network run has a 1,200 s wall-clock limit. No retries or automatic tolerance changes. Partial waveforms are diagnostic only.
- If the stock extracted 47 run completes, perform a separate timestep/tolerance refinement before promoting it. No complete-chip, PVT or ESD pass follows from nominal completion.

## Reproduction

Run inside the repo with `scripts/run-tools.sh`; see source archive URLs in the checkpoint report. The build script expects downloaded release tarballs in `build/ngspice-version-comparison`.

```sh
bash scripts/run-tools.sh bash scripts/build-ngspice-comparison.sh
bash scripts/run-tools.sh python3 scripts/compare-ngspice-versions.py prepare
bash scripts/run-tools.sh python3 scripts/compare-ngspice-versions.py control
bash scripts/run-tools.sh python3 scripts/analyze-ngspice-control-comparison.py
bash scripts/run-tools.sh python3 scripts/compare-ngspice-versions.py stock
bash scripts/run-tools.sh python3 scripts/compare-ngspice-versions.py extracted
```

These commands refuse to overwrite existing run results. Archive each experiment before creating another explicitly named comparison.
