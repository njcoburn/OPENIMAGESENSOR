# Next steps — 64×64 on wafer.space GF180

The user prioritizes working first silicon at a modest frame rate.
[The completion plan](COMPLETION_PLAN.md) is the current source of priorities.

1. Docker access is restored and the pinned EDA tools are verified (2026-09-26).
   Read the [compact-pixel results](docs/compact-pixel.md) and
   [reset follow-up](docs/compact-reset.md) and latest
   [compact capture results](docs/compact-capture.md) and
   [joined-tile results](docs/compact-tile.md) and
   [shared two-column results](docs/compact-bank.md) before further runs.
2. Start from the [slot-fit budget](docs/64x64-slot-fit.md): full-slot default
   core 3048 × 4238 µm, candidate 40 µm square pixel pitch. Current 80 × 50 µm
   pixel layout and the 5198 µm bank cannot be the final geometry.
3. The 40 µm pixel and 2×2 control now pass scoped DRC/LVS, and the 2×2
   nominal/hot electrical and refinement screens pass. The isolated pixel now
   passes with conserved-total port/gate reset-shunt models; its raw negative
   extraction remains diagnostic. The compact capture column now passes scoped
   physical checks, 60 transients and 36 references at 40 µm pitch. Start from
   `build/compact-capture-v4-20260926`. The physical join is now qualified in
   `build/compact-tile-v1-20260926` (54 transients, 72 references; 419.404 µV total
   error). The shared two-column control now passes in
   `build/compact-bank-c2-v1-20260926`: 100 transients/240 references,
   419.033 µV worst capture/readout error. Extend to compact 1×64; reassess
   supply/reference sizing, all 64 outputs, loading and shunt placement.
   Keep the 5.821 mV layout–schematic integrated-response difference and
   26.670 µV neighbor-pattern response as separate scaling/calibration
   measurements. Budget the
   new bank at 2700 × 1100 µm; retain 40 pF. Freeze legal MIM option
   and aperture rules against the selected run before committing that layout.
4. The [bounded solver comparison](docs/compact-pixel.md) is complete: raw and
   reduced bank OP/reset controls all time out at 180 s without samples. Use
   the now-working shared two-column control to investigate scaled initialization;
   do not repeat a full-bank attempt without a discriminating change.
5. Physically join compact row and bank, check 64 outputs/references/refinement,
   then 4×64 repeated rows with real decoding/drivers and full-column loading.
6. Proceed to full 64×64 and the exact-chip release gates in the completion plan.

Manufacturing and interface work can proceed now: resolve the run/slot booking,
optical packaging and pad allocation; draft 6-bit row/column addressing with
safe reset/capture/output sequencing and an external ADC. A separate 3×3 tapeout
and a 30 fps redesign are not prerequisites.

Offline checks already available:

```sh
python3 scripts/test-compact-bank-resistors.py
python3 scripts/budget-64x64-floorplan.py --out build/slot-budget-new
python3 scripts/compact-bank-resistors.py \
  --source build/capture-bank-c64-v5-20260925/rc-port.spice \
  --out build/bank-equivalent-new
```

Use fresh output directories. Preserve existing experiments and uncommitted work.
[Earlier detailed next steps](checkpoints/planning-history-20260925/NEXT_STEPS.md)
are historical, not a second active plan.
