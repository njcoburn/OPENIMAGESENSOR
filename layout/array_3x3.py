"""GF180 verification array. PDK primitive GDS + explicit gdsfactory wiring.
Original prototype: ../test.py (preserved). Units are micrometres.
"""
from pathlib import Path
import json
import sys
import gdsfactory as gf
ROOT=Path(__file__).resolve().parents[1]
gf.gpdk.PDK.activate()
gf.kcl.dbu=.001
M1=(34,0);V1=(35,0);M2=(36,0);V2=(38,0);M3=(42,0)

def rect(c,layer,x0,y0,x1,y1):
 assert x1>x0 and y1>y0
 c.add_polygon([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],layer=layer)
def wire(c,layer,p,q,w=.4):
 assert p[0]==q[0] or p[1]==q[1]
 rect(c,layer,min(p[0],q[0])-w/2,min(p[1],q[1])-w/2,max(p[0],q[0])+w/2,max(p[1],q[1])+w/2)
def via(c,x,y,upper=False):
 lower,cut,top=(M2,V2,M3) if upper else (M1,V1,M2)
 size=.6 if upper else .48
 for layer in [lower,top]:rect(c,layer,x-size/2,y-size/2,x+size/2,y+size/2)
 rect(c,cut,x-.13,y-.13,x+.13,y+.13)
def label(c,name,x,y,layer=M2):c.add_label(name,position=(x,y),layer=(layer[0],10))

nf=gf.import_gds(ROOT/'build/layout-probe-verified/nfet_probe.gds')
pd=gf.import_gds(ROOT/'build/array-primitives/photodiode.gds')
pixel=gf.Component('pixel_physical')
rails={'GND':20,'sense':23,'sf':26,'RST':29,'ROW':32,'VRESET':35,'VDD':38,'COL':41}
# Widely spaced primitives allow independently inspectable routes.
for x in [10,25,40]:
 ref=pixel.add_ref(nf);ref.dmove((x,10))
r=pixel.add_ref(pd);r.dmove((60,10))
for name,y in rails.items():
 ends=(0,80) if name in ['GND','RST','ROW','VRESET','VDD'] else (5,75)
 wire(pixel,M2,(ends[0],y),(ends[1],y))
# terminal → horizontal M2 fanout → vertical M3 → assigned M2 net rail.
def terminal(x,y,track,net):
 via(pixel,x,y);wire(pixel,M2,(x,y),(track,y));via(pixel,track,y,True)
 wire(pixel,M3,(track,y),(track,rails[net]));via(pixel,track,rails[net],True)
for x,nets in [(10,('VRESET','RST','sense')),(25,('VDD','sense','sf')),(40,('sf','ROW','COL'))]:
 terminal(x+.51,10,x+3,nets[0])
 terminal(x,10.94,x,nets[1])
 terminal(x-.51,10,x-3,nets[2])
 terminal(x,8.46,x+5,'GND')
terminal(62,10,65,'sense')
terminal(60,7.01,67,'GND')
# Column connection reserved at right edge, away from the optical aperture.
via(pixel,75,41,True)
# Do not place top-level net labels in repeated pixel cells: top names below.
pixel.write_gds(ROOT/'build/pixel_physical.gds')
array=gf.Component('array_3x3')
for row in range(3):
 for col in range(3):
  ref=array.add_ref(pixel);ref.dmove((80*col,50*row))
# Three independent columns, one continuous vertical conductor each.
for col in range(3):
 x=75+80*col;wire(array,M3,(x,0),(x,145));label(array,f'COL{col}',x,0,M3)
# Extend supply rails to three vertical distribution trunks.
for name,x in [('GND',-10),('VRESET',-7),('VDD',-4)]:
 wire(array,M3,(x,0),(x,145));label(array,name,x,0,M3)
 for row in range(3):
  y=rails[name]+50*row;wire(array,M2,(x,y),(0,y));via(array,x,y,True)
for row in range(3):
 for name in ['RST','ROW']:label(array,f'{name}{row}',0,rails[name]+50*row)
if '--preview' not in sys.argv:
 array.write_gds(ROOT/'build/array_3x3.gds')
array.write_gds(ROOT/'build/array-functional.gds')
meta=dict(pixel_pitch_um=[80,50],routing_bounds_um=[-10.3,-.2,240.2,145.2],diode_area_um2=25,diode_perimeter_um=20,nfet_W_um=1,nfet_L_um=.5)
(ROOT/'layout/array-parameters.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Wrote pixel and connected 3x3 array GDS.')
