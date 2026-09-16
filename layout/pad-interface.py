"""Single analog-pad interface and independently verifiable local protection cell."""
from pathlib import Path
import klayout.db as k
root=Path(__file__).resolve().parents[1];out=root/'build/pad-layout'
l=k.Layout();l.dbu=.001;top=l.create_cell('analog_secondary');u=lambda x:round(x/l.dbu)
for name,x,y in [('protect_res',0,12),('protect_lo',10,12),('protect_hi',20,12)]:
 s=k.Layout();s.read(str(out/(name+'.gds')));c=l.create_cell(name);c.copy_tree(s.top_cell());top.insert(k.CellInstArray(c.cell_index(),k.Trans(u(x),u(y))))
top.flatten(True)
for idx in l.layer_indexes():
 if l.get_info(idx).layer==0:top.shapes(idx).clear()
def box(layer,x0,y0,x1,y1):top.shapes(l.layer(*layer)).insert(k.Box(u(x0),u(y0),u(x1),u(y1)))
def wire(layer,p,q,w=.6):
 assert p[0]==q[0] or p[1]==q[1]
 box(layer,min(p[0],q[0])-w/2,min(p[1],q[1])-w/2,max(p[0],q[0])+w/2,max(p[1],q[1])+w/2)
def via(x,y):
 box((34,0),x-.28,y-.28,x+.28,y+.28);box((35,0),x-.13,y-.13,x+.13,y+.13);box((36,0),x-.3,y-.3,x+.3,y+.3)
def label(n,x,y):top.shapes(l.layer(36,10)).insert(k.Text(n,k.Trans(u(x),u(y))))
# Resistor ends are separated vertically, with substrate guard tied to ground.
via(0,12.83);via(0,11.17);wire((36,0),(-5,11.17),(0,11.17));label('PAD',-5,11.17)
wire((36,0),(0,12.83),(4,12.83));wire((36,0),(4,12.83),(4,12));wire((36,0),(4,12),(25,12));label('CORE',25,12)
for x,y in [(10,12),(20,12)]:via(x,y)
wire((36,0),(-5,2),(25,2),1);label('VSS',-5,2)
for x,y in [(0,10.21),(10,5.5),(20,4.69)]:via(x,y);wire((36,0),(x,2),(x,y))
via(20,18.5);wire((36,0),(20,18.5),(20,23));wire((36,0),(-5,23),(25,23),1);label('VDD',-5,23)
# Merge adjacent P+ implant regions around the poly resistor and substrate guard.
box((31,0),-3,9.5,3,14.5)
l.write(str(out/'secondary-functional.gds'))
# Standalone density-filled coupon; guard device/COMP clearances for dummy poly.
def reg(layer):return k.Region(top.begin_shapes_rec(l.layer(*layer)))
comp=reg((22,0));bounds=k.Box(u(-5.5),u(1.5),u(25.5),u(23.5))
for layer,size,pitch in [((30,0),1.4,2.4),((34,0),1.2,1.6),((36,0),1.2,1.6),((42,0),1.2,1.6),((46,0),1.2,1.6),((81,0),1.2,1.8)]:
 forbidden=reg(layer).sized(u(.4 if layer!=(30,0) else 1))
 if layer==(30,0):forbidden|=comp.sized(u(1))
 fill=k.Region()
 for x in range(bounds.left+u(.5),bounds.right-u(size),u(pitch)):
  for y in range(bounds.bottom+u(.5),bounds.top-u(size),u(pitch)):
   tile=k.Region(k.Box(x,y,x+u(size),y+u(size)))
   if (tile&forbidden).is_empty():fill|=tile
 top.shapes(l.layer(*layer)).insert(fill)
l.write(str(out/'analog_secondary.gds'))
# Visual/connection test wrapper. Full ring clamps, corners, supply bonding remain separate.
s=k.Layout();s.read('/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/gds/gf180mcu_fd_io.gds')
pad=l.create_cell('gf180mcu_fd_io__asig_5p0');pad.copy_tree(s.cell('gf180mcu_fd_io__asig_5p0'))
wrapper=l.create_cell('analog_pad_interface');wrapper.insert(k.CellInstArray(pad.cell_index(),k.Trans()))
wrapper.insert(k.CellInstArray(top.cell_index(),k.Trans(u(42.5),u(365))))
# Route primary pad signal to the local resistor using metal2.
for a,b in [((33.65,349.655),(33.65,376.17)),((33.65,376.17),(37.5,376.17))]:
 wrapper.shapes(l.layer(36,0)).insert(k.Box(u(min(a[0],b[0])-.4),u(min(a[1],b[1])-.4),u(max(a[0],b[0])+.4),u(max(a[1],b[1])+.4)))
# Tie core/IO supply stripes together only for this single-domain test coupon.
def wb(layer,p,q,w=.8):
 assert p[0]==q[0] or p[1]==q[1]
 wrapper.shapes(l.layer(*layer)).insert(k.Box(u(min(p[0],q[0])-w/2),u(min(p[1],q[1])-w/2),u(max(p[0],q[0])+w/2),u(max(p[1],q[1])+w/2)))
for sh in pad.shapes(l.layer(81,10)).each():
 if not sh.is_text():continue
 n=sh.text.string;pt=sh.text.trans.disp.to_dtype(l.dbu)
 if n in ['DVDD','VDD']:wb((81,0),(pt.x,pt.y),(85,pt.y))
 elif n in ['DVSS','VSS']:wb((81,0),(-10,pt.y),(pt.x,pt.y))
wb((81,0),(85,120.975),(85,388),2)
wb((81,0),(-10,78.305),(-10,367),2)
for n,y,x in [('VDD',388,85),('VSS',355,-10)]:
 if n=='VSS':
  wb((36,0),(37.5,367),(37.5,355),1)
  for layer in [36,42]:wb((layer,0),(37.5,355),(37.5,355),1)
  wb((38,0),(37.5,355),(37.5,355),.26)
  wb((42,0),(37.5,y),(x,y),1)
 else:wb((36,0),(37.5,y),(x,y),1)
 for layer in [36,42,46,81]:wb((layer,0),(x,y),(x,y),1)
 for layer in [38,40,41]:wb((layer,0),(x,y),(x,y),.26)
 wrapper.shapes(l.layer(36,10)).insert(k.Text(n,k.Trans(u(x),u(y))))
wrapper.shapes(l.layer(81,10)).insert(k.Text('PAD',k.Trans(u(37.595),u(33.1))))
wrapper.shapes(l.layer(36,10)).insert(k.Text('CORE',k.Trans(u(67.5),u(377))))
l.write(str(out/'analog_pad_interface.gds'))
