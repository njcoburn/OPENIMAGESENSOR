# Provisional 3×3 pad placement and bond-map review

Recorded **2026-09-19 02:12 PDT**. **Placement proposal only: no signal/power routing or manufacturing sign-off.** The packaging route has not been selected. This assumes a bare-die/custom-carrier route for planning; it is not claimed compatible with wafer.space's default-ring chip-on-board service.

![Proposed pad map, top view](assets/proposed-pad-map.png)

## Geometry and assignment

- Nominal ring: **1.210 × 1.210 mm**, with a nominal 500 × 500 µm inner opening. This is not a selected die/slot size; seal ring, scribe margin, die ID and submission outline remain absent.
- Unchanged existing core: **334.2 × 241.2 µm**, centered with translation (474.9, 478.4) µm.
- **24 pad locations**: all 19 existing core nets plus two extra VDD and three extra GND pads. One ground on each side; three supply pads total.
- Installed GF180 macros: 17 `asig_5p0`, three `dvdd`, four `dvss`, four corners, and twenty `fill10` instances. Each side uses six 75 µm pad pitches and 50 µm total filler.
- Added supply macros imply **15 supply/corner clamps** by macro inventory, versus ten in the previous power-ring vehicle. Fillers also change. This assembly needs fresh electrical qualification after review; previous ring results do not transfer unchanged.

Pad IDs run counterclockwise from the first southern pad, viewed from the top of the die. They are proposal IDs, not connector pins or an approved package numbering convention. Coordinates below refer to actual macro bond-region text labels, **not certified bond landing centers**. Final openings, edge distances, metallurgy and bond-loop geometry need the provider's review.

[Coordinate CSV](proposed-pad-map.csv) · [Logical interface and board timing](demonstrator-interface.md).

| Pad | Core net | Edge | X reference (µm) | Y reference (µm) | Bond intent |
|---|---|---|---:|---:|---|
| P01 | GND | south | 392.985 | 32.735 | proposed functional bond |
| P02 | VDD | south | 468.900 | 34.275 | proposed functional bond |
| P03 | BIAS | south | 542.595 | 33.100 | proposed functional bond |
| P04 | SEL0 | south | 617.595 | 33.100 | proposed functional bond |
| P05 | SEL1 | south | 692.595 | 33.100 | proposed functional bond |
| P06 | SEL2 | south | 767.595 | 33.100 | proposed functional bond |
| P07 | GND | east | 1177.265 | 392.985 | proposed functional bond |
| P08 | PREF | east | 1176.900 | 467.595 | proposed functional bond |
| P09 | BUF | east | 1176.900 | 542.595 | proposed functional bond |
| P10 | COL2 | east | 1176.900 | 617.595 | optional diagnostic / loading review |
| P11 | COL1 | east | 1176.900 | 692.595 | optional diagnostic / loading review |
| P12 | COL0 | east | 1176.900 | 767.595 | optional diagnostic / loading review |
| P13 | GND | north | 817.015 | 1177.265 | proposed functional bond |
| P14 | VDD | north | 741.100 | 1175.725 | proposed functional bond |
| P15 | OUT | north | 667.405 | 1176.900 | optional diagnostic / loading review |
| P16 | RST2 | north | 592.405 | 1176.900 | proposed functional bond |
| P17 | ROW2 | north | 517.405 | 1176.900 | proposed functional bond |
| P18 | VRESET | north | 442.405 | 1176.900 | proposed functional bond |
| P19 | GND | west | 32.735 | 817.015 | proposed functional bond |
| P20 | RST1 | west | 33.100 | 742.405 | proposed functional bond |
| P21 | ROW1 | west | 33.100 | 667.405 | proposed functional bond |
| P22 | RST0 | west | 33.100 | 592.405 | proposed functional bond |
| P23 | ROW0 | west | 33.100 | 517.405 | proposed functional bond |
| P24 | VDD | west | 34.275 | 441.100 | proposed functional bond |

## Routing and protection review before implementation

1. Confirm the manufacturing slot and carrier route. The nominal ring can be moved into a larger approved die; its 1.21 mm size must not be treated as a submission entitlement or final die outline.
2. Review the three supply/four return bonds and whether their extra clamp/loading cost is justified. The supply-domain straps have not been added.
3. Review the analog-pad/protection choice for every functional pin, especially 3.3 V controls, 2 V VRESET and low-current BIAS. `asig_5p0` is an existing candidate macro; its name is not proof of thin-oxide protection compatibility.
4. Decide on COL0–COL2 and OUT access. Their four purple pads are optional placeholders. Even an unbonded but connected pad adds leakage/capacitance. Default to leaving those routes absent until a load budget is approved; replacing unused pads with fillers would change the ring again.
5. Reserve secondary protection and supply connections near the functional pads. The prior local protection cell has not been placed or copied blindly onto all pins.
6. Route controls away from the optical junctions and sensitive BIAS/OUT paths; keep bond wires and packaging out of the optical path. No passivation opening or optical keepout mask is introduced by this proposal.
7. After these choices: generate the matching full-chip schematic, route, then run connectivity, device LVS, applicable DRC/density/antenna and extracted electrical checks.

## Checks completed here

All 19 schematic port names are assigned, pad IDs and reference points are unique, each point lies in its placed macro bounding box, nominal side lengths match, the core fits the nominal opening, and its translation lies on the layout grid. These are placement checks, not DRC/LVS. Macro process layers have small bounding-box overhangs; simple bbox overlaps are not treated as design-rule violations.

The original core and power-ring GDS files are not modified. The separate proposal GDS and source hashes are in the checkpoint. No simulator experiments were resumed.

## Information needed to finalize this

- Selected wafer.space run/slot, or confirmation that none has been selected.
- Intended wire-bonding/package provider, or confirmation that none has been selected.
- Their required pad ring, die geometry, bond map and optical-access constraints.

The [manufacturing review questions](manufacturing-review.md) are ready to send to a provider once the destination and authorization are supplied. No external contact has been made. We cannot certify an optical path from a pad-placement drawing.

## Reproduce

```sh
bash scripts/run-tools.sh python3 layout/demonstrator-pad-proposal.py
python3 scripts/report-pad-proposal.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```
