#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs/build/power-ring/flat-lvs
magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc /foss/designs/layout/export-power-ring-lvs.tcl > export.log 2>&1
cat > reference.spice <<'SPICE'
.include /foss/designs/build/power-ring/power_ring.spice
.subckt ring_flat AVDD_BOND AVSS_BOND AVDD AVSS
Rbondv AVDD_BOND AVDD 0
Rbondg AVSS_BOND AVSS 0
Xring AVDD AVSS power_ring
.ends ring_flat
SPICE
netgen -batch lvs 'ring_flat_lvs.spice ring_flat' 'reference.spice ring_flat' /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl lvs.log > netgen.log 2>&1
