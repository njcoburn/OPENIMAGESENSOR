#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash scripts/run-tools.sh bash -c '
set -e
xschem -n -q -x --rcfile /foss/designs/xschem/xschemrc -o /foss/designs/simulations -N pixel_from_schematic.spice /foss/designs/xschem/pixel_3t.sch
ngspice -b simulations/pixel_from_schematic.spice
'
