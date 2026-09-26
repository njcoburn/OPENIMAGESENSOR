# Finish the 3×3, then scale to 64×64

**Superseded planning sequence — 2026-09-25:** the user now targets 64×64 first silicon on wafer.space GF180 at a modest frame rate. The [current plan](../COMPLETION_PLAN.md) and [slot-fit study](64x64-slot-fit.md) take precedence. Compact pixel/bank geometry is required; a separate 3×3 tapeout is not a prerequisite. The earlier scope and evidence below are preserved.

Decision guide — 19 September 2026. No geometry changes made.

## Purpose of the issue

The public issue seeks a focused diagnosis of the supply-protection clamp's timestep-sensitive startup simulation. It does not assert that the chip or PDK is defective. The issue is prepared, not posted. The local model-rescaling test did not meet its current-agreement screen. Passing DRC/LVS establishes geometry/connectivity, not transient accuracy or ESD qualification.

## Completion sequence

1. **Electrical review:** post the prepared issue and use specific feedback to choose the next bounded diagnostic. Preserve the original model; do not accept an omitted clamp or relaxed tolerances as final qualification.
2. **Proceed alongside that review:** prepare the carrier/controller/ADC block schematic and pin mapping; confirm supplies, reset reference, external bias resistors, timing, analog output and test points. Select a run/bonding route and obtain optical-access, die, seal-ring and pad-opening requirements.
3. **Electrical release:** qualify an accepted extracted model of the final filled assembly. Check startup, repeated frames, PVT and the intended ADC load against COMPLETION_PLAN.md limits.
4. **Physical release:** apply final manufacturing requirements, rerun affected physical checks, and obtain independent release review.
5. **Measured demonstrator:** fabricate, bond and measure nine-pixel dark/light response, exposure dependence, reset recovery, noise, pixel variation, saturation and spectral response.

The current working layout passes scoped main DRC, density, antenna and LVS. Fabricated optical measurements do not yet exist. Board and manufacturing planning need not wait for the clamp review. This guide does not send messages or authorize purchases/submission.

## Larger photodiodes and QE

The current junction is **20 × 20 µm**, area 400 µm², at **80 × 50 µm pitch**: a **10% geometric fraction**, before shadowing. The earlier 5/10/20 µm comparison used assumed photocurrent density, not measured QE.

More exposed diode area can collect more photons at fixed irradiance. This does not automatically increase the fraction of photons incident on the junction that become collected electrons. Pixel-level effective QE can improve with fill factor; specify which incident-photon area is used. Sources: [Hamamatsu detector-selection guide](https://hub.hamamatsu.com/us/en/technical-notes/detector-selection/the-wits-guide-to-selecting-a-photodetector.html), [EMVA definition including fill factor](https://www.emva.org/wp-content/uploads/EMVA1288-3.1a.pdf).

Larger area also increases capacitance. Our integrating pixel approximately follows `ΔV = Iphoto × exposure / Csense`; increased photocurrent therefore need not yield proportionally increased voltage. Leakage, capacity and settling also need evaluation. [Hamamatsu photodiode technical note](https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/ssd/si_pd_kspd9001e.pdf).

The original `test.py` defines an **N-well/substrate** detector, with a default 5 µm width and later added/merged N-well geometry. The verified demonstrator uses **N+/substrate** (`diode_nd2ps_03v3`). This is a junction-type difference, not simply a larger interchangeable diode. An N-well alternative needs its own extraction, capacitance, isolation, optical and design-rule evaluation.

Recommendation: preserve the verified 20 µm 3×3 baseline. For the camera pixel, compare larger diode area against a smaller transistor/routing footprint, and separately investigate the original N-well junction. Select from measured sensitivity/noise and available area. Optional diode test structures on the first die could compare alternatives, but require an explicit layout revision and renewed verification.

Actual QE requires calibrated photon flux at a known wavelength and a collected-charge measurement or calibrated conversion gain. An uncalibrated LED test demonstrates light response, not QE. Record the wavelength, exposure and optical/package transmission.

## Scaling to 64×64

**Yes: 64×64 is a sensible second generation after the 3×3 is validated.** It is not simply tiling the present demonstrator.

| Pixel-pitch assumption | Array-only size |
|---|---|
| Existing 80 × 50 µm | 5.12 × 3.20 mm |
| Proposed 40 × 40 µm | 2.56 × 2.56 mm |

Both exclude pads, protection, readout/control circuits and seal ring. The 40 µm pixel remains a target, not a verified design. No run/slot is selected, so neither footprint implies manufacturing acceptance.

The larger sensor needs scalable row/reset addressing, a 64-column readout/multiplexer strategy, and validation of longer-line capacitance, settling and crosstalk. Keep the ADC external initially. At 30 frames/s, one sample per pixel requires `4096 × 30 = 122,880 samples/s` before overhead. Sampling reset and signal separately doubles that count. Choose actual frame rate and ADC from the analog settling/noise budget.

Before full-array implementation, verify an intended-length loaded column or representative strip. Then implement and extract 64×64 and repeat electrical/physical qualification. Use measured optical results—or an explicitly accepted optical-risk decision—to freeze its junction type and pixel geometry.

**Immediate priority:** focused clamp review plus carrier/interface and optical-packaging planning. Finish the 3×3 as a measured technology demonstrator; keep the 64×64 redesign separate.
