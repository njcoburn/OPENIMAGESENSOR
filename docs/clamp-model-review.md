# Local clamp-model review

**Follow-up 2026-09-19 09:34 PDT:** A new independent terminal-equation audit identified insufficient resolution in the old standalone control. Locally refined controls pass; the scaled extracted clamp completes and passes isolated voltage refinement, and both larger corner placements complete. See [current evidence](scaled-electrical-progress.md). Full-chip qualification remains open. Earlier failure observations below are retained as history; no upstream confirmation or accepted general PDK fix is claimed.


Reviewed **2026-09-19 04:08 PDT**. Local engineering review; **not an independent expert endorsement and not sent externally**.

## What is unresolved, in plain language?

The pad ring includes supply-protection clamps. Their startup behavior must be included in the camera's complete electrical model. The saved extracted-clamp simulation sometimes stops with “timestep too small.” One coarse run finishes, while smaller timestep checks fail. That prevents us from trusting the complete-chip startup and sampling results.

This is **not a demonstrated defective chip or defective foundry model**. Passing DRC/LVS verifies geometry/connectivity; it does not establish transient simulation accuracy or ESD performance. The issue was narrowed to a smaller 144-device extracted fixture, but that fixture is not the final filled 24-pad camera.

## What the review checked

- Re-read the saved failure logs, test settings, model provenance and earlier standalone controls. The original 24 standalone capacitor fixtures completed; the smaller extracted clamp remained timestep-sensitive.
- Verified that the installed model SHA-256 matches the earlier reproducer's recorded model hash.
- Parsed the actual ngspice 46 expanded standalone netlist with `listing e`, without running a transient during that inspection.
- Found that `ec_moscap` is a simulator-generated helper voltage source, not a fabricated device name. The expansion includes an internal **1 F** capacitor and a behavioral source that scales its current by the much smaller physical capacitance. This is an observed implementation detail, not proof of the failure's cause.
- Ran one original/scaled standalone pair at the existing settings. No PDK files, physical GDS, extracted wiring, solver tolerances or full-chip acceptance criteria were changed.

The official [ngspice manual, §3.3.9](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) documents capacitance- and charge-expression forms and illustrates the helper-source implementation. The installed version-46 expanded listing is the evidence for this project's actual implementation; the online manual currently identifies version 47.

## Exact hypothesis and limits

For the 25 × 10 µm typical NMOS capacitor, the installed equation is:

`C(v) = area × corner × (0.001107 + 0.00107 × tanh(6.25v − 4.1875))`.

The observed expansion differentiates the reversed terminal voltage with a 1 F helper capacitor and returns the scaled current to the physical terminals. The diagnostic replaces that **internal helper** with 1 pF and divides the behavioral current gain by 1 pF. Algebraically, the terminal law remains `i = C(v) × dv/dt`. It does not replace the physical voltage-dependent capacitor with a fixed capacitor.

The hypothesis is that reducing the internal current scale could improve numerical conditioning. Algebraic equivalence alone is insufficient: numerical output must agree, including current/charge and refinement. This test covers only the selected typical, 27 °C fixture; it does not validate all model options, temperatures or corners.

## Bounded diagnostic results

| Check | Result |
|---|---|
| Original standalone transient | Completed to 153 µs |
| Rescaled standalone transient | Completed to 153 µs |
| Maximum terminal-voltage difference | 2.708 µV (screen: 10 µV) |
| Maximum source-current difference | 2.708 nA (screen: 0.1 nA) — fails |
| Extracted-clamp rescaling trial | **Not run** because its prerequisite current comparison failed |
| Accepted fix | **None** |

Differences use linear interpolation onto the union of adaptive output times. These maxima can include interpolation effects near sharp waveform changes; they do not prove that the algebraic models represent different physical capacitance. They do establish that this test has not demonstrated the required numerical agreement. No charge-equivalence claim is made. The current limit is a diagnostic comparison gate, not a fabricated-chip specification.

The two-test budget ended at this failed prerequisite. No follow-on scaling, tolerance, timestep or solver sweep was launched. The previous stop rule remains in place; this narrowly scoped test was justified by new evidence from the actual expanded equations.

## Specific questions for independent review

1. Is this exact E/C/B expansion's internal scaling a credible source of the extracted clamp's failure, given that the simple controls complete?
2. How should helper-branch convergence and truncation error be diagnosed without changing terminal behavior?
3. Is a charge-form or other model-equivalent implementation appropriate? If so, how should current/charge equivalence and sharp-edge interpolation error be verified?
4. Which controlled test best separates numerical conditioning from the reduced extracted fixture's topology and loading?

Provide both the [original reproducer](../checkpoints/clamp-review/reproducer.tar.gz) and [new audit evidence](../checkpoints/clamp-model-review/evidence.tar.gz). The [existing review brief](reviews/clamp-startup-review.md) remains the request context. An external expert has **not** yet received or answered this packet.

## What is needed to close this

An accepted explanation/fix must pass matched current/charge tests and timestep/tolerance refinement, both recorded capacitance placements, and then the full assembly's startup, repeated frames, PVT and ADC-load tests. The final filled camera needs its own accepted extracted model. No layout redesign is justified solely by this simulator error.

No new tools are needed for the completed local review. Independent review needs a reviewer/contact or a public issue posted by the user. No message or public issue was sent in this step.

## Reproduce

```sh
bash scripts/run-tools.sh python3 scripts/review-clamp-scaling.py
python3 scripts/report-clamp-model-review.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The bounded runner preserves the archived original inputs and applies a 120-second watchdog per case. Its optional clamp test only runs if both standalone comparison limits pass. All saved results, including the failed comparison, are in the checkpoint manifest.
