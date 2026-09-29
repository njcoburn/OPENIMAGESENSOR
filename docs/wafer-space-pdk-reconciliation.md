# wafer.space PDK source reconciliation — 27 September 2026

The provider-pinned source was compared without changing the running PDK.
The repeated scoped DRC check finishes cleanly with **zero violations**;
the report database and log are independently checked. The result is in the
[reconciliation report](../simulations/wafer-space-pdk-reconciliation-20260927.json)
and [overview](overview.html#wafer-space-run3). This is a block-level main
DRC pass, not the provider's complete-chip submission check.

The provider's [precheck Makefile](https://github.com/wafer-space/gf180mcu-precheck/blob/main/Makefile)
selects open_pdks `d658698bd8bcf4e05fc7b5991a701247ba0d744c` and GF180MCUD.
Its [build configuration](https://github.com/fossi-foundation/open-pdks/blob/d658698bd8bcf4e05fc7b5991a701247ba0d744c/gf180mcu/Makefile.in)
selects five metal layers, 1.1 µm top metal and MIM between the top two metals.
The [node template](https://github.com/fossi-foundation/open-pdks/blob/d658698bd8bcf4e05fc7b5991a701247ba0d744c/gf180mcu/gf180mcu.json)
declares 2 fF/µm² MIM. Together these identify the M4/M5 option used by our bank.
This establishes alignment with the published PDK configuration, not optical
packaging approval or a completed provider submission check.

The installed open_pdks commit is `b344c97eacc2aaf8e14ae7e43e2e9dc0871de2c0`.
The histories diverge, so a merge-base comparison alone is insufficient. Exact
recursive Git trees show only five changed paths: README, VERSION, the GF180
node/dependency template and two SKY130 files. The GF180 build/extraction
sources are unchanged. Downloaded configuration files are checked against
their Git blob IDs.

The primitive dependency changes from `a0c31bd71c2084a5283204dc4e80f1f901d2d5d0`
to `b6866b82e2bd560a29f3576c19106ff7b8b41b10`. Its
[complete comparison](https://github.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/compare/a0c31bd71c2084a5283204dc4e80f1f901d2d5d0...b6866b82e2bd560a29f3576c19106ff7b8b41b10)
contains only a KLayout GUI checkbox fix. Primitive device-model sources do
not change. This source comparison does not prove every built PDK byte or
runtime tool binary is identical.

The verification dependency changes from `13f5cb3829f7ec3fe1d4469534fd60c12aaaa477`
to `e766ad1974edf7712ebd4729e40037f24d9232cb`. Its
[comparison](https://github.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pv/compare/13f5cb3829f7ec3fe1d4469534fd60c12aaaa477...e766ad1974edf7712ebd4729e40037f24d9232cb)
contains 47 changed files, including rule code and unit-test fixtures. The
pinned verification archive is extracted separately under `build/`; all
changed files are checked against their Git blob IDs before reporting.

## Scoped physical check

The unchanged `build/compact-bank-c64-ground-grid-20260927/bank.gds` is checked
with the pinned verification source and installed KLayout executable. The GDS
has a single top cell, `compact_bank`. Main DRC excludes density, antenna and
cup, matching the block's existing check scope. One worker and one thread
avoid the documented older-KLayout parallel-worker issue.

After downloading/extracting the exact verification revision, reproduce into
a fresh output directory:

```sh
mkdir build/provider-drc-new
bash scripts/run-tools.sh klayout -b \
  -r build/gf180-provider-verification-20260927/klayout/drc/gf180mcu.drc \
  -rd input=/foss/designs/build/compact-bank-c64-ground-grid-20260927/bank.gds \
  -rd topcell=compact_bank -rd report=/foss/designs/build/provider-drc-new/main.lyrdb \
  -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup \
  -rd workers=1 -rd threads=1
python3 scripts/report-provider-pdk.py
python3 scripts/report-wafer-space-plan.py
python3 scripts/update-overview-sections.py
```

The report generator audits the retained `build/compact-bank-c64-provider-drc-v2-20260927`
result. It reads the report database rather than treating KLayout's zero exit
status as proof of zero violations. The upstream deck returns zero even when
it finds errors.

## Remaining release work

Run the exact-chip provider precheck with the selected release tool versions.
Close density, antenna, fill/extraction, origin/grid/slot, die identifiers,
pad and optical-access requirements, LVS/ERC and optical packaging. Source
alignment and a block-level main DRC pass do not establish tapeout readiness.
All current simulations keep their original pinned environment and evidence.

The first attempt completed its rules with zero reported violations but raised
a relative-path error during KLayout cleanup. Its log/database are preserved;
the accepted repeat finished cleanly in 518.278 seconds using absolute
input/output paths. Both attempts and the source archive are retained.
