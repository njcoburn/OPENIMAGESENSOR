"""Foundry supply-ring test vehicle. Signal-pad placement/routing is a later step."""
from pathlib import Path
import json
import klayout.db as k
root=Path(__file__).resolve().parents[1];out=root/'build/power-ring';out.mkdir(exist_ok=True)
l=k.Layout();l.dbu=.001;u=lambda x:round(x/l.dbu)
s=k.Layout();s.read('/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/gds/gf180mcu_fd_io.gds')
top=l.create_cell('power_ring');cells={}
for n in ['dvdd','dvss','cor','fill10']:
 c=l.create_cell('gf180mcu_fd_io__'+n);c.copy_tree(s.cell(c.name));cells[n]=c
W,H=1110,1010
instances=[]
def put(n,rot,x,y):
 top.insert(k.CellInstArray(cells[n].cell_index(),k.Trans(rot,False,u(x),u(y))))
 instances.append({'macro':n,'rotation':90*rot,'x_um':x,'y_um':y})
for r,x,y in [(0,0,0),(1,W,0),(2,W,H),(3,0,H)]:put('cor',r,x,y)
put('dvdd',0,355,0);put('dvss',0,430,0)
for x in range(505,755,10):put('fill10',0,x,0)
for x in range(355,755,10):put('fill10',2,W-x,H)
for y in range(355,655,10):
 put('fill10',1,W,y);put('fill10',3,0,H-y)
def box(c,layer,a,b,x,y):c.shapes(l.layer(layer,0)).insert(k.Box(u(a),u(b),u(x),u(y)))
def wire(c,layer,a,b,width):
 assert a[0]==b[0] or a[1]==b[1]
 box(c,layer,min(a[0],b[0])-width/2,min(a[1],b[1])-width/2,max(a[0],b[0])+width/2,max(a[1],b[1])+width/2)
def label(c,n,layer,x,y):c.shapes(l.layer(layer,10)).insert(k.Text(n,k.Trans(u(x),u(y))))
# Six M2 fingers per supply pad, strapped outside the macro boundary.
for net,origin,target_y in [('AVDD',355,365),('AVSS',430,355)]:
 for x in [6.11,18.885,30.735,44.265,56.115,68.89]:
  wire(top,36,(origin+x,349.5),(origin+x,target_y),.8)
 wire(top,36,(origin+6.11,target_y),(origin+68.89,target_y),2)
 label(top,net,36,origin+30.735,target_y)
# Core-facing supply endpoints, still electrically the same nets before RC extraction.
label(top,'AVDD_BOND',81,393.9,34.275)
label(top,'AVSS_BOND',81,467.985,32.735)
l.write(str(out/'power_ring.gds'))
# No invented resistance: route geometry is preserved for extraction.
(out/'placement.json').write_text(json.dumps({'width_um':W,'height_um':H,'instances':instances,
 'supply_pad_count':2,'corner_count':4,'clamp_count':10,'scope':'Power ring test vehicle; no signal pads, seal ring, or sensor placed.'},indent=2)+'\n')
sp=['.include /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/spice/gf180mcu_fd_io.spice',
 '.subckt power_ring AVDD AVSS',
 'Xvdd AVDD AVSS AVSS gf180mcu_fd_io__dvdd',
 'Xvss AVDD AVSS AVDD gf180mcu_fd_io__dvss']
for i in range(4):sp.append(f'Xcor{i} AVDD AVSS AVDD AVSS gf180mcu_fd_io__cor')
for i,inst in enumerate(x for x in instances if x['macro']=='fill10'):
 sp.append(f'Xfill{i} AVDD AVSS AVDD AVSS gf180mcu_fd_io__fill10')
sp+=['.ends power_ring'];(out/'power_ring.spice').write_text('\n'.join(sp)+'\n')
print('Placed',len(instances),'macros; 10 clamps; size',W,H)
# Assembly preview with real sensor geometry and routed power only.
# Functional signal ports remain unbonded at this checkpoint.
core_src=k.Layout();core_src.read(str(root/'checkpoints/integrated/sensor_3x3.gds'))
core=l.create_cell('sensor_3x3');core.copy_tree(core_src.cell('sensor_3x3'))
assembly=l.create_cell('ring_sensor_power')
assembly.insert(k.CellInstArray(top.cell_index(),k.Trans()))
assembly.insert(k.CellInstArray(core.cell_index(),k.Trans(u(420),u(385))))
def via(c,x,y,upper=False):
 for layer in ([42,46] if upper else [36,42]):box(c,layer,x-.6,y-.6,x+.6,y+.6)
 for dx in [-.26,.26]:
  for dy in [-.26,.26]:box(c,40 if upper else 38,x+dx-.13,y+dy-.13,x+dx+.13,y+dy+.13)
# AVDD M3 trunk; AVSS M4 trunk; avoid crossings on the same conductor layer.
wire(assembly,36,(385.735,365),(385.735,370),2);via(assembly,385.735,370)
for a,b in [((385.735,370),(380,370)),((380,370),(380,473)),((380,473),(378,473))]:wire(assembly,42,a,b,4)
via(assembly,378,473,True)
wire(assembly,46,(378,473),(384,473),2)
wire(assembly,36,(460.735,355),(460.735,360),2);via(assembly,460.735,360);via(assembly,460.735,360,True)
for a,b in [((460.735,360),(374,360)),((374,360),(374,469))]:wire(assembly,46,a,b,4)
wire(assembly,46,(374,469),(384,469),2)
l.write(str(out/'ring_sensor_power.gds'))
# Isolated copy of the actual added routes for a fast, separately auditable RC check.
leads=l.create_cell('power_leads')
for idx in l.layer_indexes():
 for shape in assembly.shapes(idx).each():leads.shapes(idx).insert(shape)
for n,z,x,y in [('VDD_RING',36,385.735,365),('VSS_RING',36,460.735,355),('VDD_CORE',46,384,473),('VSS_CORE',46,384,469)]:label(leads,n,z,x,y)
options=k.SaveLayoutOptions();options.add_cell(leads.cell_index());l.write(str(out/'power_leads.gds'),options)
