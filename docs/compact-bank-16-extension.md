# Revised 16-column bank: refinement and individual shunt placement

The 27 September continuation **passes its selected screen**. All 32 new
transients and 576 new references have finished. The independently audited
combined result covers 46 transients and 1,152 references, with
433.171 µV worst total error and 301.667 µV tracking.
Physical 100/50 ns comparisons peak at 0.450 µV. Hot inverse individual/joint
placement changes peak at 0.105 µV HOLD and 0.137 µV STORE. The separate
physical/schematic inverse-pattern response differs by up to 10.062 mV;
that metric has no assigned acceptance threshold.

The unchanged layout is `build/compact-bank-c16-ground8-20260927`.
New evidence is under `build/compact-bank-c16-ground8-extension-20260927`.
The previous 14-case report remains immutable; all 2,453 evidence hashes were verified.

## Added scope

| Cases | Purpose | References |
|---|---|---|
| 8 physical runs | 50 ns for inverse/dark/middle/bright at 27/125 °C | 384 |
| 4 schematic runs | Inverse pattern at 27/125 °C and 100/50 ns | 192 |
| 20 placement runs | All 19 individual shunts plus joint far placement, inverse pattern at 125 °C, 100 ns | None; comparison controls |

Together with the retained runs, this supplies paired 100/50 ns physical
results for all five patterns at both temperatures. Individual placement
uses the previous highest-error case; it does not establish coverage at
other temperatures or patterns. All cases capture once and read 16 columns
twice over 3 ms, with KLU, trapezoidal integration and unchanged tolerances.

Accuracy criteria remain 500 µV for same-state capture/readout and output
tracking. Refinement and HOLD/STORE placement comparisons use 10 µV.
Layout–schematic integrated response has no assigned acceptance threshold.

## Reproduction

Use fresh output directories and retain the original failures and controls.
The batch runs four cases concurrently, with a 1,800 s transient/reference
watchdog and a 3,600 s whole-case process-group watchdog. Each accuracy case
checks 16 capture and 32 output references, two at a time. It records execution
completion and accuracy separately; a missing case cannot produce a pass.

```sh
bash scripts/run-tools.sh python3 scripts/extend-bank-16-screen.py \
  --layout build/compact-bank-c16-ground8-20260927 \
  --out build/compact-bank-c16-ground8-extension-new --workers 4
```

Audit the retained batch, then render the results:

```sh
bash scripts/run-tools.sh python3 scripts/report-bank-16-extension.py \
  --batch build/compact-bank-c16-ground8-extension-20260927
bash scripts/run-tools.sh python3 scripts/render-bank-16-extension.py
python3 scripts/update-overview-sections.py
```

The audit verifies all prior evidence hashes, every new/retained binary trace,
all 1,152 combined references, the exact model variant, simulator options,
controls, illumination, sampling schedule, reference clamp voltages and error
calculations. It also proves each placement changes only the intended shunt
endpoint while preserving capacitance totals and every resistor/device.

Seven regression/adversarial tests exercise the new audit:

```sh
bash scripts/run-tools.sh python3 scripts/test-bank-16-extension-audit.py \
  --layout build/compact-bank-c16-ground8-20260927 \
  --run build/compact-bank-c16-ground8-patterns-20260927/inverse-125
```

They include a retained passing control, all 20 intended variants, and rejection
of corrupted samples, a missing scan sample, false DC reference values,
relabelled error summaries and unintended circuit changes.

## Remaining gates

The other placement and schematic pattern/temperature combinations, process,
wire and supply corners, and remaining local supply/reference-drop checks are
still required to close the broader bank qualification. The [64-column ground-return diagnosis](compact-bank-64-read-probes.md)
records completed geometry, main DRC/LVS and selected electrical checks. Full 64-column reference qualification, real decoding and
drivers, repeated rows, exact 64×64 assembly and manufacturing signoff remain
open. Run-specific optical packaging/MIM options are still unresolved.

Raw evidence is local and ignored by Git. A fresh clone needs a separate
copy or reproduction; see [checkpoint storage](../checkpoints/README.md).
The [overview](overview.html#compact-bank-16-extension) is the user-facing
report; the [previous screen](compact-bank-16-screen.md) retains its own scope.
