"""Render the exact checkpoint GDS in KLayout; use klayout -b -r this_file.py.

Only display settings change. The compressed design is authenticated before use.
"""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import pya

ROOT=Path(__file__).resolve().parents[1]
package=ROOT/'checkpoints/compact-bank-64-matrix'
meta=json.loads((package/'verification.json').read_text())
assets=ROOT/'docs/assets'
with tempfile.TemporaryDirectory() as tmp:
    gds=Path(tmp)/'bank.gds';digest=hashlib.sha256()
    with gzip.open(package/'bank.gds.gz','rb') as source,gds.open('wb') as target:
        while chunk:=source.read(1024*1024):target.write(chunk);digest.update(chunk)
    assert digest.hexdigest()==meta['gds_sha256']
    view=pya.LayoutView();view.load_layout(str(gds),0)
    layout=view.active_cellview().layout();top=layout.top_cell()
    assert top.name=='compact_bank'
    bbox=top.bbox().to_dtype(layout.dbu)
    assert abs(bbox.width()-2667.87)<1e-6 and abs(bbox.height()-1069.8)<1e-6
    view.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp')
    view.add_missing_layers();view.max_hier()
    view.set_config('text-visible','false');view.set_config('grid-visible','false')
    view.set_config('background-color','#0b1725')
    views=[('current-bank-layout.png',[-150,-150,2620,990],2200,906),
           ('current-bank-layout-detail.png',[-108,-125,164,175],1200,1324)]
    for name,bounds,width,height in views:
        view.zoom_box(pya.DBox(*bounds));view.save_image(str(assets/name),width,height)
    report=dict(scope=__doc__,source='checkpoints/compact-bank-64-matrix/bank.gds.gz',
                gds_sha256=digest.hexdigest(),top_cell=top.name,bbox_um=[bbox.left,bbox.bottom,bbox.right,bbox.top],
                width_um=bbox.width(),height_um=bbox.height(),columns=meta['columns'],
                pixel_rows_implemented=1,full_chip_assembled=False,
                views=[dict(image='docs/assets/'+name,view_box_um=bounds,pixels=[width,height]) for name,bounds,width,height in views])
    (ROOT/'simulations/current-bank-layout-view.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
