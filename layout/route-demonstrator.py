"""Route the approved working 24-pad arrangement; diagnostics remain isolated.
Uses the existing functional core and protection geometry. No submission claim.
"""
from pathlib import Path
import json,heapq,hashlib,math
import klayout.db as k
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];B=R/'build/routed-demonstrator';B.mkdir(exist_ok=True)
m=json.loads((R/'build/pad-proposal/placement.json').read_text());L=k.Layout();L.read(str(R/'build/pad-proposal/demonstrator_pad_proposal.gds'));T=L.cell('demonstrator_pad_proposal');T.name='demonstrator_routed';u=lambda a:round(a/L.dbu)
# Replace only the core's dummy-filled version with its saved functional reference.
S=k.Layout();S.read(str(R/'build/integrated/sensor-functional.gds'));core=L.cell('sensor_3x3');core.clear();core.copy_tree(S.cell('sensor_3x3'))
S=k.Layout();S.read(str(R/'build/pad-layout/secondary-functional.gds'));secondary=L.create_cell('local_secondary');secondary.copy_tree(S.cell('analog_secondary'))
dx,dy=m['core_translation_um'];ports=json.loads((R/'build/integrated/placement.json').read_text())['ports'];ports={n:[x+dx,y+dy,z] for n,(x,y,z) in ports.items()}
metals=[34,36,42,46,81];cuts=[35,38,40,41];routes=[];protected=[];probes=[]
drawn={};active='fixed'
def rect(z,x0,y0,x1,y1):
 b=k.Box(u(x0),u(y0),u(x1),u(y1));T.shapes(L.layer(z,0)).insert(b);drawn.setdefault(active,{}).setdefault(z,[]).append(b)
def wire(z,a,b,w=.8):
 assert abs(a[0]-b[0])<1e-8 or abs(a[1]-b[1])<1e-8,(a,b)
 rect(z,min(a[0],b[0])-w/2,min(a[1],b[1])-w/2,max(a[0],b[0])+w/2,max(a[1],b[1])+w/2)
def via(a,lo,hi):
 x,y=a
 for z in metals[metals.index(lo):metals.index(hi)+1]:rect(z,x-.6,y-.6,x+.6,y+.6)
 for z in cuts[metals.index(lo):metals.index(hi)]:rect(z,x-.13,y-.13,x+.13,y+.13)
def polywire(z,ps,w=.8):
 for a,b in zip(ps,ps[1:]):wire(z,a,b,w)
def transform(p,x,y):
 t=k.Trans(p['rotation_deg']//90,False,u(p['origin_x_um']),u(p['origin_y_um']));q=t.trans(k.Point(u(x),u(y))).to_dtype(L.dbu);return (q.x,q.y)
def ringpoint(p,depth,tangent):return transform(p,tangent,depth)
# M5 ground and power distribution rings, placed in the inner routing annulus.
for name,a,b in [('GND',400,810),('VDD',408,802)]:
 polywire(81,[(a,a),(b,a),(b,b),(a,b),(a,a)],4)
# Supply pads: connect all six physical M2 fingers, then cross any outer ring on M4.
for p in m['pads']:
 if p['core_net'] not in ['GND','VDD']:continue
 for x in [6.11,18.885,30.735,44.265,56.115,68.89]:wire(36,transform(p,x,349.5),transform(p,x,360),.8)
 wire(36,transform(p,6.11,360),transform(p,68.89,360),2)
 start=transform(p,60,360);via(start,36,46)
 depth=400 if p['core_net']=='GND' else 408
 end=transform(p,60,depth)
 wire(46,start,end,2);via(end,46,81)
 probes.append(dict(net=p['core_net'],layer=81,point=[p['pad_label_x_um'],p['pad_label_y_um']],kind='supply_bond',pad=p['pad_id']))
# Core supply entry uses M4 so it crosses the other M5 ring without connecting.
for name,x in [('GND',400),('VDD',408)]:
 px,py,z=ports[name];wire(46,(x,py),(px,py),2);via((x,py),46,81)
# Local secondary protection for all 13 functional signal ports.
for p in m['pads']:
 net=p['core_net']
 if net in ['GND','VDD','COL0','COL1','COL2','OUT']:continue
 t=k.Trans(p['rotation_deg']//90,False,u(p['origin_x_um']),u(p['origin_y_um']))
 T.insert(k.CellInstArray(secondary.cell_index(),t*k.Trans(u(42.5),u(365))))
 a=transform(p,33.65,349.655);b=transform(p,33.65,376.17);c=transform(p,37.5,376.17)
 polywire(36,[a,b,c])
 for supply,y,depth in [('GND',367,400),('VDD',388,408)]:
  a=transform(p,37.5,y);tangent=30 if supply=='GND' else 37.5;b=transform(p,tangent,depth);via(a,36,46);polywire(46,[a,transform(p,tangent,y),b],1);via(b,46,81)
 start=transform(p,67.5,377)
 protected.append(dict(net=net,pad=p['pad_id'],start=start,target=ports[net][:2],target_layer=ports[net][2],pad_side=transform(p,37.5,376.17),secondary_core=start,secondary_gnd=transform(p,37.5,367),secondary_vdd=transform(p,37.5,388)))
# Preserve optical keepouts at all nine existing detector sites.
optical=k.Region()
for row in range(3):
 for col in range(3):optical.insert(k.Box(u(dx+47+80*col),u(dy+92+50*row),u(dx+73+80*col),u(dy+118+50*row)))
# Grid route M3/M4/M5 with physical-metal obstacles and optical exclusions.
low=352;high=858;N=high-low+1;layers=[42,46,81]
def raster(region):
 result=np.zeros((N,N),dtype=bool)
 for p in region.each():
  b=p.bbox().to_dtype(L.dbu)
  if b.right<low or b.left>high or b.top<low or b.bottom>high:continue
  # Polygon holes must clear only their own polygon, never a different net
  # already drawn inside a surrounding ring's hole.
  im=Image.new('1',(N,N));draw=ImageDraw.Draw(im)
  draw.polygon([(q.x*L.dbu-low,q.y*L.dbu-low) for q in p.each_point_hull()],fill=1)
  for h in range(p.holes()):draw.polygon([(q.x*L.dbu-low,q.y*L.dbu-low) for q in p.each_point_hole(h)],fill=0)
  result|=np.array(im,dtype=bool)
 return result
def pointindex(p):return (round(p[0])-low,round(p[1])-low)
def mask():
 return [raster(k.Region(T.begin_shapes_rec(L.layer(z,0))).sized(u(1.05))|optical) for z in layers]
def route(entry):
 global active
 active=entry['net']
 start,end=entry['start'],entry['target'];occ=mask();si=pointindex(start);ei=pointindex(end)
 # Endpoint landing regions are intentionally connected to their own terminals.
 # Independent physical-net checks below detect any unintended landing short.
 for a in [si,ei]:
  for o in occ:o[max(0,a[1]-1):a[1]+2,max(0,a[0]-1):a[0]+2]=False
 # Reserve the via landing space of all other functional terminals.
 for other in protected:
  if other['net']==entry['net']:continue
  for p in [other['start'],other['target']]:
   ox,oy=pointindex(p)
   for o in occ:o[max(0,oy-2):oy+3,max(0,ox-2):ox+3]=True
 initial=(0,*si);goals={(j,*ei) for j in range(3)};pq=[(0,0,initial)];dist={initial:0};prev={};last=None
 while pq:
  _,cost,state=heapq.heappop(pq)
  if cost!=dist.get(state):continue
  z,x,y=state
  if state in goals:last=state;break
  for dz,ax,ay in [(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,0,0),(-1,0,0)]:
   nz,nx,ny=z+dz,x+ax,y+ay
   if not(0<=nz<3 and 0<=nx<N and 0<=ny<N) or occ[nz][ny,nx]:continue
   step=5 if dz else 1+(0.12 if (nz==0 and ay) or (nz==1 and ax) else .0)+(0.3 if nz==2 else 0)
   nc=cost+step;ns=(nz,nx,ny)
   if nc<dist.get(ns,float('inf')):
    dist[ns]=nc;prev[ns]=state;heur=abs(nx-ei[0])+abs(ny-ei[1]);heapq.heappush(pq,(nc+heur,nc,ns))
 assert last is not None,entry['net']
 path=[last]
 while path[-1]!=initial:path.append(prev[path[-1]])
 path.reverse();gstart=(si[0]+low,si[1]+low);gend=(ei[0]+low,ei[1]+low)
 via(start,36,42);polywire(42,[start,(gstart[0],start[1]),gstart])
 for a,b in zip(path,path[1:]):
  z,x,y=a;nz,nx,ny=b;p=(x+low,y+low);q=(nx+low,ny+low)
  if z!=nz:via(p,min(layers[z],layers[nz]),max(layers[z],layers[nz]))
  else:wire(layers[z],p,q)
 finish=layers[last[0]];polywire(finish,[gend,(end[0],gend[1]),end]);via(end,min(entry['target_layer'],finish),max(entry['target_layer'],finish))
 routes.append(dict(net=entry['net'],grid_steps=len(path),path=[[layers[z],x+low,y+low] for z,x,y in path],source=entry['start'],target=end))
 print('Routed',entry['net'],len(path),'steps',flush=True)
def core_nets(stage):
 n=k.LayoutToNetlist(k.RecursiveShapeIterator(L,T,[]));ml={z:n.make_polygon_layer(L.layer(z,0),'m'+str(z)) for z in metals}
 for v in ml.values():n.connect(v)
 for cut,lo,hi in zip(cuts,metals,metals[1:]):
  v=n.make_polygon_layer(L.layer(cut,0),'v'+str(cut));n.connect(ml[lo],v);n.connect(v,ml[hi])
 n.extract_netlist();groups={}
 for name,(x,y,z) in ports.items():
  q=n.probe_net(ml[z],k.DPoint(x,y));key=(q.circuit().name,q.cluster_id);groups.setdefault(key,[]).append(name)
 bad=[v for v in groups.values() if len(v)>1]
 print('Core separation',stage,bad,flush=True)
 if bad:
  L.write(str(B/'failed-stage.gds'))
  for other in drawn:
   if other==stage:continue
   for z in metals:
    hit=k.Region(drawn.get(stage,{}).get(z,[]))&k.Region(drawn[other].get(z,[]))
    if not hit.is_empty():print('Route intersection',stage,other,z,[str(p.bbox().to_dtype(L.dbu)) for p in hit.each()][:15],flush=True)
  (B/'failed-routes.json').write_text(json.dumps(routes))
  raise RuntimeError((stage,bad))
core_nets('before signal routing')
for entry in protected:
 route(entry)
 core_nets(entry['net'])
# Check new top-level metal never covers the detector keepouts.
for z in metals:assert (k.Region(T.shapes(L.layer(z,0)))&optical).is_empty(),('Optical crossing',z)
# Save functional assembly first. Old core dummy fill was removed; density is a later gate.
options=k.SaveLayoutOptions();options.add_cell(T.cell_index());L.write(str(B/'demonstrator_routed.gds'),options)
meta=dict(ports=ports,protected=protected,supply_probes=probes,routes=routes,pad_map=m['pads'],scope='Functional routing candidate; diagnostics unconnected; existing functional core/protection; dummy fill not regenerated; no full-chip sign-off',sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'build/pad-proposal/demonstrator_pad_proposal.gds',R/'build/integrated/sensor-functional.gds',R/'build/pad-layout/secondary-functional.gds']})
(B/'routing.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Wrote routing candidate',flush=True)
