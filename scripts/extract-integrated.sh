#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
mkdir -p build/integrated-pex
(cd build/integrated-pex
PEX_GDS=/foss/designs/checkpoints/integrated/sensor_3x3.gds magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-integrated.tcl > extraction.log 2>&1)
python3 scripts/reduce-integrated.py
(cd build/integrated-pex
netgen -batch lvs 'sensor_devices.spice sensor_devices' '/foss/designs/circuits/integrated.spice sensor_3x3' /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl lvs.log > netgen.log 2>&1)
