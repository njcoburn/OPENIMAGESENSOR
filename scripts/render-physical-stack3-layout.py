"""Render the separately verified physical candidate GDS without modifying it."""
import hashlib
import json
from pathlib import Path
import pya
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'build/compact-bank-c2-stack3-v3-20260930'
meta=json.loads((source/'verification.json').read_text())
assert hashlib.sha256((source/'bank.gds').read_bytes()).hexdigest()==meta['gds_sha256']
view=pya.LayoutView();view.load_layout(str(source/'bank.gds'),0)
view.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp')
view.add_missing_layers();view.max_hier();view.set_config('text-visible','false');view.set_config('grid-visible','false');view.set_config('background-color','#0b1725')
view.zoom_box(pya.DBox(-73,-125,86,180))
view.save_image(str(ROOT/'docs/assets/compact-bank-physical-stack3-detail-20260930.png'),795,1525)
