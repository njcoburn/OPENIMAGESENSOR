#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash scripts/build-array.sh
bash scripts/run-tools.sh bash -c '
set -e
xschem -n -q -x --tcl "set top_is_subckt 1" --rcfile /foss/designs/xschem/xschemrc -o /foss/designs/build -N array_schematic.spice /foss/designs/xschem/array_3x3.sch
netgen -batch lvs "build/array-check/array_extracted.spice array_3x3" "build/array_schematic.spice array_3x3" /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl build/array-check/xschem_lvs.log > build/array-check/xschem_netgen.log 2>&1
klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=/foss/designs/build/array_3x3.gds -rd report=/foss/designs/build/array-check/klayout-final.lyrdb -rd topcell=array_3x3 -rd variant=gf180mcuD -rd threads=2 > build/array-check/klayout.log 2>&1
python3 scripts/check-array.py
python3 scripts/simulate-array.py
klayout -b -r scripts/render-array.py
'
