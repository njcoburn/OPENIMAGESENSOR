"""Independent metal/via connectivity; no joining disconnected same-name labels."""
from pathlib import Path
import json
import sys
import klayout.db as k
root=Path(__file__).resolve().parents[1];out=root/'build/power-ring'
assembly='--assembly' in sys.argv
cellname='ring_sensor_power' if assembly else 'power_ring'
l=k.Layout();l.read(str(out/(cellname+'.gds')));top=l.cell(cellname)
n=k.LayoutToNetlist(k.RecursiveShapeIterator(l,top,[]))
metal={z:n.make_polygon_layer(l.layer(z,0),'metal'+str(z)) for z in [34,36,42,46,81]}
for r in metal.values():n.connect(r)
for z,a,b in [(35,34,36),(38,36,42),(40,42,46),(41,46,81)]:
 v=n.make_polygon_layer(l.layer(z,0),'via'+str(z));n.connect(metal[a],v);n.connect(v,metal[b])
n.extract_netlist()
def probe(layer,x,y):
 net=n.probe_net(metal[layer],k.DPoint(x,y));assert net is not None,(layer,x,y)
 return (net.circuit().name, net.cluster_id)
vp=probe(81,393.9,34.275);vg=probe(81,467.985,32.735)
assert vp != vg,'Power-to-ground metal short'
checks=[]
probe_top=l.cell('power_ring') if assembly else top
for inst in probe_top.each_inst():
 c=inst.cell
 for z in [42,46,81]:
  for sh in c.shapes(l.layer(z,10)).each():
   if not sh.is_text() or sh.text.string not in ['VDD','DVDD','VSS','DVSS']:continue
   offset=sh.text.trans.disp
   pt=inst.cplx_trans*k.Point(offset.x,offset.y);pt=pt.to_dtype(l.dbu)
   expected=vp if sh.text.string in ['VDD','DVDD'] else vg
   actual=probe(z,pt.x,pt.y)
   checks.append({'macro':c.name,'rail':sh.text.string,'layer':z,'x_um':pt.x,'y_um':pt.y,'pass':actual==expected})
for net,x,y in [('AVDD',385.735,365),('AVSS',460.735,355)]:
 checks.append({'terminal':net,'pass':probe(36,x,y)==(vp if net=='AVDD' else vg)})
if assembly:
 for net,x,y in [('AVDD',384,473),('AVSS',384,469)]:
  checks.append({'sensor_terminal':net,'pass':probe(46,x,y)==(vp if net=='AVDD' else vg)})
r={'no_metal_power_ground_short':True,'checks':checks,'all_pass':all(x['pass'] for x in checks),
   'method':'Metal1-5 and via1-4 physical overlap only; no label-based joining; no device extraction.'}
(out/('assembly-connectivity.json' if assembly else 'connectivity.json')).write_text(json.dumps(r,indent=2)+'\n')
print('Physical rail probes:',len(checks),'passed:',sum(x['pass'] for x in checks))
assert r['all_pass']
