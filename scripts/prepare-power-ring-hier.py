"""Flatten inside each macro; preserve macro hierarchy and identical physical geometry."""
from pathlib import Path
import klayout.db as k
root=Path('/foss/designs');out=root/'build/power-ring';l=k.Layout();l.read(str(out/'power_ring.gds'));top=l.cell('power_ring')
# Region equality checks establish that changing hierarchy did not change masks.
check_layers=[(21,0),(22,0),(30,0),(31,0),(32,0),(33,0),(34,0),(35,0),(36,0),(38,0),(40,0),(41,0),(42,0),(46,0),(81,0)]
before={z:k.Region(top.begin_shapes_rec(l.layer(*z))).merged() for z in check_layers}
for name in ['dvdd','dvss','cor','fill10']:l.cell('gf180mcu_fd_io__'+name).flatten(True)
for z,a in before.items():assert (a^k.Region(top.begin_shapes_rec(l.layer(*z))).merged()).is_empty(),z
options=k.SaveLayoutOptions();options.add_cell(top.cell_index());l.write(str(out/'power_ring_macroflat.gds'),options)
print('Macro-local flattening: all checked mask regions unchanged.')
