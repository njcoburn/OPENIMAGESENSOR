#!/usr/bin/env bash
# Run in the pinned tools image; verified buffer GDS is in the checkpoint.
set -euo pipefail
cd /foss/designs
mkdir -p build/buffer-pex
(cd build/buffer-pex
PEX_GDS=/foss/designs/checkpoints/output-buffer/output_buffer.gds magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/extract-buffer.tcl > extraction.log 2>&1)
python3 scripts/reduce-buffer.py
netgen -batch lvs 'build/buffer-pex/buffer_devices.spice buffer_devices' 'circuits/output-buffer.spice output_buffer' /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl build/buffer-pex/lvs.log > build/buffer-pex/netgen.log 2>&1
python3 scripts/simulate-buffer-pex.py
python3 scripts/check-buffer-pex.py
python3 scripts/report-buffer-pex.py
python3 scripts/build-overview.py
