#!/usr/bin/env bash
# Run inside the pinned tools container: bash scripts/run-tools.sh bash scripts/run-parasitics.sh
set -euo pipefail
cd /foss/designs
for variant in rc-probe rc-filled; do
  input=array-functional.gds
  if [[ $variant == rc-filled ]]; then input=array_3x3.gds; fi
  mkdir -p "build/parasitics/$variant"
  (
    cd "build/parasitics/$variant"
    export PEX_GDS="/foss/designs/build/size-study/20um/build/$input"
    magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-rc-probe.tcl > extraction.log 2>&1
    test -s array_rc.spice
  )
done
python3 scripts/reduce-parasitics.py
for variant in rc-probe rc-filled; do
  netgen -batch lvs "build/parasitics/$variant/array_devices.spice array_devices" \
    'build/size-study/20um/build/array_schematic.spice array_3x3' \
    /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl \
    "build/parasitics/$variant/lvs.log" > "build/parasitics/$variant/netgen.log" 2>&1
  grep -q 'Circuits match uniquely' "build/parasitics/$variant/lvs.log"
done
python3 scripts/simulate-parasitics.py
python3 scripts/check-parasitic-timestep.py
python3 scripts/build-overview.py
