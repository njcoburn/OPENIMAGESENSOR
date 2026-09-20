# Ring-section audit with the combined extraction candidate

Recorded **2026-09-18 23:55 PDT**.

**The combined resistance corrections do not make the corner RC model ready for transient simulation.** Fresh filler and corner extraction completes with baseline and combined executables, using both full-device and conductor-only geometry. Four full-device LVS checks pass, and all 32 resistor-only rail solves pass connectivity and current-balance checks. The corner still fails the extracted-capacitance energy test.

![Matched ring resistance comparison](assets/ring-candidate.png)

| Build | Coupon | Geometry | Negative capacitors | Negative-energy nodes | Ground rails connected |
|---|---|---|---:|---:|---|
| baseline | fill10 | full | 0 | 0 | False |
| baseline | fill10 | metal | 4 | 4 | False |
| baseline | corner | full | 5 | 5 | True |
| baseline | corner | metal | 136 | 136 | False |
| combined | fill10 | full | 0 | 0 | False |
| combined | fill10 | metal | 4 | 4 | False |
| combined | corner | full | 5 | 5 | True |
| combined | corner | metal | 132 | 132 | False |

## What the capacitance failure means

For each node we sum every incident capacitor to obtain its diagonal entry in the capacitance matrix. Set that node to 1 V and every other node to 0 V. The stored energy is one-half the diagonal capacitance. A negative diagonal therefore supplies a direct negative-energy witness: no eigenvalue fitting or deletion of small capacitors is needed.

Candidate full corner example: `VDD_B.n7152`, diagonal **-0.00949 fF**, energy **-4.745e-18 J** at 1 V. These are internal extracted nodes with finite resistive connections, not nodes constrained together by ideal shorts. This rejects the raw parasitic capacitance network as a passive model; it does not by itself prove instability of a complete transistor circuit, whose device capacitances also contribute.

The negative values are already present in the raw `.res.ext` rnode capacitance fields, before SPICE export. This narrows the investigation to resistance extraction/capacitance redistribution rather than only the SPICE reader. Matching raw records are archived.

Negative entries and exact witness nodes are preserved in `simulations/ring-candidate.json`. Signed zero entries are not counted as negative. No capacitor was clamped, removed or redistributed. We did not attempt a corner transient or use this extraction to qualify the camera.

## Substrate connections and LVS scope

The full corner's `.ext` aliases VSS and DVSS; its resistor mesh joins the ground rails. The conductor-only corner retains separate rails. This localizes the distinction to semiconductor extraction rather than a metal-only short, but does not establish the physical accuracy of the substrate resistance model.

Corner device LVS uses tied analog supplies, matching the existing ring use: both VDD names map to AVDD and both ground names map to AVSS for that comparison. Filler LVS keeps four macro ports. DC audits separately reject supply-to-ground paths and supply-rail shorts before that LVS mapping. Passing LVS does not validate capacitance or independent corner-domain operation.

The same 0.4 µm external M5 leads and terminal fixtures are used for each matched comparison. Resistances include those leads and cannot simply be added into a full-ring model. Raw extraction diagnostics, including grid snapping and any `Missing rptr` messages, are retained in the audit. No new DRC is claimed for these diagnostic coupons.

## Decision and next work

Keep the candidate isolated. Its resistance fixes pass the earlier controls and block regressions, but neither fix addresses the corner's capacitance redistribution.

1. Trace each negative corner shunt back through `.res.ext` and Magic's capacitance redistribution code; check charge conservation against the pre-resistance `.ext` network.
2. Build a minimal reproducible capacitor-redistribution control, including the semiconductor reference node.
3. Require a passive, charge-conserving extracted model and justified substrate treatment before reduced-RC corner transients, stitched sections, or full-ring extraction.

Production ring GDS and installed tools remain unchanged. The source-code patches remain diagnostic, not a production tool adoption.

## Reproduce

Prerequisites are the previous ring-section coupon generation and combined executable checkpoint.

```sh
bash scripts/run-tools.sh python3 scripts/extract-ring-candidate.py
for variant in baseline combined; do
  bash scripts/run-tools.sh python3 scripts/audit-ring-sections.py --cases fill10 corner --work-dir build/ring-candidate/$variant --output build/ring-candidate/$variant/dc-audit.json
done
bash scripts/run-tools.sh python3 scripts/audit-ring-capacitance.py
bash scripts/run-tools.sh python3 scripts/report-ring-candidate.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The checksummed archive `checkpoints/ring-candidate/evidence.tar.gz` retains coupon GDS, command inputs, raw extraction, RC netlists, diagnostics, DC/LVS audits, capacitance witnesses, scripts and results. Executables and PDK remain dependencies from the pinned environment and previous checkpoint; binary and GDS hashes are recorded for each extraction.
