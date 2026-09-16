#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
mkdir -p build/power-ring/pex-metal
cp build/power-ring/pex/ring_flat.ext build/power-ring/pex-metal/
cd build/power-ring/pex-metal
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-power-ring-metal.tcl > extraction.log 2>&1
