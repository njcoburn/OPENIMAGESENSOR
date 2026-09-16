#!/usr/bin/env bash
# Run in pinned tools container.
set -euo pipefail
cd /foss/designs
mkdir -p build/readout-primitives build/readout-check
(cd build/readout-primitives; magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/readout-primitives.tcl > magic.log 2>&1)
python3 layout/readout.py
cp build/column_readout.gds build/column_readout-functional.gds
python3 layout/fill-readout.py
(cd build/readout-check; magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/check-readout.tcl > magic.log 2>&1
netgen -batch lvs 'readout_extracted.spice column_readout' '/foss/designs/layout/column_readout.spice column_readout' /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl lvs.log > netgen.log 2>&1)
klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=/foss/designs/build/column_readout.gds -rd report=/foss/designs/build/readout-check/klayout.lyrdb -rd topcell=column_readout -rd variant=gf180mcuD -rd threads=2 > build/readout-check/klayout.log 2>&1

klayout -b -r scripts/report-readout.py
