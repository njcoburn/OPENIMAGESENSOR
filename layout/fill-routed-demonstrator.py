"""Add isolated central fill to a copy of the routed demonstrator, preserving optical keepouts."""
from pathlib import Path
import hashlib,json
import klayout.db as k
R=Path(__file__).resolve().parents[1]; B=R/'build/filled-demonstrator'; B.mkdir(exist_ok=True)
source=R/'build/routed-demonstrator/demonstrator_routed.gds'
m=json.loads((R/'build/routed-demonstrator/routing.json').read_text())
placement=json.loads((R/'build/pad-proposal/placement.json').read_text());dx,dy=placement['core_translation_um']
L=k.Layout();L.read(str(source));T=L.cell('demonstrator_routed');u=lambda v:round(v/L.dbu)
def region(z):return k.Region(T.begin_shapes_rec(L.layer(z,0))).merged()
optical=k.Region()
for row in range(3):
 for col in range(3):optical.insert(k.Box(u(dx+47+80*col),u(dy+92+50*row),u(dx+73+80*col),u(dy+118+50*row)))
bounds=k.Box(u(356),u(356),u(854),u(854));comp=region(22)
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fill_bounds_um':[356,356,854,854],'optical_keepout_um':26,'layers':{},'floating_fill':True,'added_vias':0}
for z,size,pitch,clearance in [(30,2,4,1),(34,1.2,1.8,.5),(36,1.2,1.8,.5),(42,1.2,1.8,.5),(46,1.2,1.8,.5),(81,1.2,1.8,.5)]:
 existing=region(z);forbidden=existing.sized(u(clearance))|optical
 if z==30:forbidden|=comp.sized(u(1))
 tiles=k.Region()
 for x in range(bounds.left,bounds.right-u(size),u(pitch)):
  for y in range(bounds.bottom,bounds.top-u(size),u(pitch)):tiles.insert(k.Box(x,y,x+u(size),y+u(size)))
 fill=tiles.not_interacting(forbidden)
 assert (fill&optical).is_empty() and (fill&existing.sized(u(clearance))).is_empty()
 if z==30:assert (fill&comp.sized(u(1))).is_empty()
 T.shapes(L.layer(z,0)).insert(fill)
 after=region(z);assert (existing-after).is_empty() and ((after-existing)^fill).is_empty()
 area=T.bbox().area()*L.dbu**2
 report['layers'][str(z)]={'tiles':fill.count(),'added_um2':fill.area()*L.dbu**2,'coverage_before_percent':100*existing.area()*L.dbu**2/area,'coverage_after_percent':100*after.area()*L.dbu**2/area}
 print(z,report['layers'][str(z)],flush=True)
L.write(str(B/'demonstrator_filled.gds'));report['gds_sha256']=hashlib.sha256((B/'demonstrator_filled.gds').read_bytes()).hexdigest()
(B/'fill.json').write_text(json.dumps(report,indent=2)+'\n')
# Flat device LVS uses the same independent reference and labels as the routed checkpoint.
ports=next(line.split()[2:] for line in (R/'circuits/demonstrator-routed.spice').read_text().splitlines() if line.startswith('.subckt demonstrator_routed '))
tcl=['drc off','gds read /foss/designs/build/filled-demonstrator/demonstrator_filled.gds','load demonstrator_routed','select top cell']
for i,name in enumerate(ports,1):tcl += [f'catch {{port {name} make {i}}}',f'port {name} index {i}']
tcl += ['flatten routed_flat','load routed_flat','select top cell','extract no capacitance','extract no coupling','extract no resistance','extract all','ext2spice lvs','ext2spice extresist off','ext2spice short resistor','ext2spice subcircuits top on','ext2spice -o routed_extracted.spice routed_flat','quit -noprompt']
(B/'extract-flat.tcl').write_text('\n'.join(tcl)+'\n')
