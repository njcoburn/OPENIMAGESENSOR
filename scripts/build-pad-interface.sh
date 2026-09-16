#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
mkdir -p build/pad-layout
cd build/pad-layout
pdk=/foss/pdks/gf180mcuD
magic -dnull -noconsole -rcfile "$pdk/libs.tech/magic/gf180mcuD.magicrc" /foss/designs/layout/pad-primitives.tcl > primitives.log 2>&1
python3 /foss/designs/layout/pad-interface.py
for part in secondary interface; do
 magic -dnull -noconsole -rcfile "$pdk/libs.tech/magic/gf180mcuD.magicrc" "/foss/designs/layout/check-pad-$part.tcl" > "$part-magic.log" 2>&1
 if [ "$part" = secondary ]; then
  top=analog_secondary
  schematic=/foss/designs/circuits/analog-secondary.spice
 else
  top=analog_pad_interface
  schematic=/foss/designs/circuits/analog-pad-interface.spice
 fi
 netgen -batch lvs "${part}_extracted.spice $top" "$schematic $top" "$pdk/libs.tech/netgen/gf180mcuD_setup.tcl" "$part-lvs.log" > "$part-netgen.log" 2>&1
 klayout -b -r "$pdk/libs.tech/klayout/tech/drc/gf180mcu.drc" -rd input="$top.gds" -rd report="$part-klayout.lyrdb" -rd topcell="$top" -rd variant=gf180mcuD -rd threads=2 > "$part-klayout.log" 2>&1
done
klayout -b -r "$pdk/libs.tech/klayout/tech/drc/gf180mcu.drc" -rd input=analog_pad_interface.gds -rd report=stock-pad-klayout.lyrdb -rd topcell=gf180mcu_fd_io__asig_5p0 -rd variant=gf180mcuD -rd threads=2 > stock-pad-klayout.log 2>&1
magic -dnull -noconsole -rcfile "$pdk/libs.tech/magic/gf180mcuD.magicrc" /foss/designs/layout/extract-pad-secondary.tcl > secondary-pex.log 2>&1
python3 /foss/designs/scripts/reduce-pad-secondary.py
