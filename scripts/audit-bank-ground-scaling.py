"""Check a 2–64 column ground-bus revision against the exact intended M4 rectangle."""
import argparse
import hashlib
import json
from pathlib import Path
import klayout.db as k

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--original',type=Path,required=True)
p.add_argument('--revised',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
(a.out/'runner.py').write_bytes(Path(__file__).read_bytes())
layouts=[];metadata=[]
for directory in [a.original,a.revised]:
    layout=k.Layout();layout.read(str(directory/'bank.gds'));layouts.append(layout)
    metadata.append(json.loads((directory/'verification.json').read_text()))
assert layouts[0].dbu==layouts[1].dbu
columns=metadata[0]['columns']
assert columns==metadata[1]['columns'] and 2<=columns<=64
assert metadata[0]['column_pitch_um']==metadata[1]['column_pitch_um']==40
assert metadata[0]['bus_y_um']==metadata[1]['bus_y_um']
assert metadata[0]['bus_y_um']['GND']==-10
assert metadata[0].get('ground_bus_width_um',2)==2 and metadata[1]['ground_bus_width_um']==8
assert (a.original/'reference.spice').read_bytes()==(a.revised/'reference.spice').read_bytes()
assert set(map(str,layouts[0].layer_infos()))==set(map(str,layouts[1].layer_infos()))
def bus(width):
    return k.Region(k.Box(*[round(v/layouts[0].dbu) for v in [-50-width/2,-10-width/2,40*(columns-1)+38+width/2,-10+width/2]]))
changes=[]
for info in layouts[0].layer_infos():
    regions=[];texts=[]
    for layout in layouts:
        cell=layout.top_cell();layer=layout.layer(info)
        regions.append(k.Region(cell.begin_shapes_rec(layer)))
        texts.append(sorted(str(shape.text) for shape in cell.shapes(layer).each() if shape.is_text()))
    assert texts[0]==texts[1], f'Changed labels on {info}'
    difference=regions[0]^regions[1]
    if not difference.is_empty():
        assert (info.layer,info.datatype)==(46,0), f'Unexpected changed layer {info}'
        assert (difference^(bus(2)^bus(8))).is_empty(), 'M4 difference extends beyond the intended ground bus'
        changes.append(str(info))
assert changes==['46/0']
files=[directory/name for directory in [a.original,a.revised] for name in ['bank.gds','verification.json','reference.spice']]+[a.out/'runner.py']
result=dict(scope=__doc__,columns=columns,original=str(a.original),revised=str(a.revised),only_ground_bus_rectangle_changed=True,
            changed_layers=changes,reference_identical=True,
            old_bbox_um=metadata[0]['bbox_um'],new_bbox_um=metadata[1]['bbox_um'],
            evidence_hashes={str(f.resolve().relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
(a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
