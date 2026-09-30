"""Render pixel (row 0, column 0) from the exact bank checkpoint.

Run with: bash scripts/run-tools.sh klayout -b -r scripts/render-current-pixel-layout.py
Then run scripts/annotate-current-pixel-layout.py with the tools-container Python.
The original checkpoint and its rendered bank views remain unchanged.
"""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

import pya

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'checkpoints/compact-bank-64-matrix'
ASSETS = ROOT / 'docs/assets'
meta = json.loads((PACKAGE / 'verification.json').read_text())
bounds = [-2, -122, 42, -78]
with tempfile.TemporaryDirectory() as temporary:
    path = Path(temporary) / 'bank.gds'
    sha = hashlib.sha256()
    with gzip.open(PACKAGE / 'bank.gds.gz', 'rb') as source, path.open('wb') as target:
        while chunk := source.read(1024 * 1024):
            sha.update(chunk)
            target.write(chunk)
    assert sha.hexdigest() == meta['gds_sha256']
    view = pya.LayoutView()
    view.load_layout(str(path), 0)
    assert view.active_cellview().layout().top_cell().name == 'compact_bank'
    view.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp')
    view.add_missing_layers()
    view.max_hier()
    view.set_config('text-visible', 'false')
    view.set_config('grid-visible', 'false')
    view.set_config('background-color', '#0b1725')
    view.zoom_box(pya.DBox(*bounds))
    view.save_image(str(ASSETS / 'current-pixel-layout.png'), 1400, 1400)

report = dict(source='checkpoints/compact-bank-64-matrix/bank.gds.gz',
              gds_sha256=sha.hexdigest(), row=0, column=0, view_box_um=bounds,
              pixel_translation_um=[0, -120], pitch_um=40,
              transistor_centers_um={'reset': [6, -92], 'source_follower': [14, -92],
                                      'row_select': [22, -92]},
              diode_junction_um=[4, -117, 24, -97],
              clear_aperture_um=[5, -116, 23, -98],
              annotation_source='scripts/build-compact-pixel.py',
              scope='Actual GDS crop with explanatory labels; no geometry or qualification changes.',
              images=['docs/assets/current-pixel-layout.png', 'docs/assets/current-pixel-layout-labeled.png'])
(ROOT / 'simulations/current-pixel-layout-view.json').write_text(json.dumps(report, indent=2) + '\n')
print('Rendered pixel (0, 0) from verified bank GDS.')
