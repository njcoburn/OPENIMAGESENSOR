#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash scripts/run-tools.sh bash -c '
set -e
mkdir -p build/layout-probe-verified
cd build/layout-probe-verified
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/primitive-probe.tcl > magic.log 2>&1
grep -q "PROBE_DRC_COUNT=0" magic.log
netgen -batch lvs "nfet_probe.spice nfet_probe" "/foss/designs/layout/nfet_probe.spice nfet_probe" /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl lvs.log > netgen.log 2>&1
grep -q "Circuits match uniquely" lvs.log
printf "Primitive probe: Magic DRC zero errors; Netgen LVS unique match.\n"
'
