# Removable sensor fixture — engineering prototype

Updated 2026-09-19. **Not released for fabrication.** Dimensions below are design proposals, not a qualified package drawing.

## Mechanical arrangement

The 100 × 80 mm tester sits above the 40 × 40 mm removable carrier. The carrier's die and bond wires face upward through the tester's 22 × 22 mm opening. Spring contacts fitted on the tester's underside press against the carrier's top copper targets. They never touch the die or bond wires. Four screws and rigid spacers retain the carrier; do not use screw torque to set spring compression.

| Feature | Proposed dimension |
|---|---:|
| Removable carrier | 40 × 40 mm |
| Tester | 100 × 80 mm |
| Clear aperture | 22 × 22 mm |
| Four mounting holes | Ø3.2 mm, 32 × 32 mm pattern |
| Contact targets | Ø2.4 mm, 3.5 mm pitch, six per side |
| Contact count | 24 positions; 18 electrically used at the dock |
| Asymmetric alignment features | Ø2.05 mm round hole and 3.05 × 2.05 mm slot |
| Nominal die drawing | 1.210 × 1.210 mm |
| Bond fingers | 0.32 × 1.2 mm, 0.55 mm pitch; provisional |

Exact XY coordinates are in [mechanical.json](kicad/mechanical.json). Both board files use a common top-view coordinate system; the boards face the same direction, so the contact pattern is not mirrored. The dock spring footprints are on its bottom side. The asymmetric round/slot locations require matching locating hardware to prevent a rotated assembly; holes alone do not prevent misassembly.

### Items that must be resolved before ordering

- Confirm the selected spring contact's manufacturer drawing, installed height, recommended working stroke, hole tolerance and solder process. Candidate: Mill-Max **0906-0-15-20-76-14-11-0**. The current footprint uses a 0.6 mm finished hole and 1.6 mm pad. The manufacturer's [spring-contact drawing collection](https://www.mill-max.com/sites/default/files/external/catalog/2019-04/023M-028M.pdf) is the authority; the spacer height is deliberately not released yet.
- Choose board thickness, rigid stops and locating pins as one tolerance stack. Check compressed springs, die/bond-wire height, underside parts, and screw-head clearance in 3D.
- Have the wire-bond provider approve finger dimensions, bondable metallization, die attach, die orientation, loop height and cleaning. Ordinary PCB finish must not be assumed suitable for their bonding process.
- Specify a contact finish and wear lifetime for repeated pogo use. Bond fingers and pogo targets may require different finish requirements.
- Keep the photosensitive die uncovered; any protective window, cavity cover or encapsulant must preserve optical access. Provide handling protection around exposed bond wires.

## Electrical population

The carrier holds only the die, 5.1 MΩ BIAS resistor, 49.9 kΩ PREF resistor and 100 nF local supply bypass. **P03 and P08 pogo positions are reserved/unconnected**: their die pads connect to these local resistors instead. P10/P11/P12/P15 remain unconnected diagnostic positions. This differs intentionally from simply extending every die pad through a connector.

The tester contains:

- External, regulated, current-limited 3.3 V input at J2; no onboard regulator.
- Two SN74LVC244A buffers with disabled-by-default output enable, 100 Ω series resistors, and chip-side pulls (reset high; row/column selects low).
- OPA2320 dual follower: one channel drives the ADC path; the other buffers a 13 kΩ / 20 kΩ divider to produce nominal 2.0 V VRESET from 3.3 V. This is ratiometric, not an independent precision reference.
- ADS1115, address 0x48; AIN0 reads the buffered pixel output. A 100 Ω / 10 nF input network has nominal 1 µs RC. Driver stability, supply behavior and settling still require verification.
- J1 timing header, J3 I²C/enable header, and J4 analog expansion for a faster external ADC. J4 is not intended for a 50 Ω termination.

See each project's `bom.csv` and `design.json` for exact values, pin assignments and positions. Ground-return routing, decoupling loop lengths, connector keying and power sequencing are review items; an automatically connected netlist does not qualify analog performance.

## First assembly and test

1. Inspect bare boards and measure shorts/continuity with no die attached. Verify every pogo position against the carrier and the routed chip pad map.
2. Populate the dock; leave the die carrier disconnected. Keep IO_OE_N high. Apply a current-limited 3.3 V supply and verify rails, VRESET, logic defaults and ADC communication.
3. Test the ADC path with a known voltage source and realistic source/loading conditions. Check buffer stability and ADC noise.
4. Validate controller startup/reset sequencing on the scope. Do not connect a powered controller to an unpowered fixture without checking the complete back-power paths, including I²C.
5. Turn all power off before installing or removing a carrier. After installing a bonded die, begin with current limits and dark measurements.
6. Validate a slow single-pixel conversion sequence, then scan nine pixels; retain raw samples and timestamps. The unresolved full-chip clamp-model review remains separate from this board work.
