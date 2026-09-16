#!/usr/bin/env bash
set -euo pipefail
cd /foss/designs
mkdir -p build/pad-closure
python3 - <<'PY'
from pathlib import Path
for p in ['wafer-space-precheck.py','wafer-space-template.yaml']:
 assert 'all,-antenna,-density,-cup' in (Path('checkpoints/pad-closure/references')/p).read_text()
PY
for group in wafer-space density antenna; do
 case "$group" in
  wafer-space) decks=all,-antenna,-density,-cup ;;
  *) decks=$group ;;
 esac
 klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc \
  -rd input=checkpoints/pad-layout/analog_pad_interface.gds \
  -rd report="build/pad-closure/interface-$group.lyrdb" \
  -rd topcell=analog_pad_interface -rd variant=gf180mcuD -rd decks="$decks" -rd threads=2 \
  > "build/pad-closure/interface-$group.log" 2>&1
done
python3 - <<'PY'
import xml.etree.ElementTree as E
for group in ['wafer-space','density','antenna']:
 n=len(E.parse('build/pad-closure/interface-'+group+'.lyrdb').findall('.//items/item'))
 print(group,n)
 assert n==0
PY
