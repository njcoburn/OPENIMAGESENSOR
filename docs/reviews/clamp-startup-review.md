# Draft expert review: GF180 extracted-clamp transient failure

**Follow-up 2026-09-19 09:34 PDT:** A new independent terminal-equation audit identified insufficient resolution in the old standalone control. Locally refined controls pass; the scaled extracted clamp completes and passes isolated voltage refinement, and both larger corner placements complete. See [current evidence](../scaled-electrical-progress.md). Full-chip qualification remains open. Earlier failure observations below are retained as history; no upstream confirmation or accepted general PDK fix is claimed.


Prepared **2026-09-19 02:01 PDT**. **Local draft; not sent.**

## Request

Please review a reproducible ngspice startup failure in a reduced extracted GF180 supply-clamp group. We need a numerically justified solution that preserves the foundry device equations and terminal behavior. We are not claiming a confirmed simulator or PDK defect.

## Reproducer and observations

- [Portable evidence archive](../../checkpoints/clamp-review/reproducer.tar.gz), with decks, logs, saved waves, replay runner, initialization and model hashes.
- Pinned container: `hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a`. Recorded logs identify ngspice 46.
- 144 device records, 22,575 resistors, 127 explicit wiring capacitors; other semiconductor groups omitted. The smaller resistor reduction passes current comparisons with maximum relative error 9.15e-14.
- The reported `X354` is a 25 × 10 µm `cap_nmos_06v0`. Simple one/eight-capacitor fixtures all complete (24 cases).
- Direct Gear/100 ns aborts near 127.352 µs in another capacitor of the bank. Trapezoidal/100 ns completes to 153 µs, including the load pulse.
- Trapezoidal/50 ns aborts near 125.330 µs; stricter 50 ns aborts near 119.488 µs, both naming `e.x354.ec_moscap#branch`.
- Final SPARSE-only replacements of the two 50 ns decks each time out after 120 seconds. They are incomplete, not evidence that SPARSE can never converge.
- No accepted numerical fix. Local solver experimentation is stopped after this bounded batch.

## Questions for the reviewer

1. Does the behavioral-capacitor conversion or matrix conditioning explain failure near the settled state? How can we distinguish the cause with a controlled diagnostic?
2. Are the initialization, compatibility (`ngbehavior=hsa`, `wnflag=1`) and nonlinear-capacitor treatment appropriate for this installed PDK?
3. What targeted solver/model-equivalent reformulation should be tested, and how should terminal charge/current equivalence be demonstrated?
4. Is an independent extraction or simulation cross-check warranted before applying this to the full ring?

## Acceptance before adoption

Complete startup and load traces for both original capacitance placements, timestep and tolerance refinement, preserved terminal current/charge behavior, and full-corner regression. No capacitor substitution, artificial shunt, discarded parasitic, or relaxed tolerance is accepted solely because it makes a run finish.

Context: [isolation report](../moscap-branch.md), [extraction reference](../charge-reference.md), [completion plan](../../COMPLETION_PLAN.md).

## Local audit follow-up — 19 September 2026

[Model-expansion audit and bounded rescaling test](../clamp-model-review.md): the original and scaled standalone cases complete, but maximum current disagreement is 2.71 nA against the 0.1 nA screen. No extracted-clamp trial or accepted fix follows. This is new diagnostic evidence for review, not external expert feedback. The additional [evidence archive](../../checkpoints/clamp-model-review/evidence.tar.gz) accompanies the original reproducer.
