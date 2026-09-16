#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
mkdir -p build/power-ring/pex-unsimplified
cp build/power-ring/pex/ring_flat.ext build/power-ring/pex-unsimplified/
cd build/power-ring/pex-unsimplified
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-power-ring-unsimplified.tcl > extraction.log 2>&1
