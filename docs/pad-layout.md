# Physical analog-pad interface candidate

This step creates an independently checked local protection cell and a single analog-pad wrapper. The existing sensor core GDS is unchanged. It is not a complete pad ring or ESD-qualified chip.

## Connections

The primary `gf180mcu_fd_io__asig_5p0` steering diodes terminate at the same supply and ground as the sensor. The wrapper joins VDD/DVDD stripes and VSS/DVSS stripes for a single-domain functional experiment. The local protection diodes terminate at those core rails. The PAD node connects through a poly resistor to CORE.

A complete ring still needs suitable supply pads, clamps, corners and sufficiently wide return paths. The [foundry supply-pad documentation](https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/power.html) describes built-in clamps in supply and corner pads. This checkpoint does not establish their protection voltage for our 3.3 V thin-oxide core. It does not use a 5 V rail to power the sensor.

## Local physical cell

- PDK-generated `ppolyf_u`, width 3.2 µm, length 1 µm, substrate tied to VSS.
- One N+/substrate diode and one P+/Nwell diode, each 1 × 12 µm: area 12 µm² and perimeter 26 µm.
- Routed signal and rail connections, contacted guard rings and floating density fill.
- Footprint of the filled cell: 31 × 22 µm.

The first physical resistor candidate is **149.12 Ω nominal**, rather than the previous ideal 100 Ω. The tested PDK resistance range is 121.55–176.43 Ω over resistor corners and −40 to 125 °C, measured with 10 mV across the resistor. Its acceptance is based on the new functional checks, not on treating it as a 100 Ω part.

The local cell passes Magic DRC, the full installed KLayout rule deck and device-level Netgen LVS. Geometry assertions separately check diode area and perimeter: a flat Magic export produced an incorrect perimeter suffix, while hierarchical export gives 26 µm correctly. LVS alone did not expose that unit error.

## Extraction scope

Local wiring and fill capacitance is extracted, then floating conductors are eliminated at zero net charge using a Schur complement. The physical PDK resistor and junction models remain explicit. The resulting six terminal capacitances are approximately:

| Pair | Capacitance (fF) |
| --- | ---: |
| PAD–VSS | 1.629 |
| PAD–CORE | 0.199 |
| PAD–VDD | 0.009 |
| CORE–VSS | 7.734 |
| CORE–VDD | 3.527 |
| VDD–VSS | 11.978 |

Metal wire resistance and the full primary-pad/ring parasitic network are not included in these functional checks. The primary pad still uses the installed library device model. This distinction matters even though the local wiring capacitance is small compared with the primary pad capacitance.

## Combined wrapper and bond-pad rules

The original wrapper had a metal2 signal/ground crossing. The corrected route changes metal level where it crosses the signal. Failed initial evidence is kept in the checkpoint.

The full KLayout deck reports 87 CUP.3 slot-spacing violations in the unmodified library bond pad. The same markers are present when checking the stock pad alone. These are **unresolved findings**, not waived violations. The [library describes a non-CUP pad](https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/index.html), while [CUP.3](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_09_3.html) belongs to circuit-under-pad rules. Confirm the applicable bonding option and accepted verification configuration with the chosen shuttle/assembly process before claiming complete-interface DRC closure. Do not change the library bond-pad metal just to suppress these markers.

## Reproduce

From the repository root:

```sh
bash scripts/run-tools.sh bash scripts/build-pad-interface.sh
bash scripts/run-tools.sh python3 scripts/simulate-pad-layout.py dc
bash scripts/run-tools.sh python3 scripts/simulate-pad-layout.py
bash scripts/run-tools.sh python3 scripts/refine-pad-layout.py
bash scripts/run-tools.sh klayout -b -r scripts/render-pad-layout.py
bash scripts/run-tools.sh python3 scripts/report-pad-layout.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The build script retains raw verification reports; process exit zero does not imply DRC/LVS passed. The report explicitly distinguishes local-cell verification, combined-wrapper connectivity and inherited bond-pad DRC findings. Existing extracted-sensor and board-bias prerequisites are required by the simulation runner.

Functional simulation uses the finite-transition behavioral ADC from the prior evaluation. It covers 36 physical-reference DC cases (typical MOS/diodes, three resistor corners, four temperatures, three supplies) and five selected imaging cases, plus a finer-timestep hot check. It is not a complete Cartesian PVT matrix, ESD pulse simulation, arbitrary power-sequencing qualification, or fabricated-silicon measurement.
