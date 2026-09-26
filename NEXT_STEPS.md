# Next steps — 64×64 on wafer.space GF180

The user prioritizes working first silicon at a modest frame rate.
[The completion plan](COMPLETION_PLAN.md) is the current source of priorities.

**Latest:** [compact 1×64 geometry](docs/compact-bank-64.md) now fits the bank
budget and passes main DRC and both LVS paths. It is not electrically qualified.

1. Docker Desktop works after launching its Windows application directly. Use
   the pinned container through `scripts/run-tools.sh`; socket access is needed.
2. Start from `build/compact-bank-c64-v1-20260926`. The 2627.76 × 978.28 µm
   layout includes physical row/bank joins and shared references/wiring. It fits
   the 2700 × 1100 µm local budget with unchanged 40 µm pitch and 40 pF storage.
   Complete-chip fit, run-specific MIM and aperture approval remain open.
3. Localize extracted initialization before another full-bank transient. The new
   compact `rc-port` attempt times out at 180 s with zero samples; the matching
   schematic reaches 1.785052 ms/76,919 samples before timeout. Both are incomplete.
   Use smaller compact banks or an audited resistor-only reduction of the new
   extraction to discriminate the cause. Preserve the failed attempts and keep
   solver tolerances and real devices/parasitics unchanged.
4. Once initialization works, qualify all 64 matched capture/output references,
   nominal/hot patterns, 200→100 ns refinement, shunt placements and actual
   supply/reference drops. The runner supports 2–64 columns with nonoverlapping
   scans; the existing qualification matrix remains explicitly two-column.
5. Keep the [two-column evidence](docs/compact-bank.md) as the passing electrical
   control: 100 transients/240 references and 419.033 µV worst capture error.
   Its 5.821 mV layout–schematic response and 26.670 µV neighbor response are
   separate model/scaling measurements. Its success does not qualify 64 columns.
6. After full-bank qualification, exercise 4×64 repeated rows with real
   decoding/drivers and full-column loading, then assemble 64×64 and complete
   the exact-chip release gates in the completion plan.

Manufacturing and interface work can proceed now: resolve the run/slot booking,
optical packaging and pad allocation; draft 6-bit row/column addressing with
safe reset/capture/output sequencing and an external ADC. A separate 3×3 tapeout
and a 30 fps redesign are not prerequisites.

Offline checks already available:

```sh
python3 scripts/test-compact-bank-schedule.py
python3 scripts/test-compact-bank-resistors.py
python3 scripts/budget-64x64-floorplan.py --out build/slot-budget-new
python3 scripts/compact-bank-resistors.py \
  --source build/compact-bank-c64-v1-20260926/rc-port.spice \
  --out build/bank-equivalent-new
```

Use fresh output directories. Preserve existing experiments. Source/reports/manifests
are pushed; generated checkpoint archives remain local and ignored by Git. A fresh
clone needs separate evidence copies or reproduced builds; see [storage](checkpoints/README.md).
[Earlier detailed next steps](checkpoints/planning-history-20260925/NEXT_STEPS.md)
are historical, not a second active plan.
