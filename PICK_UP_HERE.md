# Pick up here — 64×64 wafer.space first silicon

Updated 2026-09-29. **User confirmed GF180 with wafer.space and first silicon
over frame rate.** Read [COMPLETION_PLAN.md](COMPLETION_PLAN.md), then
[NEXT_STEPS.md](NEXT_STEPS.md). Do not resume the old 3×3-first release sequence.

The requested 29 September checkpoint includes the [labeled device layout](docs/overview.html#current-device-layout)
and a [portable exact-GDS package](checkpoints/compact-bank-64-matrix/README.md).
It preserves the completed matrix and source scripts; large raw simulation traces
remain local under `build/`. No new simulation batch was started for this checkpoint.

## Reviewed 2026-09-29 — alternating/inverse matrix complete and passing

Both new cases pass all five independent checks. The 27 °C inverse case has
387.179 µV worst total error and 17.529 µV tracking; 125 °C alternating has
430.383 µV total error and 81.527 µV tracking, against 500 µV. Saved-sample
refinement is 0.134/0.150 µV and physical-event refinement is 0.135/0.099 µV,
against 10 µV. All four new transients complete 128 reads each and both 100 ns
cases have all 192 matched references (384 total).

The four simulation containers and watcher exited with code 0, with no simulation,
audit or rendering failures. The batch plus audits took about **4.1 hours**.
The desktop alert was delivered and dismissed. There are no active jobs from
this batch, and no further simulations were launched during the review.

Reviewed both new plots and rehashed **1,707 distinct evidence files** from the
two new manifests (909 entries each), without missing files or mismatches. The
10 launch source hashes verify; the earlier reviewed reports are unchanged.
See [review evidence](simulations/compact-bank-cross-review-20260929.json) and
[the full matrix](docs/overview.html#compact-bank-64-cross).

With the earlier pair, the alternating/inverse patterns now pass at **both 27 °C
and 125 °C**: eight complete 100/50 ns transients and 768 audited references.
Worst total error across the matrix remains 438.213 µV (61.8 µV margin to 500 µV),
with 0.150 µV maximum saved-sample refinement. This does not qualify uniform
illumination, other operating corners or the complete chip.

**Next:** extend the independently checked reporting path to uniform dark/middle/
bright patterns, then test 0/80/240 pA per pixel at both temperatures, with the same
reference and 100/50 ns checks. The current full-bank auditor only accepts
alternating/inverse; do not relabel uniform cases to bypass its assertions.
Preserve its hash-pinned version and verify a new auditor before long runs.
The six uniform cases would require 12 transients and 1,152 references if each
receives the same coarse/fine treatment; launch in bounded batches.

After uniform coverage, finish operating-corner, parasitic-placement and local
supply/reference checks, then exercise 4×64 repeated rows with real drivers and
full-column loading. Full-bank/corner and full-chip qualification flags remain
false. Keep the completed raw runs and prior failing controls unchanged.

## Historical launch 2026-09-28 — crossed cases were running

At the user's request, the **27 °C inverse** and **125 °C alternating** batch is
running: four fresh 100/50 ns transients plus 384 new matched references. No new
pass is claimed. The completed nominal alternating/hot inverse evidence below
is preserved. The v3 runner and v2 auditor are unchanged.

**First action on return:** inspect
`build/compact-bank-cross-watch-20260928/status.json`, then check
`docker ps -a --filter name=ois-bank-cross` and the container logs. Exact commands
and inherited/source hashes are in `build/compact-bank-cross-plan-20260928.json`.
Do not relaunch these directories:

| Case | Directory under `build/` |
|---|---|
| 27 °C inverse, 100 ns + 192 references | `compact-bank-c64-cross-inverse27-100-20260928` |
| 27 °C inverse, 50 ns refinement | `compact-bank-c64-cross-inverse27-50-20260928` |
| 125 °C alternating, 100 ns + 192 references | `compact-bank-c64-cross-alternating125-100-20260928` |
| 125 °C alternating, 50 ns refinement | `compact-bank-c64-cross-alternating125-50-20260928` |

The watcher is `ois-bank-cross-watcher-20260928`. It runs the existing independent
auditor before publishing `simulations/compact-bank-64-inverse27.json` and
`simulations/compact-bank-64-alternating125.json`, retaining measured failures.
The new [matrix overview](docs/overview.html#compact-bank-64-cross) preserves the
earlier two results and marks the new ones pending until audited.

Six new preflight/regression checks pass. All 1,711 prior evidence files and
the new plan source hashes verify. All four jobs have produced saved transient
records; no startup failure is reported. The dated launch observation is
`simulations/compact-bank-cross-20260928.json`. All four new decks differ from their
same-temperature/timestep controls only in 64 reversed illumination-source values.
No tolerances, timing, physical models or saved probes change. The job bounds
remain four hours per transient, 30 minutes per reference, four reference workers
and a seven-hour watcher that does not stop simulations on expiry.

The desktop alert is re-enabled for this batch; PID and heartbeat are in
`build/compact-bank-cross-notification-20260928.json`. Leave Windows awake/signed
in and Docker running. The prior notification is a completed historical record.
See [reproduction](docs/compact-bank-64-cross.md). After completion, check both
reports, all 128 reads/192 references per case, refinement/plots and evidence
hashes. Then extend uniform illumination and remaining corner/placement checks
before repeated rows and real drivers. Full bank/corner and full-chip qualification
remain open. The sections below describe earlier completed and stopped batches.

## Completed and reviewed 2026-09-28 — both selected full-bank cases pass

Both complete-bank cases pass their selected checks: 27 °C alternating and
125 °C inverse illumination, with 100/50 ns comparisons. All four transients
finish 128 reads each; both 100 ns cases have 192 independently audited references
(384 total). Worst total errors are 372.606/438.213 µV and output tracking is
17.486/57.086 µV, against 500 µV. Saved-sample refinement is 0.133/0.129 µV
and physical-event refinement is 0.135/0.099 µV, against 10 µV.

The four simulation containers and completion watcher all exited with code 0.
No simulation, audit or rendering failure was reported. The desktop notification
was delivered and dismissed. This supersedes the running-state notes below.
The resumed batch and its audits finished about 3.1 hours after launch.

Reviewed both output plots and verified **all 1,711 distinct evidence files**
across the nominal/hot manifests (913/909 entries), with no missing files or hash
mismatches. Reports and plots are linked from
[the complete-bank overview](docs/overview.html#compact-bank-64-full) and
[reproduction](docs/compact-bank-64-full.md). The per-run monitor's generic
"independent audit pending" wording is stale: the final watcher's `audited`
map and both reports confirm completion. Preserve these files; do not rerun or
modify these completed directories.

**Immediate next batch:** the two missing crossed cases, **27 °C inverse** and
**125 °C alternating**, each with 100/50 ns runs and 192 references at 100 ns.
Use the same ground-grid layout, 12 µs acquisition, 20 µs slots, KLU, current-form
drivers and strict settings. Use fresh directories and independent audits. No
new batch was launched during this review.

Then add uniform dark/middle/bright illumination at both temperatures, remaining
parasitic-placement and process/wire/supply checks, and local supply/reference
drop measurements. The hot case has only 61.8 µV remaining margin to the total
error limit, so selected-case success does not qualify those untested corners.
After bank coverage closes, exercise 4×64 repeated rows with real decoders/drivers
and full-column loading, then assemble and qualify the full 4096-pixel chip.
Pin/protocol and pad planning can proceed alongside the bank extension.
Full bank/corner and full-chip qualification flags remain false.

## Historical launch 2026-09-28 — jobs were running


Docker Desktop and the existing VNC desktop are restored. The **v3 runner**
adds timing-aware 10/12 µs transient reuse and separately audited completed
reference reuse. The original runners, stopped attempts and prior manifests
are unchanged. The new [resume control](simulations/compact-bank-resume-control.json)
independently checks all 32 samples and 48 references of the passing 16-column
control: every retained sampled/reference voltage and reported error is identical.
Sixteen resume/deck tests, eight independent auditor tests and the four original
v2 timing tests pass. Two watcher regressions also verify that a rendering failure
does not skip the remaining pair and a measured accuracy failure stays a completed
audit. Compilation and whitespace checks pass.

Four detached jobs plus a new configured completion watcher are running:

| Case | Fresh directory under `build/` | Work |
|---|---|---|
| Nominal 100 ns | `compact-bank-c64-resume-nominal100-20260928` | Audited copy of complete nominal trace; 64 capture references reused; 128 output references being solved |
| Nominal 50 ns | `compact-bank-c64-resume-nominal50-20260928` | Fresh full transient |
| Hot inverse 100 ns | `compact-bank-c64-resume-hot-inverse100-20260928` | Fresh full transient plus 192 references |
| Hot inverse 50 ns | `compact-bank-c64-resume-hot-inverse50-20260928` | Fresh full transient |

**Completion notification:** at the user's request, a separate Windows process
watches the audit status and displays a persistent desktop popup when both audits
finish, or when the watcher fails/expires or stops updating. It does not send a
new Codex chat message. Leave Windows awake and signed in. Its PID and heartbeat
are in `build/compact-bank-notification-20260928.json`; source is
`scripts/notify-bank-completion.ps1` and `scripts/start-bank-notification.py`.
Four outcome checks pass without displaying test popups. The monitor exits after
its alert is dismissed, or alerts after eight hours without a final result.

**First action on return:** read
`build/compact-bank-resume-watch-20260928/status.json`, then inspect
`docker ps -a` and the named containers' logs. The plan and exact commands are in
`build/compact-bank-resume-plan-20260928.json`. Containers are named
`ois-bank-{nominal100,nominal50,hot-inverse100,hot-inverse50}-20260928`;
the watcher is `ois-bank-watcher-20260928`. Do not relaunch these directories.
Watch status is a dated observation; compare it with container state.

The new watcher calls `report-bank-full-v2.py` separately for each complete
100/50 ns pair, retaining measured failures as completed audits. It writes
`simulations/compact-bank-64-full.json` and `compact-bank-64-full-hot.json`, then
refreshes the overview when the nominal report exists. **Neither selected-screen
pass nor complete-bank accuracy has yet been established.** Once both reports
exist, review their checks, all 128 reads/192 references per case, plots and
hashes before extending coverage. The original fixed-path watcher remains stopped. The new watcher was restarted
once to apply that rendering fix; its initial status is retained in
`build/compact-bank-resume-watch-20260928-before-render-fix`. Simulation jobs
were not interrupted.

Transient watchdogs are now 14,400 s; each reference has 1,800 s and four workers.
These are runtime allowances, not measured completion estimates. No tolerances,
physical devices, parasitics or timing were relaxed. The watcher has a seven-hour
deadline and does not stop simulators if it expires. Remaining live runs must be
checked directly if the watcher ends without both audits.

The [resume snapshot](simulations/compact-bank-resume-snapshot-20260928.json)
records 268 hashes before copying, including all 64 finished capture references,
and verifies the earlier plan's existing hashes. Its new hashes establish the
28 September reuse baseline; they do not retrospectively authenticate unrecorded
27 September bytes. Missing/interrupted references are newly simulated; partial
transients are never used as restart checkpoints. See
[reproduction and scope](docs/compact-bank-64-full.md).

## Historical stop at user request — 2026-09-27

**All four simulation containers and their completion watcher were stopped and
verified absent from `docker ps` on 27 September.** Only the VNC desktop remains
running. This supersedes the earlier note about leaving the jobs running.
No complete-bank accuracy audit was produced.

| Retained attempt | Sample instants reached | Last saved time | References |
|---|---:|---:|---:|
| Nominal 100 ns | 128/128; transient complete | 3.980000 ms | 64/192 complete |
| Nominal 50 ns | 124/128; incomplete | 3.892011 ms | Not requested |
| Hot inverse 100 ns | 120/128; incomplete | 3.805005 ms | Not started |
| Hot inverse 50 ns | 114/128; incomplete | 3.686010 ms | Not requested |

Exact stop record: `build/compact-bank-full-stopped-progress-20260927.json`.
The older watcher `status.json` is a **stale pre-stop snapshot**, not evidence
that anything is still running. The original run directories, binary traces,
completed references and interrupted-reference files are preserved. Stopping
was requested by the user, not a demonstrated numerical or accuracy failure.

**First action tomorrow:** inspect the stop record and retained execution files.
Do not overwrite these attempts or blindly restart the old watcher. The nominal
100 ns transient is complete and may be reusable after a timing-aware audit;
12 µs reuse is currently rejected by `simulate-compact-bank-v2.py`, so implement
and verify an explicit reuse path before attempting it. The three incomplete
traces are diagnostic evidence, not simulator restart checkpoints. Plan any
necessary reruns in fresh directories. Finish the nominal references and both
full timestep/temperature pairs before claiming a selected-screen pass.

After completion, independently check all 128 reads and 192 references per
100 ns case, inspect refinement/plots, verify old/new evidence hashes and update
the project handoffs. A completed audit can report an accuracy failure; do not
equate execution completion with a pass. Full bank/corner and full-chip
qualification remain open. Preserve the versioned runner and earlier immutable
evidence. `scripts/finish-bank-full.py` has fixed old paths and needs a deliberate
new setup before use with any replacement runs.

Completed during this continuation: provider-pinned main DRC **zero violations**
on the unchanged ground-grid bank, independently checked database/log; declared
PDK options and relevant source alignment established (not binary equivalence
or full provider precheck). See
[PDK reconciliation](docs/wafer-space-pdk-reconciliation.md). Updated bank-fit
arithmetic leaves **3.126 mm²** unreserved in the default full-slot core;
complete-chip fit remains unverified. Both findings are in the overview.
The old 5,346 manifest entries and the new 193 PDK/4 fit hashes verified.
Four timing/deck tests, six auditor tests, Python compilation and whitespace
checks passed. Docker/VNC remains open; browser error dialogs were cleared.

## Original geometry constraint

Full-slot default core: 3048 × 4238 µm. Existing array: 5120 × 3200 µm;
selected bank: 5198 × 945.04 µm. Both exceed even the inside-seal dimensions
in either orientation. The new [floorplan budget](docs/64x64-slot-fit.md)
uses a candidate 40 µm pixel pitch and repacked bank. It is not qualified GDS.
The compact pixel, isolated capture column, physically joined single tile
and compact shared two-column bank are implemented and screened.
The compact 1×64 bank now has scoped physical and selected electrical results
below; complete-bank qualification remains next.

## Attempt: complete 64-column scans — stopped, 2026-09-27

The versioned timing runner passed four deck/schedule regression checks.
The nominal `full100`/`full50` and 125 °C `hot-inverse100`/`hot-inverse50`
attempts were stopped as recorded above. They requested 384 references across
the two 100 ns runs; only 64 nominal capture references finished.
All four use 12 µs acquisition, KLU, strict
settings and physical MIM saves. See [the new overview section](docs/overview.html#compact-bank-64-full)
and [reproduction](docs/compact-bank-64-full.md). These attempts are stopped and incomplete;
the earlier completed-simulation statements below are historical.

## Earlier: 16-column extension and 64-column ground-return diagnosis — 2026-09-27

The [16-column extension](docs/overview.html#compact-bank-16-extension) passes
its selected checks across **46 transients and 1,152 references**. Worst total
error is 433.171 µV and tracking is 301.667 µV
(500 µV limits). All five patterns at 27/125 °C have 100/50 ns comparisons;
the largest saved-terminal difference is 0.450 µV. All 19 individual
shunts plus their joint placement pass for the hot inverse pattern, with
0.105/0.137 µV maximum HOLD/STORE changes (10 µV limit). The separate
inverse-pattern layout–schematic response reaches 10.062 mV and has
no assigned acceptance threshold.

The 8 µm bus alone does not solve 64-column scaling: a matched column-62
readout fails at 1,994.440 µV total error. A new physical distributed ground
return **fails with 10 µs acquisition** at 547.178 µV total error and
340.253 µV tracking. Both main DRC checks and both LVS paths pass, and
a geometry audit restricts the change to ground metal/vias. The new bank is
2667.87 × 1069.80 µm, within the 2700 × 1100 µm budget. See the
[selected readout comparison](docs/overview.html#compact-bank-64-read-probes)
and [capture/ground diagnosis](docs/compact-bank-64-ground8.md).

Extending acquisition from 10 to 12 µs on that same grid **passes the selected
diagnostic** at 269.281 µV total error and 62.529 µV tracking. Only the
ACQ falling edges and sample times move; selection/reset and the 20 µs slot
budget stay unchanged. Three new matched references and an unchanged-prefix
comparison are audited. The separately versioned full-bank runner now supports
this timing; complete nominal and hot inverse-pattern scans are running with
100/50 ns refinement and 384 planned references.

These are bounded development screens. Full 16-column corner/placement
coverage, the full 64-column schedule and its 192 references, real drivers,
repeated rows and exact 64×64 manufacturing qualification remain open.

Next: Finish and independently audit the running 12 µs complete-bank scans: all 128 reads and 192 references per selected temperature/pattern, plus 100/50 ns refinement. The versioned runner and four timing/deck regression tests are complete. Then extend the remaining pattern/corner coverage.

All launched simulations in this continuation have finished. Docker/VNC remain
running; KLayout opens the distributed-return GDS. New changes and raw evidence
are local and uncommitted. No purchase, submission or external message was made.
Use fresh experiment directories and preserve all failing controls and prior
manifests. The original 2,453 evidence hashes remain intact. Seven new audit regressions and three acquisition-deck tests pass; the selected-read reference generator matches 96 archived
decks byte for byte. Provider PDK options/revision comparison is recorded in
`simulations/wafer-space-pdk-review-20260927.json`; exact equivalence and optical
packaging approval remain unresolved.

## Earlier: 16-column thermal/pattern continuation — 2026-09-27

The selected expanded screen passes all six checks across 14 transients and
576 references (13 transients and 528 references are new). Five patterns at
27/125 °C give 432.966 µV worst total capture/readout error and 301.658 µV
output tracking. Alternating-pattern 100→50 ns comparisons are 0.220/0.449 µV.
Joint far-shunt comparisons stay below 0.122 µV HOLD and 0.156 µV STORE.
Contrast/brightness ordering passes. Mixed-versus-uniform output response is
88.972 µV maximum and remains a separate metric without an assigned threshold.

See [the overview](docs/overview.html#compact-bank-16-screen),
[reproduction](docs/compact-bank-16-screen.md) and
[the audited report](simulations/compact-bank-16-screen.json). All saved samples
and DC references are re-read; 2,453 evidence hashes are recorded. A bounded
pattern batch and exact-regression-tested faster trace sampling support the
continuation. Two sampling tests and fourteen reuse/schedule/progress tests pass.

The layout is unchanged: `build/compact-bank-c16-ground8-20260927`. All new
simulations have finished. Docker/VNC remain running; changes and raw evidence
are local. No purchase, submission or external message was made. Next finish
individual-net placements, other-pattern refinement, physical/schematic and
corner checks before promoting the correction to 64 columns. The joint far test
is not a substitute for individual placement checks. No full 16-column or
64×64 tapeout qualification is claimed.

## Earlier 16-column continuation — 2026-09-27

Audited transient reuse is implemented and regression-checked against the hot
two-column control: all saved values and six independently recomputed references
match exactly. Eight reuse tests plus six schedule/progress tests pass.
The original 16-column trace now has all 48 references, exposing a nominal
capture/readout failure: 540.016 µV against the 500 µV limit. Its output tracking
passes at 54.198 µV. The fresh 100 ns rerun confirms the failure at 540.185 µV;
matching saved sample voltages differ by at most 0.185 µV. Three extended
reference controls change saved voltages by at most 0.000136241 µV.

Physical MIM probes localize most of the row-off storage shift to ground motion:
column 14 STORE/ground/across-plate shifts are −788.750/−752.243/−36.507 µV.
A physical 8 µm M4 ground-bus candidate passes both main DRC checks and both
LVS paths with unchanged 162 MOS, 128 MIM and 16 diodes. A direct GDS XOR audit
confirms that only the ground-bus rectangle changes; all labels and other
geometry match. It adds 1.8 µm to the 16-column width (709.56 × 978.28 µm).
The revised 100 ns nominal run completes 3 ms and all 48 references, passing
at 189.413 µV total capture/readout error and 55.267 µV output tracking.
The later selected thermal/pattern/refinement/placement controls are recorded
above; their stated remaining gates supersede this checkpoint's next steps. Docker/VNC
remain running; all simulations from this continuation have finished.

See [the current results](docs/overview.html#compact-bank-16) and
[reproduction](docs/compact-bank-16.md). The original model and failing trace
remain intact. Do not regenerate the prior solver manifest: its hash is part
of the reuse provenance. New evidence remains local under `build/`.

The 64-column layout is unchanged. Qualify the revised 16-column bank before
applying routing changes at full-bank scale; real addressing, repeated rows
and the assembled 64×64 tapeout gates remain open.

## Earlier continuation — 2026-09-27: KLU and Run 3 review

The [overview HTML](docs/overview.html#compact-bank-solver) now includes all new
solver controls, numerical comparisons, physical checks and the dated
[Run 3 cost/die-fit review](docs/overview.html#wafer-space-run3). It is open in
the VNC Firefox browser; Docker and VNC stay running. No simulation remains
running. Changes are local and uncommitted; no order, submission or external
message was made.

Use `--solver klu`, original current-form drivers and trapezoidal integration.
KLU completes the compact 64-column reset control through 250 µs in 66 s.
The hot two-column reference control passes and differs from SPARSE by only
0.009070 µV at saved terminals. The eight-column nominal/hot alternating cases
pass 24 references each, at 195.412/430.243 µV worst capture/readout error.
Matched 200→100 ns saved-terminal differences are 0.170/0.401 µV.
Gear passes nominal accuracy/comparison but offers no runtime improvement here.
The equivalent voltage-form driver experiment fails initialization; do not
promote it. Thirteen local reducer/schedule/progress tests pass.

`build/compact-bank-c16-v1-20260927` passes both main DRC and both LVS paths
(162 MOS, 128 MIM, 16 diodes). Its 300 s attempt ends at the second-scan start;
`build/compact-bank-c16-complete-klu-20260927` completes 3 ms/both scans in
440 s, without accuracy references. The 64-column 900 s run reaches
1.686001 ms/64,103 samples and 14/128 scheduled sample instants. Initialization
is resolved for this fixture; full-bank completion and accuracy remain open.
The audited reuse and 48 references are now complete; the newer 16-column
continuation above supersedes this earlier next step. Budget a complete
64-column run from its retained phase timings after the electrical correction.

Run 3 advertises clean GDS by 16 December 2026 (23:59 AoE), delivery Q2 2027.
The full slot is $7,000 early / $8,000 standard for 1,000 dies; CoB adds $1,500
but optical compatibility is unconfirmed. Early bird ends 30 September;
purchase deadline is 9 December. The 19 September provider update reports few
full slots left. Planning uses the full 3.048 × 4.238 mm core; smaller slots
cannot fit the 2.56 mm-square array. Final assembly must add only 63 rows to
the joined bank's existing row. No full 64×64 layout or tapeout pass exists.

## Resumed work — 2026-09-27

Docker Desktop was launched through Windows PowerShell; the existing
`openimagesensor-vnc` container is running with this checkout mounted. KLayout
opens `build/compact-bank-c64-v1-20260926/bank.gds`, and the VNC web endpoint
responds at `http://localhost:8080/vnc.html?autoconnect=true&resize=scale`.

[Initialization diagnosis](docs/compact-bank-initialization.md): the reducer
now supports compact `tile` models and preserves diode records/terminals.
The compact runner audits `--equivalent-bank-model` before simulation. Seven
reducer tests and four schedule tests pass. The hot two-column reduction control
completes, with 0.058281 µV maximum saved-sample difference from the passing
unreduced control. No tolerances, real devices or capacitor records changed.

Four- and eight-column controls pass both main DRC and LVS paths. Four columns
complete capture and both scans without transient OP fallback. Original/reduced
eight-column models recover via fallback and time out during readout at
1.475725/1.486010 ms. The audited 64-column reduction removes
1824 internal resistor-only nodes but still times out at 180 s with zero samples.
Next isolate initialization/reset/capture/readout runtime on these smaller
controls before scaling to 16 columns; full-bank electrical accuracy remains
open. See the report for final bounded-run outcomes and preserved hashes.

These changes are local and uncommitted. Earlier checkpoint/push statements
below describe the previous session. Generated evidence remains local in `build/`.
No simulation remains running; Docker and VNC stay available.

## Previous 64-column checkpoint — 2026-09-26

**Follow-up (2026-09-26):** the [compact 1×64 physical bank](docs/compact-bank-64.md)
is built in `build/compact-bank-c64-v1-20260926`. It fits the bank envelope
at 2627.76 × 978.28 µm and passes both main DRC checks and direct/RC-collapsed
LVS (642 MOS, 512 MIM, 64 diodes). The runner supports 64 columns with separate
first/late scans; four schedule tests and an exactly matching hot two-column
regression pass. Full-bank electrical qualification remains open. Use this
compact geometry for further diagnosis; retain the older stalled bank as evidence.

Both new 180 s nominal alternating-pattern attempts remain incomplete:
`rc-port` times out in initialization with zero samples (gmin/source stepping
fail; transient OP starts), while the schematic initializes and reaches
1.785052 ms/76,919 samples before timeout. Localize the new extracted network
with smaller banks or audited reduction before another full-bank attempt.

Git checkpoint `5d9de32` was pushed. About 32 GB of generated checkpoint
archives remain local and ignored; reports/manifests/source are tracked.
See [archive storage](checkpoints/README.md). Docker Desktop was launched
successfully again; container calls require access to the Docker socket.

## Resumed work — 2026-09-26

**Latest: [compact shared two-column bank](docs/compact-bank.md).**
`build/compact-bank-c2-v1-20260926` has two physically joined pixels/columns,
one physical reference pair and shared supply/reference/capture/output wiring.
Both main DRC and LVS paths pass (22 MOS, 16 MIM, two diodes, 293 resistors).
The matrix in `build/compact-bank-c2-matrix-v1-20260926` passes 100 transients
and 240 independent references across nominal/hot, five illumination patterns,
two timesteps and seven selected shunt placements. Worst total capture/readout
error is 419.033 µV, physical refinement 0.431 µV, and sampled placement
sensitivity 0.038 µV. Layout–schematic integrated response differs by up to
5.821 mV; changing one pixel changes its neighbor's output by up to 26.670 µV.
These are separate model/shared-response measurements, not capture-error passes.
One simultaneous capture and two reads per column are tested; repeated frames
and full-bank loading remain open. Evidence: `checkpoints/compact-bank`.

Next: compact 1×64 with actual shared wiring, supply/reference sizing and all
64 matched output/refinement/placement checks. The two-column control does not
validate 64-column supply drops. Keep the old stalled full bank diagnostic.

Docker Desktop/WSL is restored. If the CLI reports running with no engine,
launch `C:\Program Files\Docker\Docker\Docker Desktop.exe` directly. The CLI
restart waited for active Ubuntu processes and was cancelled; do not terminate
the working Ubuntu distro to satisfy that wait. No Docker settings were changed.

**Earlier: [physically joined tile](docs/compact-tile.md).**
`build/compact-tile-v1-20260926` joins the pixel/column through extracted COL,
VDD and GND routes. Both main DRC and LVS paths pass (10 MOS, eight MIM, one
diode, 133 resistors); the geometric aperture remains clear. The matrix in
`build/compact-tile-matrix-v1-20260926` passes 54 transients and 72 references:
419.404 µV worst total capture/readout error, 0.325 µV physical timestep
difference, 0.018 µV maximum sampled shunt-placement difference. Both nominal
and hot conditions read a captured value after pixel deselection/reset.
The layout–schematic integrated response differs by up to 3.922 mV; this is
separate from the same-physical-circuit 500 µV accuracy screen. Six selected
placements of BIAS/COL0/RST0/VRESET shunts are tested; raw negative corrections
remain diagnostic. One capture/two reads does not establish repeated frames.

The shared two-column follow-up above now passes; compact 1×64 routing, loading
and numerical screens remain next. Do not restart the old stalled full bank.

**Latest: [compact capture column](docs/compact-capture.md).**
`build/compact-capture-v4-20260926` fits 40 µm pitch (36.6 × 861.48 µm),
passes Magic/KLayout main DRC, both LVS paths and a two-column spacing control.
The selected seven-transistor/eight-MIM column passes 60 nominal/hot transients
and 36 DC references: 165.716 µV tracking, 395.222 µV layout–schematic shift,
0.262 µV refinement and 0.024 µV independent shunt-placement sensitivity.
Storage is 40.034/40.069 pF nominal/hot. VDD/ground/output trunks are
0.8/2/0.6 µm; all transistor primitives are unchanged. COL and BIAS shunts
use audited signed-total approximations; raw negative corrections remain
diagnostic. The 2 fF MIM option is still conditional. No shared bank is implied.

The joined follow-up above qualifies the next small development step. Reassess
the routing balance and shunt placements again when building a shared bank.

Docker and pinned ngspice 46 work. `build/compact-pixel-v1-20260926` contains
a 40 µm-pitch pixel and 2×2 control using the unchanged 20 µm junction and
transistor primitives. Both main DRC and direct/RC-collapsed LVS paths pass.
The [reset follow-up](docs/compact-reset.md) now passes 12 nominal/hot transients
and six extended-reference sets. Isolated port/gate shunt models conserve
5.77598 fF total reset capacitance; worst tracking is 24.204 µV, refinement
2.573 µV and placement sensitivity 0.035 µV. The unchanged 2×2 control still
passes (191.066/234.550 µV tracking). The raw isolated model reproduces its
220.01 µs reset abort and remains diagnostic; distributed capacitance is
approximated, not qualified. Evidence: `build/compact-reset-v1-20260926` and
`checkpoints/compact-reset`. Six 100 ns traces were reused for independent
200→1000 µs reference checks; worst reference shift is below 0.000002 µV.

Raw/reduced bank `.op` and 0.25 ms reset attempts all time out at 180 s without
samples. The reduction has not resolved initialization. The small coupled
shared two-column control now initializes and passes its development screen. Scale from that geometry; run-specific MIM/aperture gates remain.
[Report/reproduction](docs/compact-pixel.md) · [Evidence](checkpoints/compact-pixel/README.md).

## Verified evidence retained

- Extracted power-grid row plus schematic periphery: all 64 outputs at 27/125 °C
  pass 500 µV tracking and 10 µV timestep limits. `docs/grid-readout.md`.
- Isolated physical column: all 48 transients and both main DRC/LVS paths pass.
  `build/capture-column-routed-v8-20260925`; `docs/capture-column-qualification.md`.
- Reinforced physical bank: main DRC/both LVS pass; 16 DC controls complete;
  worst static physical–ideal buffer shift is 1.320 mV over 1.2–2.0 V.
  `build/capture-bank-c64-v5-20260925`; `docs/bank-reinforcement.md`.
- Coupled bank still unqualified: last 180 s attempt never completed initialization.
  Row-bank joins remain ideal; no full 64×64, startup or manufacturing pass.

## Work done during the 2026-09-25 replan

Archived the previous planning files without dropping evidence. Checked current
provider dimensions and schedule. Added reproducible slot-fit arithmetic and SVG.
Added standard-library resistor-only star-mesh reduction and five analytical/
corruption tests, plus an audited optional model input to the coupled runner.
The port model loses 4239 resistor-only nodes; device/capacitor/port records are
unchanged. Algebraic audits pass; the subsequent bounded runtime attempts above
all fail to initialize, so transient equivalence remains untested.
See [solver preparation](docs/bank-solver-preparation.md).

**Environment:** Docker access restored and EDA tools exercised on 2026-09-26.
No simulation remains running. Source, reports and manifests have been committed
and pushed; generated archives remain local. No release GDS, carrier, purchase
or external message changed.

Provider Run 3 dates are recorded in the plan; no run/slot reservation is assumed.
Optical access, analog pad allocation, MIM option and exact run requirements
remain open. Preserve all existing uncommitted work.

[Prior full handoff](checkpoints/planning-history-20260925/PICK_UP_HERE.md)
