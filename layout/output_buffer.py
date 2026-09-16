"""Three-PMOS output buffer, matching circuits/output-buffer.spice."""
from pathlib import Path
import gdsfactory as gf
root=Path(__file__).resolve().parents[1];gf.gpdk.PDK.activate();gf.kcl.dbu=.001
M1=(34,0);M2=(36,0);M3=(42,0)
def rect(c,l,x0,y0,x1,y1):c.add_polygon([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],layer=l)
def wire(c,l,p,q,w=.4):
 assert p[0]==q[0] or p[1]==q[1]
 rect(c,l,min(p[0],q[0])-w/2,min(p[1],q[1])-w/2,max(p[0],q[0])+w/2,max(p[1],q[1])+w/2)
def via(c,x,y,upper=False):
 lo,cut,hi=(M2,(38,0),M3) if upper else (M1,(35,0),M2)
 size=.6 if upper else .48
 for l in [lo,hi]:rect(c,l,x-size/2,y-size/2,x+size/2,y+size/2)
 rect(c,cut,x-.13,y-.13,x+.13,y+.13)
c=gf.Component('output_buffer')
mirror=gf.import_gds(root/'build/buffer-primitives/mirror_pfet.gds')
follower=gf.import_gds(root/'build/buffer-primitives/buffer_pfet.gds')
rails={n:40+3*i for i,n in enumerate(['GND','VDD','PREF','IN','BUF'])}
for n,y in rails.items():
 wire(c,M2,(0,y),(120,y));c.add_label(n,position=(0,y),layer=(36,10))
def terminal(x,y,track,net):
 via(c,x,y);wire(c,M2,(x,y),(track,y));via(c,track,y,True);wire(c,M3,(track,y),(track,rails[net]));via(c,track,rails[net],True)
for i,nets in enumerate([('PREF','PREF','VDD'),('BUF','PREF','VDD'),('GND','IN','BUF')]):
 x=20+40*i;ref=c.add_ref(mirror if i<2 else follower);ref.dmove((x,20));dx=1.26 if i<2 else .51
 terminal(x+dx,20,x+4,nets[0]);terminal(x,30.40,x,nets[1]);terminal(x-dx,20,x-4,nets[2]);terminal(x,8.96,x+6,'VDD')
c.write_gds(root/'build/output_buffer.gds')
