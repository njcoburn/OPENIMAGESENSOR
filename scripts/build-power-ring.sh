#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
python3 layout/power-ring.py
cd build/power-ring
pdk=/foss/pdks/gf180mcuD
magic -dnull -noconsole -rcfile "$pdk/libs.tech/magic/gf180mcuD.magicrc" /foss/designs/layout/check-power-ring.tcl > magic.log 2>&1
magic -dnull -noconsole -rcfile "$pdk/libs.tech/magic/gf180mcuD.magicrc" /foss/designs/layout/extract-power-ring-devices.tcl > device-extraction.log 2>&1
mkdir -p flat-lvs
cp ring_flat.ext flat-lvs/ring_flat.ext
bash /foss/designs/scripts/check-power-ring-flat-lvs.sh
cd /foss/designs/build/power-ring
klayout -b -r "$pdk/libs.tech/klayout/tech/drc/gf180mcu.drc" -rd input=power_ring.gds -rd report=ring-early.lyrdb -rd topcell=power_ring -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup -rd threads=2 > klayout.log 2>&1
