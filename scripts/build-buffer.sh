#!/usr/bin/env bash
# Inside pinned silicon tools container.
set -euo pipefail
cd /foss/designs
mkdir -p build/buffer-primitives build/buffer-layout-check
(cd build/buffer-primitives; magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/buffer-primitives.tcl > magic.log 2>&1)
python3 layout/output_buffer.py
cp build/output_buffer.gds build/output_buffer-functional.gds
python3 layout/fill-buffer.py
(cd build/buffer-layout-check
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/check-buffer.tcl > magic.log 2>&1
netgen -batch lvs 'buffer_extracted.spice output_buffer' '/foss/designs/circuits/output-buffer.spice output_buffer' /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl lvs.log > netgen.log 2>&1)
klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=/foss/designs/build/output_buffer.gds -rd report=/foss/designs/build/buffer-layout-check/klayout.lyrdb -rd topcell=output_buffer -rd variant=gf180mcuD -rd threads=2 > build/buffer-layout-check/klayout.log 2>&1
klayout -b -r scripts/report-buffer-layout.py
