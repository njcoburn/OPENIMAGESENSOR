# Manufacturing and optical-access review

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
