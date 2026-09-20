# ngspice 46 / GF180: extracted supply-clamp transient fails timestep refinement at MOS-capacitor helper branch

## Controlled-version update — 2026-09-19 11:30 PDT

[Matched ngspice 46/47 results](../ngspice-version-comparison.md): standalone controls pass, both extracted stock-model runs fail at startup. An unextracted v47 corner also hits a separate parser issue, isolated in a [PDK-free draft](ngspice47-cap-multiplier-issue.md). The parser issue does not explain the multiplier-free extracted failure. No upgrade or candidate is accepted; nothing has been posted.

## Latest evidence — 2026-09-19 10:02 PDT

The matched standalone control now passes (1.493 pA difference), and isolated-clamp refinement passes. Both complete-corner 50 ns runs finish, but 25 ns with reltol=1e-7/abstol=1e-14 aborts at the 151 µs load onset (two 1 mA pulses, 1 ns rise), in `e.x354.ehelper#branch`, timestep 3.125e-20 s. The step and tolerance changes are combined, so this does not isolate their individual effects. See [current evidence](../scaled-electrical-progress.md) and [saved runs](../../checkpoints/scaled-electrical-progress/evidence.tar.gz). These supersede the older control-failure diagnosis below. This remains a draft; nothing has been posted.


**Follow-up 2026-09-19 09:34 PDT:** A new independent terminal-equation audit identified insufficient resolution in the old standalone control. Locally refined controls pass; the scaled extracted clamp completes and passes isolated voltage refinement, and both larger corner placements complete. See [current evidence](../scaled-electrical-progress.md). Full-chip qualification remains open. Earlier failure observations below are retained as history; no upstream confirmation or accepted general PDK fix is claimed.


## Summary

We would appreciate guidance on diagnosing a timestep-sensitive transient failure in an extracted GF180MCU supply-protection clamp. A 100 ns trapezoidal run completes, but otherwise matching 50 ns runs abort with “timestep too small,” naming a generated MOS-capacitor helper branch.

We have not established a simulator or PDK defect. We are looking for a controlled diagnostic or model-equivalent formulation whose terminal current/charge behavior can be verified, rather than accepting completion at a looser numerical setting.

Attached:

- `reproducer.tar.gz`: original decks, logs, saved traces, replay script and model provenance.
- `model-review-evidence.tar.gz`: subsequent expanded-model inspection and bounded standalone rescaling experiment.
- `SHA256SUMS`: attachment hashes.

Project context: an open GF180 monochrome image-sensor demonstrator, https://github.com/njcoburn/OPENIMAGESENSOR. The attached fixture is a reduced diagnostic from an earlier clamp extraction, **not the final camera or a full-chip equivalent**. The attachments contain the evidence needed here; no unpublished repository files are needed for the original replay.

## Environment and fixture

- ngspice 46, KLU for the baseline.
- Pinned image: `hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a`.
- GF180MCU D installed model: `/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice`.
- Model SHA-256: `f6f4a96e18fc5ad11270ad3451aaecc7ac37fc81eb61e15b0d7d94c7bc594a24`.
- Initialization: `set ngbehavior=hsa`, `set wnflag=1`.
- Typical MOS/diode/resistor/MOS-capacitor sections, 27 °C.
- 144 device records, 22,575 resistors and 127 explicit wiring capacitors. Other semiconductor groups were omitted during isolation; the resulting fixture is not electrically equivalent to the full corner.
- A second resistor-only reduction passed seeded terminal-current comparisons, with maximum relative error 9.15e-14. This checks that reduction, not the original extraction or omitted semiconductor loading.
- Supply: linear 0–3.3 V ramp over 100 µs through 2 Ω, two 100 kΩ standby loads, and two 1 mA load pulses beginning at 151 µs. The archived deck contains the complete connections and stimuli.

Baseline options:

```spice
.options gmin=1e-17 reltol=1e-6 abstol=1e-12 chgtol=1e-16 trtol=3 method=gear
.options method=trap
```

The second line selects trapezoidal integration; the inherited first line remains in the saved deck. The control section selects KLU and uses:

```spice
tran 50n 153u 0 50n uic
```

`uic` skips the operating point. We have not established whether that initialization is appropriate for every internal state of this extracted fixture.

## Reproduce

Extract the **original** attachment into an empty directory:

```sh
mkdir clamp-repro
tar -xzf reproducer.tar.gz -C clamp-repro
cd clamp-repro
```

Then run:

```sh
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" -w /work --entrypoint /bin/bash \
  hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a \
  -lc 'python3 run.py klu-trap-50ns'
```

The runner writes new files under `replay/`, preserves the original evidence under `cases/`, and returns failure for an aborted or timed-out run. Its default watchdog is 120 seconds; runtime depends on hardware. `--timeout 180` can be passed after the case name to allow the original diagnostic budget.

For the completed coarse comparison, substitute `klu-trap-100ns`. The archive also contains `capacitor-control`, `klu-gear-100ns`, `klu-trap-50ns-strict`, and the two `sparse-*` cases. The PDK is supplied by the pinned image, not redistributed in the original reproducer.

## Observed versus expected

Expected: complete the 153 µs startup/load test with repeatable terminal behavior under timestep/tolerance refinement. Completion alone is insufficient to accept the model.

| Case | Recorded outcome |
|---|---|
| Gear, 100 ns | Aborts near 127.352 µs, naming another MOS-capacitor helper branch |
| Trapezoidal, 100 ns | Completes to 153 µs |
| Trapezoidal, 50 ns | Aborts near 125.330 µs |
| Trapezoidal, 50 ns; `reltol=1e-7`, `abstol=1e-14` | Aborts near 119.488 µs |
| SPARSE replacing KLU in each 50 ns case | Both time out after 120 seconds |

The ordinary 50 ns failure includes:

```text
doAnalyses: TRAN:  Timestep too small; time = 0.00012533, timestep = 6.25e-20: trouble with node "e.x354.ec_moscap#branch"
tran simulation(s) aborted
```

A timeout is an incomplete result, not proof that SPARSE cannot converge. We have not performed a controlled cross-version comparison.

## Isolation and model inspection

`X354` is a 25 × 10 µm `cap_nmos_06v0`. Earlier standalone fixtures with one/eight capacitors, three source resistances and two supply-ramp shapes completed all 24 cases. Thus, the simple capacitor alone did not reproduce the extracted-clamp failure in those conditions.

The installed foundry subcircuit uses:

```spice
C_moscap 1 2 c='cap_nmos_06v0_corner*c_length*c_width*(0.001107+0.00107*tanh(6.25*v(1,2)-4.1875))' dtemp=dtemp
```

Inspection with `listing e` showed ngspice expanding it into a reversed-voltage helper source, a 1 F helper capacitor, and a behavioral source multiplying the helper current by the physical capacitance expression. The named `ec_moscap` branch is generated by this expansion. We do not infer that this branch or the foundry equation is defective solely from its appearance in the error.

A subsequent bounded experiment scaled the **internal helper** from 1 F to 1 pF and inversely scaled the current gain, preserving the algebraic terminal law `i=C(v)·dv/dt`. It did not edit the PDK or replace the physical C(V) with a fixed capacitor.

Both original and scaled standalone traces completed. Comparing the union of their adaptive output times by linear interpolation gave maximum differences of 2.708 µV and 2.708 nA. The current difference exceeded our preselected 0.1 nA diagnostic screen, so we **did not run the scaled extracted clamp or adopt the change**. Interpolation near waveform corners may contribute; this result does not prove physical inequivalence, and charge equivalence has not been established. The supplemental archive records the exact decks, expanded listing and outputs.

## Questions

1. What diagnostic would distinguish behavioral-helper scaling/convergence issues from the reduced fixture's topology, loading or initialization?
2. Are `hsa`, `wnflag=1` and the use of `uic` appropriate here? If not, what controlled initialization comparison would you recommend?
3. Is a charge-form or rescaled helper implementation appropriate, and how should terminal current/charge equivalence and truncation behavior be verified?
4. Is there a specific simulator revision or existing issue we should compare against before doing further model work?

We have stopped broad solver/tolerance experiments and would welcome a focused next test. Any candidate solution will require current/charge comparison, timestep/tolerance refinement and full-corner regression before it is used for camera qualification.
