# GF180 shuttle references and the actual blocker

Checked 2026-09-19 13:02 PDT.

## The issue, plainly

**Our detailed simulation of the pad-ring protection circuit stops before it produces a trustworthy startup result. We have not demonstrated a faulty pad layout.** This blocks our current complete-chip startup qualification. It does not erase the earlier pixel/readout results or physical DRC/LVS checks. A separate ngspice 47 multiplier parser issue is reproducible without a PDK; it is not the cause of the multiplier-free extracted failure.

## References actually inspected

| Reference | Evidence | Relevance and limit |
|---|---|---|
| [Tiny Tapeout GF 0.2](https://github.com/TinyTapeout/tinytapeout-gf-0p2), listed in wafer.space Run 1 | Pinned multiplexer revision `30c3f44bcb23ffdad2c2f97edd4c4fe3fc6a87bf`. Its `rtl/tt_gf_gpio.v` instantiates foundry `asig_5p0`, `dvdd`, `dvss` and digital I/O cells. Build config uses 3.3 V and GF180 foundry I/O timing libraries. | Direct pad-family and integration reference. Reviewed GF180 build files provide implementation/timing verification, not our detailed ESD-clamp transient fixture. |
| [JKU1 wafer.space chip](https://github.com/iic-jku/gf180mcu-jku-projects) | Authors report successful bring-up at 3.3 V or 5 V. Inspected repository revision `ebfc69daad23bf42182ae617398ee436d9ae05b5`; its Makefile selects historical PDK tag 1.6.6. Top-level uses `gf180mcu_ws_io__dvdd/dvss`, with supply/return ports tied as shown in source. | Strong reference for a working packaged chip. Its documented simulation uses cocotb/Icarus RTL and gate-level checks, not complete transistor-level ESD startup. Current repository source is not proven identical to the fabricated release merely by the README. |
| [Historical wafer.space PDK 1.6.6](https://github.com/wafer-space/gf180mcu/tree/1.6.6) | Resolved commit `fb4b8f59451d248ef5b310a593759f946a8f6ae8`. Downloaded `gf180mcu_ws_io.spice`. | After renaming only the `ws_io` cell prefix to `fd_io` and trimming outer whitespace, the two supply-pad netlists **exactly match our archived foundry supply-pad netlists**. No alternative capacitor fix appears here. |
| [ISHI-KAI wafer.space analog projects](https://github.com/ishi-kai/ISHI-KAI_Multiple_Projects_WaferSapce-GF180-1) | Public analog schematics/layouts, links to SAR ADC/LDO/PLL/BGR/OPAMP projects and a configured simulation environment. | Useful analog-block and probing references. The inspected parent files do not establish a passing full pad-clamp transient test. Child projects were not comprehensively audited. |
| [OCD I/O library](https://github.com/RTimothyEdwards/gf180mcu_ocd_io) | Pinned `6e0e354a78793339a4a004a6d9c08990d0eee3e4`; inspected corner and supply schematic netlists. | Still uses `cap_nmos_06v0` with explicit multipliers. It is not an obvious escape from the capacitor-model issue. No switch to this library is proposed on present evidence. |

[wafer.space Run 1 roster](https://github.com/wafer-space/ws-run1) establishes shuttle participation. A submitted or fabricated layout alone is not evidence of a particular analog simulation passing. [Current wafer.space PDK notice](https://github.com/wafer-space/gf180mcu) says the development fork is superseded by upstream open_pdks/Ciel; the old tag was inspected as a historical reference, not installed as our new development environment.

## Recommended way forward

Keep the standard physical pad macros and use the published supply connections as the integration reference. There is no evidence here that we should invent a new pad or corner.

Separate two deliverables explicitly:

1. **Camera functional qualification:** extracted 3×3 pixels, bias, mux and output buffer, with signal-pad loading, supply impedance, leakage and capacitance represented by justified normal-operation models and uncertainty bounds. Verify repeated frames, settling, PVT and ADC loading. Any omitted protection dynamics must be named and bounded; an arbitrary capacitor or short is not an accepted substitute.
2. **Protection/startup qualification:** retain the actual protection devices in physical LVS/DRC, and track the unresolved detailed startup simulation and ESD/application review separately. No ESD robustness or unrestricted complete-chip qualification can be inferred from the first deliverable.

This separation is our engineering recommendation informed by the references, not a claim that these teams used our proposed analog load model or that the numerical failure is solved. This turn changes no acceptance gates and runs no new solver sweep. Next implementation work should define and validate the normal-operation interface model before using it to qualify the camera; obtain separate evidence for the remaining protection/startup requirements before fabrication release.

## Saved evidence

[Source snapshots and comparison](../checkpoints/gf180-reference-survey/evidence.tar.gz). The archive includes pinned source-tree metadata, downloaded files, a source URL/hash list, and the supply-netlist diff. Additional wrapper sources resolve to commits explicitly listed above. Working PDK, GDS and netlists remain unchanged.
