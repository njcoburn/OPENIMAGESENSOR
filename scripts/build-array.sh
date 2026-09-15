#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash scripts/check-layout-probe.sh
bash scripts/run-tools.sh bash -c '
set -e
mkdir -p build/array-primitives build/array-check
cd build/array-primitives
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/diode-probe.tcl > diode.log 2>&1
grep -q "DIODE_DRC_COUNT=0" diode.log
cd /foss/designs
python3 layout/array_3x3.py
python3 layout/add_fill.py
cd build/array-check
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/check-array.tcl > magic.log 2>&1
netgen -batch lvs "array_extracted.spice array_3x3" "/foss/designs/layout/array_3x3.spice array_3x3" /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl lvs.log > netgen.log 2>&1
grep ARRAY_DRC magic.log
 tail -4 lvs.log
'
