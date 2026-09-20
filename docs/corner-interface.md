# Full-corner numerical interface check

Recorded **2026-09-19 01:32 PDT**. Target: **3×3 demonstrator**.

**DC/AC interface comparison: NOT VERIFIED. Full-corner ramp/load transients: NOT VERIFIED.**

## What changed

Each of the eight corner ports is connected through a testbench-only unity-gain voltage-controlled source, a zero-volt current-sensing source, and a unity-gain current-controlled source. For port p and external node e:

```spice
Ep drive 0 e 0 1
Vp drive p 0
Fp e 0 Vp 1
```

This enforces V(p)=V(e) and returns the measured current to e with the same sign. Port voltage, current, and power are preserved algebraically. It is a numerical reformulation, not an on-chip amplifier. All semiconductor, resistor and capacitor records are retained. The ground-connected ports use the same construction; their external current sources connect ground to ground.

## Checks performed

Direct and adapted circuits use the same 3.3 V supply, 2 Ω source and 100 kΩ standby loads at typical process and 27 °C. Both capacitor placements are checked. The DC and 1 kHz–1 GHz common-supply AC comparison includes both differential output rail voltages, source current and all eight port currents. This is a fixture-specific check, not a complete eight-port admittance matrix or a PDK bandwidth qualification.

The seeded comparison attempt uses `reltol=1e-7` and `abstol=1e-14`. The adapted DC solve is initialized with all voltage values from the direct operating point using `.nodeset`; these are nonbinding guesses, not fixed-voltage constraints. Earlier unseeded practical and strict attempts are archived separately and do not substitute for a passing comparison.

Mixed comparison limits: 10 nV + 10 ppm for voltage, 1 pA + 10 ppm for current, applied to saved real/imaginary components. A maximum ratio ≤1 passes.

| Placement | Analysis | Maximum error/limit | Pass |
|---|---|---:|---|
| nominal | dc | 0.000911927 | True |
| nominal | ac | 4.10236 | False |
| remote | dc | 0.00164392 | True |
| remote | ac | 1.12544 | False |

The seeded AC rail-voltage component differences are at most 4.74 nV (nominal placement) and 0.387 nV (remote). The failed screens are port-current comparisons: maximum mixed error/limit ratios 4.10 and 1.13. These small discrepancies are not evidence of a physical circuit change, but they do not satisfy the stated numerical-equivalence screen.

## Startup and load pulse

The adapted startup attempt uses a 100 µs 0–3.3 V ramp, zero-charge startup, a 100 ns maximum step and a 1 mA-per-rail pulse at 151 µs with 1 ns edges; the requested end is 153 µs. It uses KLU, Gear, one thread, `gmin=1e-17`, `abstol=1e-14`, `reltol=1e-7`, and the existing GF180 clamp initialization. A simulator exit code alone is insufficient: aborted runs or traces that end early are rejected.

- **nominal**: incomplete — ['doAnalyses: TRAN:  Timestep too small; time = 1e-09, timestep = 1.25e-19: cause unrecorded.', 'tran simulation(s) aborted'].
- **remote**: incomplete — ['doAnalyses: TRAN:  Timestep too small; time = 1e-09, timestep = 1.25e-19: trouble with node "e.x354.ec_moscap#branch"', 'tran simulation(s) aborted'].

A separate diagnostic repeat uses the prior direct-ramp settings (`reltol=1e-6`, `abstol=1e-12`). It retains the failed AC screen and is not a qualified interface result:

- **nominal**: incomplete — ['doAnalyses: TRAN:  Timestep too small; time = 1e-09, timestep = 1.25e-19: cause unrecorded.', 'tran simulation(s) aborted'].
- **remote**: incomplete — ['doAnalyses: TRAN:  Timestep too small; time = 1e-09, timestep = 1.25e-19: trouble with node "e.x354.ec_moscap#branch"', 'tran simulation(s) aborted'].

Both tolerance choices abort at about 1 ns, before the ramp or load test. The remote-placement log identifies `e.x354.ec_moscap#branch`; the nominal log reports an unrecorded cause. The prior direct model reached about 100 µs. The eight-port interface is therefore not adopted.

## Next step

Reject the whole-corner eight-port interface for production use. Build a minimal reproducer around the reported `X354` MOS-capacitor branch and its extracted connections; compare direct and localized interface formulations, including a smooth supply ramp. Resolve the AC current-comparison discrepancy and startup failure before integrated 3×3 qualification. Do not alter physical parasitics or PDK device equations to obtain a pass.

No layout, DRC/LVS, process/temperature, optical or fabrication qualification is claimed by this experiment.

## Reproduce

```sh
bash scripts/run-tools.sh python3 scripts/check-corner-interface.py --strict --seed --diagnostic-startup
bash scripts/run-tools.sh python3 scripts/check-corner-interface.py --strict --seed --reuse-equivalence --diagnostic-startup --startup-practical
python3 scripts/report-corner-interface.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Requires the preceding charge-reduction checkpoint and its parent charge-reference inputs. The checksummed checkpoint retains decks, logs, results and scripts.
