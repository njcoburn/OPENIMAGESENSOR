#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
python3 scripts/prepare-power-ring-hier.py
mkdir -p build/power-ring/pex-hier
cd build/power-ring/pex-hier
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-power-ring-hier.tcl > extraction.log 2>&1
