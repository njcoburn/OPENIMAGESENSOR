#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
python3 layout/power-ring.py
mkdir -p build/power-ring/leads
cd build/power-ring/leads
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-power-leads.tcl > extraction.log 2>&1
