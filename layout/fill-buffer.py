"""Add floating density fill around the standalone PMOS buffer.
No vias are added to fill. Functional device and route geometry is unchanged.
"""
from pathlib import Path
import klayout.db as k
root=Path(__file__).resolve().parents[1]
ly=k.Layout();ly.read(str(root/'build/output_buffer.gds'));top=ly.cell('output_buffer');dbu=ly.dbu
assert abs(dbu-.001)<1e-12
u=lambda v:round(v/dbu)
def region(layer):return k.Region(top.begin_shapes_rec(ly.layer(*layer)))
# Standalone density region, including spare area around the routes.
# Remove generator-only bounding-box drawings, not process geometry.
for cell in ly.each_cell():cell.shapes(ly.layer(0,0)).clear()
bounds=k.Box(u(0),u(6),u(120),u(96))
optical=k.Region()
# Avoid contact, active, implant/well and functional poly for dummy poly.
comp=region((22,0));poly=region((30,0))
for layer,size,pitch in [((30,0),2,4),((34,0),1.2,1.5),((36,0),1.2,1.5),((42,0),1.2,1.5),((46,0),1.2,1.5),((81,0),1.2,1.8)]:
 existing=region(layer)
 forbidden=existing.sized(u(1 if layer==(30,0) else .4))|optical
 if layer==(30,0):forbidden|=comp.sized(u(1))
 fill=k.Region()
 for x in range(bounds.left+u(1),bounds.right-u(size),u(pitch)):
  for y in range(bounds.bottom+u(1),bounds.top-u(size),u(pitch)):
   tile=k.Box(x,y,x+u(size),y+u(size))
   if (k.Region(tile)&forbidden).is_empty():fill.insert(tile)
 top.shapes(ly.layer(*layer)).insert(fill)
 print(layer,'added',fill.area()*dbu*dbu,'um2')
ly.write(str(root/'build/output_buffer.gds'))
