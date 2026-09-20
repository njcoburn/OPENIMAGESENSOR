# Small ring sections — extraction experiment

This experiment isolates one `fill10`, two abutted fillers, one corner, and a corner abutted to a filler at the actual 355 µm boundary. It leaves the sensor and ring GDS unchanged. Results are in [the notebook](overview.html#ring-sections) and [JSON](../simulations/ring-sections.json).

## Geometry and terminals

The generator copies the installed foundry macros without device edits. It separately copies metal 1–5 and vias 1–4 for a conductor-only control, checking conductor-region equality before adding identical measurement leads to both versions. KLayout traces physical overlaps without joining labels by name: four metal rails remain separate, and 830 macro-label probes pass across the four coupons.

Each rail has an A/B measurement pair. The 0.4 µm wide M5 leads extend outside the macro to give Magic distinct terminal locations. Reported resistance includes the leads, with other terminals left open in the resistor-only calculation. The leads are a diagnostic fixture, not proposed fabrication wiring; no new DRC run is claimed. Existing full-ring DRC evidence applies only to its unchanged geometry.

Point terminals are not equipotential abutment faces. More than one stripe and layer crosses each macro boundary. A valid stitched model must preserve those boundary connections and internal device taps; scalar resistance addition is insufficient.

## Extraction and checks

The pinned container uses Magic 8.3 revision 664. Threshold/minimum-delay settings must be established before `extract all`, because `extract do resistance` invokes resistance extraction automatically. RC export runs independently from a device-only export. See the [official Magic command reference](https://www.opencircuitdesign.com/magic/commandref/extresist.html).

Each extraction has a 120-second watchdog. All corrected full-geometry cases finish: fillers in under one second and corner cases in about 28 seconds. The audit rejects zero/nonpositive extracted resistors, disconnected terminal pairs, and supply-to-ground resistor paths. A sparse 1 A nodal solve measures each rail with all other terminals open and checks current balance to 1e-6 A.

All four exports pass device LVS after the explicitly extracted resistor networks are shorted; PDK resistor devices remain. Filler LVS retains four separate macro ports. Corner LVS uses tied VDD/DVDD and VSS/DVSS, matching the actual analog ring's supply domain. This does not verify independent biasing of the four corner rails.

The full corner `.ext` file aliases VSS and DVSS through semiconductor geometry; its resistor mesh connects those grounds. The conductor-only control retains four separate nets. The current experiment establishes this extraction distinction; it does not independently qualify the substrate coupling model.

## Results and limitations

Full-device point-terminal resistance, including the probe leads:

| Coupon | VDD (Ω) | VSS (Ω) | DVDD (Ω) | DVSS (Ω) |
| --- | ---: | ---: | ---: | ---: |
| One filler | 0.45849 | 0.45848 | 0.40100 | 0.40100 |
| Two fillers | 0.49908 | 0.49870 | 0.45121 | 0.45123 |
| Corner | 1.40980 | 1.90921 | 1.83018 | 1.41587 |
| Corner + filler | 1.57681 | 1.76414 | 1.32701 | 1.64015 |

Full and conductor-only filler results are close. Corner results differ by up to about 27%, reflecting different semiconductor networks and extraction partitions; no interchangeable-model or absolute-accuracy claim is made. The abutment can add parallel paths, so adding a filler need not increase every measured point-to-point resistance.

Full filler exports have no negative capacitor entries; the corner and corner-plus-filler exports contain five and seven respectively. The conductor-only controls also contain negative capacitor entries. None has been silently clamped, deleted, or corrected. Their transient/passivity implications and substrate treatment must be resolved before using these RC files for camera verification. Passing device LVS and DC resistor checks does not validate capacitance.

## Retained failed experiments

1. A device-only export followed by RC export in one session produced zero-ohm aliases and eliminated-node errors. These exports are invalid.
2. Direct internal point labels produced an open/missing passive terminal despite a successful tool exit. These exports are invalid as terminal models.
3. The initial audit expected four disconnected resistor networks everywhere. The corner fails that assumption because its full extraction connects the two grounds through semiconductor geometry. The revised audit allows that specific corner connection while forbidding supply-to-ground paths; tied-domain LVS is reported explicitly.

The failed exports remain under `build/ring-sections/<coupon>/attempt-*`. The portable archive retains their scripts, status and logs. Corrected exports have separate audits and should not be confused with the failed attempts.

## Reproduce

```sh
bash scripts/run-tools.sh python3 scripts/prepare-ring-sections.py
bash scripts/run-tools.sh python3 scripts/extract-ring-sections.py --mode full --timeout 120
bash scripts/run-tools.sh python3 scripts/extract-ring-sections.py --mode metal --timeout 120
bash scripts/run-tools.sh python3 scripts/audit-ring-sections.py
bash scripts/run-tools.sh python3 scripts/report-ring-sections.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The preparer writes coupons under `build/ring-sections/`. The archive and manifest are in `checkpoints/ring-sections/`; restore into a separate directory first, as the archive also contains source snapshots. The installed foundry library is provided by the pinned Docker image.

## Next acceptance test

Define a consistent multiport boundary interface, preserving every abutting conductor and device connection. Compare a stitched two-filler model with the monolithic two-filler extraction under the same terminal excitations before attempting a complete ring. Investigate the corner's semiconductor-ground coupling and negative capacitance entries separately; then validate transient behavior and integrate the full camera.
