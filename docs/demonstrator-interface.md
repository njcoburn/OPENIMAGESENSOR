# 3×3 electrical and board interface baseline

Recorded **2026-09-19 01:59 PDT**. Logical interface extracted from `sensor_3x3` in [integrated.spice](../circuits/integrated.spice). This is a design baseline, not a manufacturing-approved bond map or controller firmware specification.

[Machine-readable port worksheet](demonstrator-ports.csv) — names match all 19 schematic ports; pad IDs reference the user-approved working [placement proposal](pad-proposal.md); actual external names and connection states are in the [routed map](routed-pad-map.csv); connector numbers remain unassigned.

## Existing ports and board connections

| Core net | Count | Board function / baseline | Physical state |
|---|---:|---|---|
| VDD, GND | 2 | Nominal 3.3 V analog supply and return | Three VDD and four GND pads routed; final return/ESD qualification open |
| VRESET | 1 | Separate nominal 2.0 V reset source | Routed through primary and local secondary protection |
| RST0–RST2 | 3 | Controller reset outputs, active high | Routed through primary and local secondary protection |
| ROW0–ROW2 | 3 | Controller row selects, active high | Routed through primary and local secondary protection |
| SEL0–SEL2 | 3 | Controller one-hot column selects, active high | Routed through primary and local secondary protection |
| BIAS | 1 | 5.1 MΩ from VDD to column-reference input | Routed; assembled pad leakage requires verification |
| PREF | 1 | 49.9 kΩ from buffer-reference pin to GND | Routed through primary and local secondary protection |
| BUF | 1 | Buffered analog output to board ADC path | Routed; final ADC-loading verification pending |
| COL0–COL2, OUT | 4 | Unbuffered diagnostic nodes | Core nodes disconnected from diagnostic pads; no external probe access in this revision |

There are **19 core ports: 15 functional connections and four diagnostic nodes**. This is not a final bond-pad count: duplicate supply/ground pads and a decision on diagnostic access may change it. COL/OUT must not be assumed capable of driving a board trace; the four corresponding bond pads are intentionally disconnected in this revision. Provisional physical IDs and macro orientations are now in the [placement proposal](pad-proposal.md); the working arrangement is approved, while final manufacturing/bond approval, protection qualification and connector pins remain open.

## Baseline timing from the existing testbench

- Candidate supply soft-start: 1 ms, then 200 µs reset hold. VRESET ramps to 2 V; RST high tracks the powered supply. Do not drive an unpowered die.
- Keep row/column selects low through startup; preserve the initial 20 µs all-row reset in the established scan.
- Existing fixture uses 1 ms row increments and 3 ms frame increments; adjacent column slots are 18 µs apart, with 5 µs ADC acquisition.
- The saved sampling expression is `t = 1.2 ms + 0.975 ms + 3 ms × frame + 1 ms × row + 18 µs × col + 10 µs`, with zero-based indices. Source: [three-frame runner](../scripts/simulate-clamp-frames.py).
- These numbers reproduce earlier simulation; they are not a qualified maximum frame rate. Final edge timing, break-before-make, power-down/brownout behavior and controller logic levels need review against the routed pads and chosen ADC.

Sources: [board bias](board-bias.md), [clamp convergence](clamp-convergence.md), [coupled board supply](board-supply.md). Preserve the full existing waveform generator when implementing firmware; the sample-time expression alone is insufficient.

## Board work that can proceed independently

1. Draw supplies, VRESET source, bias resistors, nine controller outputs, analog BUF path, programming/debug and test points.
2. Select an ADC by input range, common-mode requirements, acquisition capacitance/time, reference accuracy and controller interface. Existing 100 pF board / 20 pF sampling-capacitor and 5 µs acquisition assumptions are test loads, not a selected ADC. Do not select by nominal resolution alone.
3. Allocate pad/board leakage at BIAS: 1% of 0.5 µA is only 5 nA. Account for protection, contamination, temperature and measurement loading.
4. Plan low-noise supplies, local decoupling, ground returns and optional ADC driver footprints. Existing source R/L and capacitor ESR/ESL are assumptions, not selected components.
5. Produce a bond diagram and mechanical optical-access drawing after packaging requirements are confirmed.
6. Bench plan: continuity/current-limited startup, reference/bias measurement, electrical readout, dark frames, stepped illumination/exposure, repeatability and pixel variation.

Open decisions: ADC/controller parts, regulator/reference parts, physical package, any future diagnostic connection, final bond geometry and acquisition timing. No new component purchase or package suitability is implied by this baseline.
