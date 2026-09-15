"""Write inspectable hierarchical Xschem views for the physical array."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
header=['v {xschem version=3.4.8RC file_version=1.2}','G {}','K {}','V {}','S {}','E {}']
class Sch:
 def __init__(self):self.lines=header.copy()
 def c(self,s,x,y,p,rot=0):self.lines.append(f'C {{{s}}} {x} {y} {rot} 0 {{{p}}}')
 def n(self,x,y,a,b):self.lines.append(f'N {x} {y} {a} {b} {{}}')
 def lab(self,x,y,label):self.c('devices/lab_pin.sym',x,y,f'name=l{len(self.lines)} sig_type=std_logic lab={label}')
 def port(self,x,y,label):self.c('devices/iopin.sym',x,y,f'name=p{len(self.lines)} lab={label}')
 def save(self,name): (root/'xschem'/name).write_text('\n'.join(self.lines)+'\n')
p=Sch()
for x,y,name,d,g,s in [(220,-360,'Xrst','VRESET','RST','sense'),(500,-260,'Xsf','VDD','sense','sf'),(500,-100,'Xsel','sf','ROW','COL')]:
 p.c('symbols/nfet_03v3.sym',x,y,f'name={name[1:]} W=1u L=0.5u nf=1 m=1 ad=0.44p as=0.44p pd=2.88u ps=2.88u nrd=0 nrs=0 sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X')
 for xx,yy,net in [(x+20,y-30,d),(x-20,y,g),(x+20,y+30,s),(x+20,y,'GND')]:p.lab(xx,yy,net)
p.n(240,-330,240,-260);p.n(240,-260,480,-260)
p.n(520,-230,520,-130)
p.c('symbols/diode_nd2ps_03v3.sym',240,-150,'name=Dphoto model=diode_nd2ps_03v3 r_w=5u r_l=5u m=1',2)
p.n(240,-260,240,-180);p.lab(240,-120,'GND')
for i,name in enumerate(['VDD','VRESET','GND','RST','ROW','COL']):p.port(80+i*110,50,name)
p.lines.append('T {Physical GF180 pixel: 3 NMOS + 5 x 5 um N+/substrate diode} 60 -470 0 0 0.4 0.4 {}')
p.lines.append('T {No optical current source or ideal capacitor in the physical cell.\nAll NMOS: W=1 um, L=0.5 um; junction geometry from the primitive.} 80 130 0 0 0.3 0.3 {}')
p.save('pixel_physical.sch')
symbol=['v {xschem version=3.4.8RC file_version=1.2}','G {}','K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=X1"}','V {}','S {}','E {}','B 4 -60 -60 60 60 {}','T {@name} -50 -85 0 0 0.25 0.25 {}','T {3T pixel} -25 -10 0 0 0.25 0.25 {}']
for i,(name,x,y) in enumerate([('VDD',-60,-40),('VRESET',-60,-20),('GND',-60,0),('RST',-60,20),('ROW',-60,40),('COL',60,0)]):
 symbol.append(f'B 5 {x-2.5} {y-2.5} {x+2.5} {y+2.5} {{name={name} dir=inout}}')
 symbol.append(f'T {{{name}}} {x+5 if x<0 else x-30} {y-8} 0 0 0.15 0.15 {{}}')
(root/'xschem/pixel_physical.sym').write_text('\n'.join(symbol)+'\n')
a=Sch()
for row in range(3):
 for col in range(3):
  x=300+340*col;y=100+240*row
  a.c('pixel_physical.sym',x,y,f'name=X{row}{col}')
  for net,dy in [('VDD',-40),('VRESET',-20),('GND',0),(f'RST{row}',20),(f'ROW{row}',40)]:a.lab(x-60,y+dy,net)
  a.n(x+60,y,x+120,y)
for col in range(3):
 x=420+340*col
 a.n(x,100,x,340);a.n(x,340,x,580);a.n(x,580,x,700);a.lab(x,700,f'COL{col}')
ports=['VDD','VRESET','GND','RST0','RST1','RST2','ROW0','ROW1','ROW2','COL0','COL1','COL2']
for i,name in enumerate(ports):a.port(140+(i%6)*170,800+(i//6)*70,name)
a.lines.append('T {3 x 3 GF180 monochrome array - physical schematic} 120 -90 0 0 0.5 0.5 {}')
a.lines.append('T {Shared labels connect supplies, reset and row-select nets.\nEach column is wired vertically; select only one row at a time.} 120 -30 0 0 0.3 0.3 {}')
a.save('array_3x3.sch')
