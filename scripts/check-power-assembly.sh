#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
python3 layout/power-ring.py
cd build/power-ring
klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=ring_sensor_power.gds -rd report=assembly-final-main.lyrdb -rd topcell=ring_sensor_power -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup -rd threads=2 > assembly-final-klayout.log 2>&1
