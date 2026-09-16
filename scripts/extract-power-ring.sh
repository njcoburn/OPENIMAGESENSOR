#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
mkdir -p build/power-ring/pex
cd build/power-ring/pex
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-power-ring.tcl > extraction.log 2>&1
