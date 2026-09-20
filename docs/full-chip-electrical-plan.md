# Complete-chip electrical qualification plan

Target: final filled GF180 3×3 demonstrator, 24-pad ring, 20 × 20 µm photodiodes. Keep the existing wire-bonded carrier. See [target hashes and status](../simulations/full-chip-qualification.json).

**An isolated clamp success, device LVS, and a board DRC pass are separate from full-chip electrical qualification.**

## 1. Qualify the numerical candidate

- Preserve the original PDK and archived failing results.
- Resolve the standalone control's fast ramp-stop transient and compare original/scaled current at native time points against an independent terminal-equation reference.
- Check resolution, integrated charge and all model options actually used before promoting the internal scaling to a general replacement.
- Complete the isolated extracted clamp and pass fixed timestep/tolerance comparisons; include startup and load-edge behavior in review, not only the final DC point.
- Repeat the necessary capacitance-placement sensitivity checks and complete-pad-ring checks. The 144-device fixture is not the assembled ring.

The new [control-resolution audit](clamp-control-reference.md) is evidence for this gate. A passing local diagnostic does not modify the foundry model or authorize a fabrication claim.

## 2. Establish an accepted model of the exact final GDS

The final filled GDS has recorded scoped physical checks. Its saved LVS netlist deliberately omits wiring capacitance and resistance. Do not relabel that file as an RC extraction.

- Extract the final geometry with recorded GDS, tool and PDK hashes.
- Preserve devices, resistance and the original capacitance matrix; audit substrate/ground domains.
- Address the previously recorded native capacitance-export limitations. Any reconstructed capacitance placement remains an approximation until its settling sensitivity is bounded.
- Verify charge/matrix accounting, resistor-reduction port behavior and device/net connectivity independently.
- Keep a device-only baseline to separate circuit behavior from parasitic effects.

## 3. Nominal full-chip acceptance

Use the actual pad-side interface and local protection, not direct ideal drives on internal core nodes. The [nine-pixel topology map](final-chip-pixel-map.csv) identifies photodiode stimulus nodes from the final LVS netlist; its source hash is recorded in [the mapping manifest](../simulations/final-chip-pixel-map.json). Revalidate those node identities against the accepted electrical extraction before applying light currents.

- Apply finite-impedance supplies and defined reset, row and multiplexer startup states.
- Verify supply/clamp/bias settling and currents, including external 5.1 MΩ BIAS and 49.9 kΩ PREF networks and VRESET behavior.
- Capture three complete frames: nine samples/frame, brightness ordering and valid reset/readout sequence.
- Retain earlier screens: <0.5 mV sample tracking error, <50 µV frame-two/three difference, <10 µV sample refinement difference, bias within 1% of settled values.
- Treat these as electrical engineering acceptance screens, not measured optical specifications.

## 4. Process, supply, temperature and external loads

Repeat the accepted full-chip test on the selected model corners, supply bounds and temperature range; explicitly list any missing combinations. Include finite source impedance, output loading and timing margins.

Separate two acquisition modes:

1. The earlier fast analog acquisition fixture (18 µs column slots / 5 µs acquisition) remains a regression baseline, not an ADS1115 timing model.
2. The board's slow ADS1115 mode requires holding selection through conversion and accounting for continued photodiode integration. Verify the external buffer/filter and the converter's input behavior before interpreting samples as images.

## 5. Archive and independent review

Freeze the accepted GDS, extracted model, model provenance, scripts, waveforms and acceptance report together. Review power-up and protection assumptions independently. Simulation qualification does not establish ESD survival, package optical access or measured QE; manufacturing/optical closure remains separate.

No further blind solver sweeps follow a failed refinement batch. A specific new diagnosis or evidence is needed for a new bounded experiment.
