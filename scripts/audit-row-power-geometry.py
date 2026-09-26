"""Audit additive power-grid geometry and unchanged photodiode clearance."""
from pathlib import Path
import argparse
import hashlib
import json
import klayout.db as k

p = argparse.ArgumentParser()
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
layouts = []
for path in [a.baseline, a.candidate]:
    ly = k.Layout()
    ly.read(str(path))
    layouts.append(ly)
old, new = layouts
assert old.dbu == new.dbu
assert old.cell('strip') is not None and new.cell('strip') is not None
layers = sorted(set((i.layer,i.datatype) for ly in layouts for i in ly.layer_infos()))
allowed = {(38,0),(42,0),(40,0),(46,0),(41,0),(81,0)}
# The source photodiode GDS explicitly marks its 20 x 20 um junction on 115/5.
apertures = k.Region(new.cell('strip').begin_shapes_rec(new.layer(115,5)))
assert abs(apertures.area()*new.dbu**2 - 64*400) < 1e-6
changes = []
for layer in layers:
    regions = [k.Region(ly.cell('strip').begin_shapes_rec(ly.layer(*layer))).merged()
               for ly in layouts]
    removed = regions[0]-regions[1]
    added = regions[1]-regions[0]
    assert removed.is_empty(), ('Removed geometry', layer)
    if added.is_empty():
        continue
    assert layer in allowed, ('Unexpected changed layer', layer)
    overlap = (added & apertures).area()*new.dbu**2
    assert overlap == 0, ('Added power geometry overlaps diode junction', layer)
    changes.append({'gds_layer':list(layer),'added_area_um2':added.area()*new.dbu**2,
                    'added_junction_overlap_um2':overlap})
assert {(42,0),(46,0),(81,0)} <= {tuple(x['gds_layer']) for x in changes}
report = {'baseline_sha256':hashlib.sha256(a.baseline.read_bytes()).hexdigest(),
          'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
          'junction_area_um2':apertures.area()*new.dbu**2,'changes':changes,
          'all_other_polygon_geometry_unchanged':True,
          'scope':'Drawn geometry check, not optical/package qualification; labels ignored.'}
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
