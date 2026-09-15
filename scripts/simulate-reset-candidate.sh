#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash scripts/run-tools.sh bash -c '
set -e
xschem -n -q -x --rcfile /foss/designs/xschem/xschemrc -o /foss/designs/simulations -N reset_candidate.spice /foss/designs/xschem/pixel_reset_candidate.sch
ngspice -b simulations/reset_candidate.spice
'
