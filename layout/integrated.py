"""Integrate saved functional blocks; units micrometres. No optical over-routing."""
from pathlib import Path
import json,hashlib
import klayout.db as k
root=Path(__file__).resolve().parents[1];dest=root/'build/integrated';dest.mkdir(exist_ok=True)
ly=k.Layout();ly.dbu=.001;top=ly.create_cell('sensor_3x3');u=lambda v:round(v/ly.dbu)
sources={}
for filename,name,x,y in [('array-functional.gds','array_3x3',0,100),('readout-functional.gds','column_readout',0,0),('buffer-functional.gds','output_buffer',160,0)]:
 p=root/'checkpoints/integrated'/filename;src=k.Layout();src.read(str(p));cell=ly.create_cell('placed_'+name);cell.copy_tree(src.cell(name));top.insert(k.CellInstArray(cell.cell_index(),k.Trans(u(x),u(y))));sources[filename]=hashlib.sha256(p.read_bytes()).hexdigest()
top.flatten(True)
for li in ly.layer_indexes():
 for s in list(top.shapes(li).each()):
  if s.is_text():s.delete()
top.shapes(ly.layer(0,0)).clear()
M2=(36,0);M3=(42,0);M4=(46,0)
def box(layer,x0,y0,x1,y1):top.shapes(ly.layer(*layer)).insert(k.Box(u(x0),u(y0),u(x1),u(y1)))
def wire(layer,p,q,w=.8):
 assert p[0]==q[0] or p[1]==q[1]
 box(layer,min(p[0],q[0])-w/2,min(p[1],q[1])-w/2,max(p[0],q[0])+w/2,max(p[1],q[1])+w/2)
def via(x,y,upper=False):
 lo,cut,hi=(M3,(40,0),M4) if upper else (M2,(38,0),M3)
 for l in (lo,hi):box(l,x-.4,y-.4,x+.4,y+.4)
 box(cut,x-.13,y-.13,x+.13,y+.13)
ports={}
def label(n,x,y,layer):
 top.shapes(ly.layer(layer[0],10)).insert(k.Text(n,k.Trans(u(x),u(y))));ports[n]=[x,y,layer[0]]
for i in range(3):
 x=75+80*i;y=70+4*i;rx=-16-4*i
 wire(M3,(x,100),(x,y));via(x,y,True)
 wire(M4,(rx,y),(x,y));via(rx,y,True)
 wire(M3,(rx,26+3*i),(rx,y));via(rx,26+3*i)
 wire(M2,(rx,26+3*i),(0,26+3*i));label(f'COL{i}',x,100,M3)
# Mux output to buffer input, routed above both blocks.
wire(M2,(145,35),(150,35));via(150,35);wire(M3,(150,35),(150,64));via(150,64,True)
wire(M4,(150,64),(160,64));via(160,64,True);wire(M3,(160,49),(160,64));via(160,49);label('OUT',150,64,M4)
# Separate shared supply and ground buses, with trunks into all relevant blocks.
for net,y,ax,bx,by in [('GND',84,-10,290,40),('VDD',88,-4,294,43)]:
 wire(M4,(-36,y),(bx,y),2)
 wire(M3,(ax,100),(ax,y),1);via(ax,y,True)
 wire(M2,(280,by),(bx,by),1);via(bx,by);wire(M3,(bx,by),(bx,y),1);via(bx,y,True)
 label(net,-36,y,M4)
wire(M2,(-32,20),(0,20),1);via(-32,20);wire(M3,(-32,20),(-32,84),1);via(-32,84,True)
label('VRESET',-7,100,M3)
for r in range(3):
 for n,dy in [('RST',29),('ROW',32)]:label(f'{n}{r}',0,100+50*r+dy,M2)
for n,y in [('BIAS',23),('SEL0',38),('SEL1',41),('SEL2',44)]:label(n,0,y,M2)
for n,y in [('PREF',46),('BUF',52)]:label(n,280,y,M2)
ly.write(str(dest/'sensor-functional.gds'))
# Keep light windows clear of fill on every filled conductor layer.
optical=k.Region()
for row in range(3):
 for col in range(3):optical.insert(k.Box(u(60+80*col-13),u(105+50*row-13),u(60+80*col+13),u(105+50*row+13)))
def region(layer):return k.Region(top.begin_shapes_rec(ly.layer(*layer)))
assert (region(M4)&optical).is_empty(), 'Inter-block routes must avoid optical keepouts'
comp=region((22,0));bounds=k.Box(u(-38),u(5),u(298),u(248))
for layer,size,pitch in [((30,0),2,4),((34,0),1.2,1.5),((36,0),1.2,1.5),((42,0),1.2,1.5),((46,0),1.2,1.5),((81,0),1.2,1.8)]:
 forbidden=region(layer).sized(u(1 if layer==(30,0) else .4))|optical
 if layer==(30,0):forbidden|=comp.sized(u(1))
 fill=k.Region()
 for x in range(bounds.left+u(1),bounds.right-u(size),u(pitch)):
  for y in range(bounds.bottom+u(1),bounds.top-u(size),u(pitch)):
   tile=k.Box(x,y,x+u(size),y+u(size))
   if (k.Region(tile)&forbidden).is_empty():fill.insert(tile)
 top.shapes(ly.layer(*layer)).insert(fill)
ly.write(str(dest/'sensor_3x3.gds'))
(dest/'placement.json').write_text(json.dumps({'source_sha256':sources,'ports':ports,'array_translation_um':[0,100],'readout_translation_um':[0,0],'buffer_translation_um':[160,0],'fill_bounds_um':[-38,5,298,248]},indent=2)+'\n')
