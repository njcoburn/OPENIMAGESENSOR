#!/usr/bin/env bash
# Inside the pinned tools image, after readout layout verification.
set -euo pipefail
cd /foss/designs
mkdir -p build/readout-pex
(cd build/readout-pex
PEX_GDS=/foss/designs/checkpoints/readout/column_readout.gds magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-readout.tcl > extraction.log 2>&1)
python3 scripts/reduce-readout.py
netgen -batch lvs 'build/readout-pex/readout_devices.spice readout_devices' 'layout/column_readout.spice column_readout' /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl build/readout-pex/lvs.log > build/readout-pex/netgen.log 2>&1
python3 scripts/simulate-readout-pex.py
python3 scripts/build-overview.py
