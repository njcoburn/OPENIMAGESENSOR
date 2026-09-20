# Charge-conserving RC reference

Recorded **2026-09-19 00:42 PDT**. First release: **3×3 monochrome demonstrator**, confirmed by the user. The proposed 64×64 camera is a later expansion.

**Eight reference models preserve the original capacitance matrix, and all 16 independent ngspice charge checks pass.** This fixes charge accounting in a separately generated reference netlist. It does not correct or qualify Magic's native distributed-capacitance export.

![Charge reference versus original extraction and native export](assets/charge-reference.png)

## Construction and scope

The builder reads original node-to-substrate and mutual capacitors from `.ext`, retains their values and connections once, and copies every extracted resistor and device record unchanged from the area-corrected RC export. It replaces the native exported capacitor records as a complete set; it does not delete isolated negative entries or fit capacitor values to simulation.

Each original net maps to one connected resistor component. If its original named node remains, that node is the anchor. Otherwise the nearest recorded resistor-node coordinate to the original extraction-node coordinate is selected deterministically. Nets without an extracted resistor network retain their original node. Every anchor and selection reason is archived.

**Placement approximation:** capacitance remains lumped per original extracted net and attached to these anchors. The original node coordinate is an extractor naming location, not a demonstrated physical capacitance centroid. Exact charge accounting with zero metal resistance does not establish accurate finite-resistance settling or high-frequency behavior. We have not adopted this as a signoff model.

| Model | Resistors | Devices | Capacitor pairs |
|---|---:|---:|---:|
| control-tee | 1 | 0 | 3 |
| control-tee-rotated | 1 | 0 | 3 |
| control-long-tee | 1 | 0 | 3 |
| control-long-tee-rotated | 1 | 0 | 3 |
| fill10-full | 2,259 | 32 | 6 |
| fill10-metal | 1,914 | 0 | 10 |
| corner-full | 571,551 | 358 | 127 |
| corner-metal | 451,892 | 0 | 150 |

## Validation

- Four small controls and four ring coupons have only nonnegative capacitors.
- Every original capacitance pair is recovered after collapsing the metal resistors. The independent audit re-reads the saved SPICE files and original `.ext`; maximum serialized pair error is 1.137e-13 fF. Pair equality determines the complete capacitance matrix, including charge and energy for arbitrary original-net voltages.
- Resistor and device records compare exactly with the earlier area-corrected exports. Their prior DC and LVS topology evidence remains applicable; no new physical layout or LVS run is claimed here.
- Sixteen ngspice AC checks cover common-mode, differential and both electrode-basis excitations across four controls. Maximum charge error versus the original capacitance matrix is 1.776e-15 fC, at numerical precision.
- The T control now measures **6.59538 fF** in common mode, matching the original **6.59538 fF**. The native RC export measured **10.50568 fF**.

For the independent AC fixtures, signal endpoints A/B are driven together so metal resistance has no voltage drop; the separate lower plate is driven according to each excitation. The implicit substrate is explicitly exposed and grounded in the fixture only. Charge is inferred from AC source current at 1 MHz. These are numerical electrical checks, not physical capacitance measurements or camera transients.

## Why a separate reference

Source inspection shows two native behaviors that need care: coupling can be redistributed as substrate capacitance while still being retained as coupling, and `killnode` handling suppresses coupling attached to eliminated nodes. A local subtraction of the observed excess would not repair all cases. Reconstructing the complete original capacitor network provides an auditable reference without changing installed tools or inventing missing spatial information.

## Next steps toward the 3×3 release

1. Test capacitor-anchor placement sensitivity rather than treating the chosen coordinate as physically exact.
2. Eliminate resistor-only internal nodes with a validated reduction that preserves retained-port behavior. The corner reference still contains over half a million resistors.
3. Run corner and integrated 3×3 transients, then repeat process/supply/temperature and realistic ADC-load checks with the accepted model.
4. Complete the physical, manufacturing-interface and bench milestones in [COMPLETION_PLAN.md](../COMPLETION_PLAN.md).

Substrate ground-domain interpretation and previously recorded extraction diagnostics remain open. No tapeout, optical performance, new DRC, or complete camera qualification is claimed. Production GDS and installed tools are unchanged.

## Reproduce

Prerequisite: the area-corrected extraction and controls from the capacitance-candidate checkpoint.

```sh
python3 scripts/build-charge-reference.py
python3 scripts/audit-charge-reference.py
bash scripts/run-tools.sh python3 scripts/check-charge-reference.py
bash scripts/run-tools.sh python3 scripts/report-charge-reference.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

`checkpoints/charge-reference/evidence.tar.gz` preserves the generated models, mappings, audits, simulator decks/logs/results, input `.ext`/`.res.ext`/RC files, scripts and completion plan, with a verified SHA-256 manifest.
