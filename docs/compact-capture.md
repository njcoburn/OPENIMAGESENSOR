# Compact 40 pF capture column — 2026-09-26

**Follow-up:** the [physically joined tile](compact-tile.md) now passes its
single-capture/two-read development screen. Shared multi-column work is next.

**A 40 µm-pitch isolated capture column now passes scoped physical and electrical
checks.** The candidate occupies 36.6 × 861.48 µm, with seven unchanged transistor
devices and eight 32 × 77.76 µm MIM plates. All 60 bounded transients and
36 DC reference solves complete. This is an isolated-column result; the pixel
join, shared bank and full 64×64 camera remain unimplemented.

## Geometry and fit

- Magic and KLayout main DRC: zero violations. Direct and resistor-collapsed LVS
  both match the independently constructed transistor/MIM reference.
- Two columns at 40 µm pitch also pass KLayout main DRC. They have no shared
  routing; this is an abutment-spacing control, not a two-column bank.
- Bounds: (0, -1)–(36.6, 860.48) µm. A 64-column pitch envelope would be
  2560 × 861.48 µm, inside the 2700 × 1100 µm bank planning rectangle before
  shared routes, references, controls and margin. Actual bank fit is still open.
- Each plate retains 2488.32 µm² area; the changed perimeter slightly changes
  modeled capacitance. Eight separate bottom-plate islands pass the overlap
  audit, with no lower via overlapping the capacitor plate.
- Ground and VDD trunks are 2 and 0.8 µm wide with distributed branch contacts;
  buffer/output rails are 0.6 µm. Device placement and routing are repacked, not scaled.
- The original generator mode reproduces the earlier qualified column: empty
  polygon XOR on every layer and byte-identical direct-device extraction.

The first compact attempt failed plate-to-routing clearance checks and is
excluded. The accepted candidate raises the plate stack by 20 µm.
The initial 2 µm VDD / 0.6 µm output revision passed tracking but missed the
separate transfer-comparison band (649.315 µV). Narrowing the output alone
reduced the limiting nominal shift to 606.466 µV. A halved-ground-resistance
diagnostic barely changed it; doubling VDD resistance brought both nominal
input extremes inside the band. These modified-netlist controls are diagnostic,
not physical passes. The accepted VDD trunk revision is newly extracted and
qualified with its actual device, resistor and capacitor records. This balance
must be reassessed with the joined tile and full-bank supply network.
Main DRC excludes density, antenna and CUP. No optical device is inside this cell.
The 2 fF MIM option is still conditional on the selected manufacturing run.

## Electrical checks

The inherited single-column fixture uses imposed inputs 1.2/1.6/2.0 V, 27/125 °C,
nominal wire RC, SPARSE, unchanged tolerances, capture at 1.4 ms, first/last
20 µs output slots, 10 µs acquisition, 100 pF board and 20 pF sample loads.
Every main-matrix waveform is finite, monotonic and complete to 2.7 ms; its
maximum timestep and recorded samples were independently audited.

| °C | Tracking (µV) | Layout–ideal schematic (µV) | 100→50 ns (µV) | Both shunts near→far (µV) |
|---|---:|---:|---:|---:|
| 27 | 34.8296 | 395.2219 | 0.0930 | 0.0010 |
| 125 | 165.7161 | 379.8981 | 0.2625 | 0.0069 |

Tracking compares the physical output to its own DC reference; its limit is
500 µV. Layout–schematic shift is a separate transfer comparison with the ideal
40 pF schematic. Its additional 500 µV screen passes: **True**.
Timestep and shunt-placement limits are 10 µV.

The 36 DC controls use 200/400 µs optran fallback limits; 0 invoke transient
fallback. Direct convergence does not exercise those durations and is not a
longer-settling test. Maximum reference difference is
0.000000000 µV against 0.01 µV.

### Extraction approximation

The raw extraction contains 5 negative COL/BIAS shunt corrections and remains
diagnostic. Four models conserve each positive signed net total (COL: 21.89907 fF, BIAS: 18.38350 fF),
placing each at its port or far resistor node. All 85 resistors, devices,
other shunts and coupling records are retained. The collapsed capacitance
matrix is conserved within 1e−25 F.

The main matrix compares both-near with both-far. Twelve additional 50 ns
transients move COL alone or BIAS alone, covering all four combinations at every
temperature/input condition. Maximum independent output shift:
0.023582 µV; maximum over output, storage and buffer nodes:
0.023582 µV. This bounds sampled sensitivity
for this fixture, not arbitrary distributed behavior or startup.

### Independent capacitor control

| °C | Measured model capacitance (pF) | Leakage magnitude (fA) |
|---|---:|---:|
| 27 | 40.033707391 | 60.579643 |
| 125 | 40.068776783 | 60.525305 |

AC and DC measurements agree with independent area/perimeter/temperature
calculations. These are simulator measurements, not fabricated-device results.
The installed model's voltage-dependent expressions remain inactive.
The capacitor control was run on the first DRC-clean compact revision; its
direct-device netlist is byte-identical to the selected routing revision and
the report checks that hash before reusing the result.

## Next and reproduction

Physically join a compact pixel and capture column, extract the joining wires,
and test coupled reset/capture before scaling. Recheck shunt placement with the
new boundary conditions. Real drivers, repeated/multirow operation, full-column
loading, process/wire corners, noise and manufacturing qualification remain open.
Milestone 1 is still open until the joined tile passes.

Use fresh directories. The selected layout is `build/compact-capture-v4-20260926`;
the selected matrix is `build/compact-capture-matrix-v4-20260926`.

```sh
bash scripts/run-tools.sh python3 scripts/build-capture-column.py \
  --out build/compact-capture-new --compact --wide-power --wide-output \
  --output-width-um 0.6 --vdd-width-um 0.8
bash scripts/run-tools.sh python3 scripts/check-compact-capture.py --run build/compact-capture-new
bash scripts/run-tools.sh python3 scripts/check-capture-capacitance.py \
  --extraction build/compact-capture-new --out build/compact-capacitance-new
bash scripts/run-tools.sh python3 scripts/qualify-capture-column.py \
  --extraction build/compact-capture-new --out build/compact-matrix-new
bash scripts/run-tools.sh python3 scripts/audit-capture-column-matrix.py --run build/compact-matrix-new
bash scripts/run-tools.sh python3 scripts/check-compact-capture-placement.py \
  --extraction build/compact-capture-new --matrix build/compact-matrix-new --out build/compact-placement-new
```

[Machine-readable results](../simulations/compact-capture.json) ·
[Checkpoint](../checkpoints/compact-capture/README.md) ·
[Current plan](../COMPLETION_PLAN.md).
