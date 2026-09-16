#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
python3 layout/integrated.py
(cd build/integrated
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/check-integrated.tcl > magic.log 2>&1
netgen -batch lvs 'integrated_extracted.spice sensor_3x3' '/foss/designs/circuits/integrated.spice sensor_3x3' /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl lvs.log > netgen.log 2>&1)
klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=/foss/designs/build/integrated/sensor_3x3.gds -rd report=/foss/designs/build/integrated/klayout.lyrdb -rd topcell=sensor_3x3 -rd variant=gf180mcuD -rd threads=2 > build/integrated/klayout.log 2>&1
klayout -b -r scripts/report-integrated.py
