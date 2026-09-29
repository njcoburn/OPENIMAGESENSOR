# Compact bank initialization diagnosis — 2026-09-27

**Later follow-up:** [KLU completes full-bank initialization/reset](overview.html#compact-bank-solver).
Eight-column nominal/hot accuracy and refinement now pass for the alternating
pattern. The SPARSE/reduction results below remain historical diagnostic evidence.

Docker Desktop and the existing `openimagesensor-vnc` desktop are running again.
The desktop mounts this checkout and KLayout opens the selected compact 64-column
GDS. The VNC web endpoint responds successfully at
<http://localhost:8080/vnc.html?autoconnect=true&resize=scale>.

## Controlled reduction

The documented reduction command previously rejected the new extraction: it
expected `.subckt bank` and did not support diode records. The reducer now accepts
the compact `tile` model, preserves its subcircuit name and protects both diode
terminals. Seven analytical/corruption tests and four readout-schedule tests pass.
Regenerating the historical port/far reductions produces byte-identical models.
The compact simulation runner accepts `--equivalent-bank-model`, recomputes the
deterministic reduction, audits it against the hash-checked selected extraction,
and rejects a changed model before simulation. Default simulation settings stay
unchanged.

For the compact 64-column port model, reduction removes **1824 internal
resistor-only nodes**. Star-mesh transformation changes 9283 resistors to 9289;
fewer nodes need not mean fewer resistors. Every device, capacitor and port
record is preserved. Twelve deterministic voltage probes give a worst relative
boundary-current residual of 2.215e-12 and scaled internal KCL residual of
3.346e-16. This is an algebraic audit of the existing shunt approximation.

A hot two-column control at 100 ns, with alternating 0/240 pA illumination,
completes one capture and two scans. Its saved terminal samples differ from the
previously passing unreduced control by at most **0.058281 µV**. This checks one
case at the saved readout points; it is not a new full electrical qualification.

## Smaller physical controls

New four- and eight-column layouts retain 40 µm pitch, shared physical references,
real joining wires and 40 pF storage. Both pass Magic/KLayout main DRC and direct/
resistor-collapsed LVS. The four-column device census is 42 MOS, 32 MIM and four
diodes; the eight-column census is 82 MOS, 64 MIM and eight diodes.

The four-column extracted port model completes a nominal alternating-pattern
transient through 2.76 ms, with 56,922 samples and both output scans. It does not
use transient operating-point fallback. Independent capture/output references,
hot operation, timestep refinement and placement sensitivity were not requested,
so this is a completion diagnostic only.

The eight-column port model logs failed gmin/source stepping and a singular-matrix
warning on `SELB5`, then **recovers via transient operating-point fallback**.
It reaches 1.475725 ms/31,513 samples before the 180 s watchdog. Thus neither
that warning nor entry into fallback establishes a persistent initialization
failure. This attempt progresses into readout but does not finish both scans.
The audited eight-column reduction also recovers through fallback, reaching
1.486010 ms/32,827 samples before the same watchdog. That partial progress does
not establish a useful speedup or a completed transient equivalence check.

The reduced 64-column attempt times out at 180 s with zero samples while still
in gmin stepping. It does not reach transient OP fallback within this bound.
The unreduced historical attempt also produced zero samples, but progressed to
fallback. Fewer unknowns have not established better convergence or runtime.

| Control | Temperature / max step | Last simulated time | Samples | Outcome |
|---|---|---:|---:|---|
| 2-column reduced | 125 °C / 100 ns | 2.720 ms | 52,981 | Complete; saved-sample comparison passes |
| 4-column port | 27 °C / 200 ns | 2.760 ms | 56,922 | Complete; no accuracy references requested |
| 8-column port | 27 °C / 200 ns | 1.475725 ms | 31,513 | 180 s timeout during readout |
| 8-column reduced | 27 °C / 200 ns | 1.486010 ms | 32,827 | 180 s timeout during readout |
| 64-column reduced | 27 °C / 200 ns | — | 0 | 180 s initialization timeout |

All cases use alternating 0/240 pA illumination. The report also retains the
previous unreduced 64-column physical and schematic attempts for comparison.
No simulation remains running; the VNC desktop stays available.

## Reproduction

Use fresh output directories and the pinned tools. Existing experiments are
preserved. The reduction keeps devices, capacitances, fixture and solver
tolerances unchanged; no UIC or seeded operating point is introduced.

```sh
python3 scripts/test-compact-bank-resistors.py
python3 scripts/test-compact-bank-schedule.py
python3 scripts/compact-bank-resistors.py \
  --source build/compact-bank-c64-v1-20260926/rc-port.spice \
  --out build/compact-bank-c64-equivalent-new
bank_lights=$(python3 -c "print(','.join(['0','240']*32))")
bash scripts/run-tools.sh python3 scripts/simulate-compact-bank.py \
  --layout build/compact-bank-c64-v1-20260926 \
  --equivalent-bank-model build/compact-bank-c64-equivalent-new/bank.spice \
  --out build/compact-bank-c64-equivalent-screen-new \
  --lights-pa "$bank_lights" --step-ns 200 --timeout 180 --transient-only
```

For smaller controls, build with `scripts/build-compact-bank.py --columns 4`
or `--columns 8` through the same Docker wrapper. Supply one comma-separated
illumination value per column to the simulator. Selected output directories,
outcomes and content hashes are in the
[machine-readable report](../simulations/compact-bank-initialization.json).
Waveforms and generated geometry remain local in `build/`; hashes are not an
external backup. Runtime observations are not benchmarks: some jobs overlapped.

## Next experiment

Use the four/eight-column pair to measure initialization, reset release, capture
and readout costs separately, then scale to a 16-column control with a bounded
watchdog. Preserve partial traces and identify the last completed phase. A
larger time limit needs measured progress to justify it. Do not repeat the
unchanged 64-column attempts or treat resistor reduction as the solution.

After full-bank completion is practical, run all 64 matched capture/output
references, nominal/hot patterns, 200→100 ns refinement, shunt placements and
actual supply/reference-drop checks. Repeated rows and real decoders/drivers
follow; the current controls do not close those gates.

[64-column physical screen](compact-bank-64.md) ·
[Passing two-column electrical control](compact-bank.md) ·
[Completion plan](../COMPLETION_PLAN.md).
