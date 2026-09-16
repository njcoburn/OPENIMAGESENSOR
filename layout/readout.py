"""Seven-transistor column bias + NMOS mux block; independent of pixel array."""
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
c=gf.Component('column_readout');nf=gf.import_gds(root/'build/layout-probe-verified/nfet_probe.gds');bias=gf.import_gds(root/'build/readout-primitives/bias_nfet.gds')
rails={n:20+3*i for i,n in enumerate(['GND','BIAS','COL0','COL1','COL2','OUT','SEL0','SEL1','SEL2'])}
for n,y in rails.items():
 wire(c,M2,(0,y),(145,y));c.add_label(n,position=(0,y),layer=(36,10))
def terminal(x,y,track,net):
 via(c,x,y);wire(c,M2,(x,y),(track,y));via(c,track,y,True);wire(c,M3,(track,y),(track,rails[net]));via(c,track,rails[net],True)
for i in range(7):
 x=10+20*i;is_bias=i<4;ref=c.add_ref(bias if is_bias else nf);ref.dmove((x,10))
 nets=('BIAS','BIAS','GND') if i==0 else ((f'COL{i-1}','BIAS','GND') if is_bias else ('OUT',f'SEL{i-4}',f'COL{i-4}'))
 dx=1.26 if is_bias else .51;gy=1.28 if is_bias else .94;by=-2.04 if is_bias else -1.54
 terminal(x+dx,10,x+3,nets[0]);terminal(x,10+gy,x,nets[1]);terminal(x-dx,10,x-3,nets[2]);terminal(x,10+by,x+6,'GND')
c.write_gds(root/'build/column_readout.gds')
