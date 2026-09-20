#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
python3 scripts/prepare-routed-verification.py
python3 scripts/check-routed-demonstrator.py
cd build/routed-demonstrator
pdk=/foss/pdks/gf180mcuD
klayout -b -r "$pdk/libs.tech/klayout/tech/drc/gf180mcu.drc" -rd input=demonstrator_routed.gds -rd report=main-drc.lyrdb -rd topcell=demonstrator_routed -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup -rd threads=2 > klayout.log 2>&1
magic -dnull -noconsole -rcfile "$pdk/libs.tech/magic/gf180mcuD.magicrc" verify.tcl > magic.log 2>&1
netgen -batch lvs 'routed_extracted.spice routed_flat' '/foss/designs/circuits/demonstrator-routed.spice demonstrator_routed' "$pdk/libs.tech/netgen/gf180mcuD_setup.tcl" lvs.log > netgen.log 2>&1
