#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
python3 scripts/check-routed-demonstrator.py --gds build/filled-demonstrator/demonstrator_filled.gds --report build/filled-demonstrator/connectivity.json
cd build/filled-demonstrator
pdk=/foss/pdks/gf180mcuD
klayout -b -r "$pdk/libs.tech/klayout/tech/drc/gf180mcu.drc" -rd input=demonstrator_filled.gds -rd report=density-antenna.lyrdb -rd topcell=demonstrator_routed -rd variant=gf180mcuD -rd decks=density,antenna -rd threads=2 > density-antenna.log 2>&1
klayout -b -r "$pdk/libs.tech/klayout/tech/drc/gf180mcu.drc" -rd input=demonstrator_filled.gds -rd report=main-drc.lyrdb -rd topcell=demonstrator_routed -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup -rd threads=2 > main-drc.log 2>&1
magic -dnull -noconsole -rcfile "$pdk/libs.tech/magic/gf180mcuD.magicrc" extract-flat.tcl > extraction-flat.log 2>&1
netgen -batch lvs 'routed_extracted.spice routed_flat' '/foss/designs/circuits/demonstrator-routed.spice demonstrator_routed' "$pdk/libs.tech/netgen/gf180mcuD_setup.tcl" lvs.log > netgen.log 2>&1
