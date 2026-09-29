# Manufacturing and optical-access review

## Run 3 budget and geometry — checked 2026-09-27

The [overview](overview.html#wafer-space-run3) now records current source links,
all four slot sizes, costs, Los Angeles deadline conversions and a dimensioned
block budget. [Source facts](../simulations/wafer-space-run3-20260927.json) and
[computed fit](../simulations/wafer-space-fit-20260927.json) separate provider
data from our arithmetic.

Run 3 lists early bird through 30 September, purchase by 9 December and clean
GDS by 16 December 2026, all 23:59 AoE; delivery is Q2 2027. The full-slot batch
of 1,000 dies costs $7,000 early / $8,000 standard. The optional $1,500 CoB
add-on brings that to $8,500 / $9,500, before unpriced project expenses and
subject to optical compatibility. The campaign includes worldwide shipping;
insurance and tariffs remain the buyer's responsibility. No later run date was
established. No purchase or reservation was made.

The provider's [19 September update](https://www.crowdsupply.com/wafer-space/gf180mcu-run-3/updates/1x1-slots-running-low)
reports few full slots remaining. Current inventory and operative order terms
must be confirmed before purchase. The campaign funding widget's 19 December
date and expired countdown messages conflict with the explicit milestone table;
do not use those widgets as the GDS deadline.

The compact 2.560 mm-square array fails even the inside-seal short dimension
of both half slots and the quarter slot. A full slot remains the viable
planning envelope. Substituting the current distributed-return bank's
2667.87 × 1069.80 µm bounds into the nonoverlapping block budget leaves
**3.126 mm²** unreserved in the default core. The older 3.409 mm² calculation
uses the original bank and remains a dated baseline.
This is not final-chip fit: the bank already includes a pixel row, so final
assembly must add 63 further rows and audit exactly 4096 diodes. Pad allocation,
optical packaging, process options and provider signoff remain open.

The provider [precheck](https://github.com/wafer-space/gf180mcu-precheck)
checks the top cell, origin/grid, slot bounds, metal limit, density, antenna,
Magic and KLayout DRC. CoB additionally checks template identifiers and pad
openings. Existing block-level main DRC/LVS passes do not replace these checks.

The [source reconciliation](wafer-space-pdk-reconciliation.md) establishes that
the provider's pinned configuration selects the same five-metal, 1.1 µm
top-metal, 2 fF/µm² M4/M5 MIM options. Relevant GF180 build/extraction and
primitive device-model sources are unchanged. The newer verification-library
main DRC completes on the unchanged grid bank with zero violations. Exact
provider tool/build equivalence, density/antenna, complete-chip precheck and
optical access/packaging remain open.

## Earlier direction — 2026-09-25

The user selected **GF180 through wafer.space** for 64×64 first silicon, with
modest frame rate acceptable. Exact run, slot booking and optical packaging
remain unconfirmed. The earlier 24-pad, 1.21 mm demonstrator is historical.

The [slot-fit study](64x64-slot-fit.md) uses the published full-slot default
core (3048 × 4238 µm) as a planning envelope. Existing array and bank geometry
exceed the slot; compact layouts are required. The [provider's Run 3 table](https://wafer.space/)
lists purchase on 9 December and clean GDS on 16 December 2026, 23:59 AoE, with
parts in Q2 2027. No reservation or delivery commitment is inferred.

The [project template](https://github.com/wafer-space/gf180mcu-project-template)
uses gf180mcuD and permits changing signal-pad types while preserving bondpad
positions and power pads for its default board. Generate a pad map for analog
output, VRESET, BIAS/PREF and control signals; verify analog protection/leakage
and available core dimensions. The default two analog pads do not constitute
an approved sensor interface. Check the selected run's precise PDK revision,
metal/MIM options and precheck rules.

Optical access and acceptable passivation/metal/fill keepouts remain unresolved.
The chip-on-board offering's default-ring requirement does not establish that
encapsulation is transparent or leaves the junctions accessible. Obtain a
compatible optical bonding/package specification before release.

The historical draft questions below now apply to a 64×64, 4096-junction sensor;
update the attached floorplan and bond map accordingly. No message was sent.

## Historical 3×3 review

Checked **2026-09-19 01:59 PDT**. No reservation, purchase, submission or external message has been made.

## Working decision — 19 September 2026

The user has no selected run, slot or wire-bonding provider and approved proceeding with the existing 24-pad arrangement. Local routing and verification may proceed. The [routed custom-carrier candidate](routed-demonstrator.md) is nominally 1.210 × 1.210 mm; this is a layout envelope, not a confirmed manufactured die outline. Final bond openings, optical access, die/seal geometry and provider requirements remain open.

## Confirmed public information versus project assumptions

[wafer.space technology](https://wafer.space/technology.html) describes GF180MCU fabrication, dicing and delivery, with design/sign-off the designer's responsibility. The [current homepage](https://wafer.space/) says its chip-on-board option requires the default pad ring. The [FAQ](https://wafer.space/faq.html) points designers to community pad-ring examples rather than offering pad-ring design assistance.

Those statements do **not** establish that the packaging provides a clear optical path or that our junction is a characterized photodetector. Neither the earlier 1.110 × 1.010 mm power-ring vehicle nor the new 1.210 × 1.210 mm routed candidate is an approved submission floorplan. Confirm the specific shuttle, slot, pad-ring and packaging requirements before adapting it. Do not infer compatibility with the chip-on-board add-on from electrical pad checks.

## Draft questions for manufacturing / packaging review — not sent

We are developing a GF180 3×3 monochrome test sensor with exposed-to-light junctions, a shared analog output and external timing/ADC. Could you confirm:

1. Which current run/slot, PDK revision, metal stack, die outline, seal-ring and sign-off/precheck rules should this design target?
2. Is the proposed junction geometry permitted for an optical test? What passivation, overlying metal/fill and optical keepout rules apply? We are not assuming any special optical opening is allowed.
3. Can dies be supplied or bonded with the nine junctions optically accessible? What encapsulant/window, bond-loop clearance and die-attach restrictions apply?
4. Does the chosen packaging route require the default pad ring? Are custom analog pad/protection cells acceptable, and who reviews bond geometry and protection compatibility?
5. What pad-coordinate/bond-map format, pad pitch, allowed bond metals, probe and handling requirements are required?
6. What review is available for protection of a 3.3 V sensor using the selected supply/analog-pad macros?

Record written answers, revision/date and supporting drawings before closing M2. Contacting a service or community is a separate action requiring explicit user authorization; this is a ready-to-review draft.
