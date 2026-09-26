# Bank solver preparation — 2026-09-25

**2026-09-26 follow-up:** Docker is restored. Raw/reduced operating-point and
0.25 ms reset controls each time out at 180 s without saved samples. The reduction
does not resolve initialization in these bounded attempts. Use a small coupled
tile next. [Measurements and checkpoint](compact-pixel.md).

The preparation record below describes the earlier offline work.

**Algebraic model audits pass; SPICE runtime and accuracy are untested.**
Docker Desktop WSL integration is unavailable again, so this work does not close
the coupled-bank blocker. The [slot-fit replan](64x64-slot-fit.md) takes priority
over further physical revisions of the oversized bank.

The new `scripts/compact-bank-resistors.py` uses standard-library Python to
eliminate resistor-only nodes with at most four neighbors by star-mesh
transformation. All ports and device/capacitor terminals are protected. Every
non-resistor record is preserved verbatim. No resistance/capacitance cutoff,
shorted wire, deleted capacitance, changed device or relaxed SPICE tolerance is
introduced. This retains the source model's existing substrate-shunt placement
approximation; it does not qualify that approximation.

## Audit results

The selected v5 port model has 23,883 resistors. Simple series/parallel reduction
removes only 64 duplicate parallel branches and zero nodes. Degree-4 star-mesh
reduction removes **4,239 resistor-only nodes**, leaving **22,924 resistors**.
Twelve deterministic random voltage probes reconstruct eliminated node voltages
and check original-network KCL and boundary currents against the serialized
reduced network. Worst boundary relative current error is **1.976e-13**; worst
internal scaled KCL residual is **9.821e-16**. Numerical equivalence supports a
runtime experiment, not a claim of improved convergence or full-row accuracy.
The far-placement model is independently generated/audited; both reports are in
`simulations/bank-solver-preparation.json`.

Five standard-library unit tests cover known series/parallel and star/delta
circuits, dangling nodes, protected device/capacitor terminals and rejection of
corrupted resistor/capacitor records. No ngspice test has run in this stage.

## Reproduce and run a bounded comparison

Use fresh directories. Original models and earlier failed experiments are preserved.

```sh
python3 scripts/test-compact-bank-resistors.py
python3 scripts/compact-bank-resistors.py \
  --source build/capture-bank-c64-v5-20260925/rc-port.spice \
  --out build/bank-equivalent-new
# Once Docker works, first compare direct operating points:
bash scripts/run-tools.sh python3 scripts/simulate-capture-bank.py \
  --bank build/capture-bank-c64-v5-20260925 --out build/bank-raw-op-new \
  --op-only --timeout 180
bash scripts/run-tools.sh python3 scripts/simulate-capture-bank.py \
  --bank build/capture-bank-c64-v5-20260925 --out build/bank-equivalent-op-new \
  --equivalent-bank-model build/bank-equivalent-new/bank.spice \
  --op-only --timeout 180
# Then test reset release, with identical settings for raw and equivalent models:
bash scripts/run-tools.sh python3 scripts/simulate-capture-bank.py \
  --bank build/capture-bank-c64-v5-20260925 --out build/bank-equivalent-reset-new \
  --equivalent-bank-model build/bank-equivalent-new/bank.spice \
  --stop-ms 0.25 --timeout 180
```

The optional runner argument recomputes the deterministic reduction and audits
the provided serialized model before simulation; a stale or modified model is
rejected. Default runner behavior stays unchanged. Nodeset seeding is deliberately
unsupported with this optional input until seed provenance handles both models.

Compare common saved terminal voltages, completion and elapsed times. Only a
complete reset control warrants proceeding to capture and all 64 outputs with
independent references, temperature/refinement and port/far comparisons. If the
bounded attempts still stall, use a small joined tile to isolate the cause.
Physical joining wires, compact layout, multirow operation, real drivers and
startup remain separate gates. No new simulation is running.
