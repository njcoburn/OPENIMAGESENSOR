# Diode-size comparison

Run `bash scripts/run-size-study.sh` from the repository root. This prepares isolated
5, 10 and 20 µm square N+/substrate diode variants, generates their Xschem views,
builds filled 3×3 GDS arrays, runs Magic and full KLayout GF180MCUD DRC, and compares
the extracted hierarchy with both an independent reference and Xschem using Netgen.
It then simulates equal assumed photocurrent densities and updates `overview.html`.

## Artifacts

- `build/size-study/{5,10,20}um/build/array_3x3.gds`: final filled layouts.
- Each variant's `xschem/array_3x3.sch` and `pixel_physical.sch`: graphical hierarchy.
- Each variant's `build/array-check/`: DRC and LVS evidence.
- Each variant's `build/size-performance/`: comparison testbench, log and waveform.
- `simulations/diode-size-comparison.json`: results and verified GDS fingerprints.
- `docs/assets/diode-size-comparison.png`: response plot.

The original baseline artifacts remain unchanged. The study generator adapts copies
of the baseline source files; rerun it after changing the baseline only with the
intent to regenerate the study. Generated variant directories are ignored by Git;
the study scripts, summary data and notebook assets are the reproducible record.

## Interpretation

The pixel pitch remains 80×50 µm. Detector areas are 25, 100 and 400 µm², with
geometric fractions of 0.625%, 2.5% and 10%. These are drawn-area fractions before
contact shadowing, not measured optical collection efficiencies.

Assumed photocurrent densities are 0, 0.2 and 0.6 pA/µm². Thus bright currents are
15, 60 and 240 pA. The model includes updated diode area/perimeter and GF180
transistor device capacitances. It does **not** include extracted wiring/fill
parasitics, calibrated optical response, noise, mismatch or corner sweeps.

The 20 µm diode shifts down by 5 µm to clear the horizontal buses. Larger variants
use revised contact routes and fill keepouts. Nonphysical layer-0 primitive bounds
are removed from their final GDS before density checking. This is a local array
exercise, not a complete chip or manufacturing submission signoff.
