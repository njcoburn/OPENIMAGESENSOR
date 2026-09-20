"""Conservative four-layer Manhattan routing of the provisional boards.
Native KiCad DRC and schematic-net comparison remain the acceptance checks.
"""
from pathlib import Path
import json,heapq,math,time,sys
import numpy as np
import pcbnew as p
R=Path(__file__).resolve().parent
name=sys.argv[1];D=R/'kicad'/name;meta=json.loads((D/'design.json').read_text());B=p.LoadBoard(str(D/(name+'.kicad_pcb')))
assert not list(B.GetTracks()), 'Regenerate clean boards before routing; do not overwrite manual routing.'
step=.1;layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];MM=p.FromMM;V=lambda x,y:p.VECTOR2I(MM(x),MM(y));u=p.ToMM
xmin,ymin,xmax,ymax=meta['bounds'];NX=round((xmax-xmin)/step)+1;NY=round((ymax-ymin)/step)+1
occ=np.zeros((4,NY,NX),dtype=np.int32);voc=np.zeros_like(occ);endpoints={}
holes=np.zeros((NY,NX),dtype=bool);existing_vias={}
def block_hole(x,y,r):
 for yy in range(max(0,y-math.ceil(r/step)),min(NY,y+math.ceil(r/step)+1)):
  for xx in range(max(0,x-math.ceil(r/step)),min(NX,x+math.ceil(r/step)+1)):
   if math.hypot(xx-x,yy-y)*step<r:holes[yy,xx]=True
def xy(pt):return (round((u(pt.x)-xmin)/step),round((u(pt.y)-ymin)/step))
def real(x,y):return xmin+x*step,ymin+y*step
def merge_box(a,l,x0,y0,x1,y1,net):
 x0=max(0,int(math.floor((x0-xmin)/step)));x1=min(NX-1,int(math.ceil((x1-xmin)/step)));y0=max(0,int(math.floor((y0-ymin)/step)));y1=min(NY-1,int(math.ceil((y1-ymin)/step)))
 z=a[l,y0:y1+1,x0:x1+1];z[:]=np.where((z==0)|(z==net),net,-1)
# Mechanical clearances; vias must clear every layer.
for a in [occ,voc]:
 a[:,:5,:]=-1;a[:,-5:,:]=-1;a[:,:,:5]=-1;a[:,:,-5:]=-1
 if meta['aperture']:
  x0,y0,x1,y1=meta['aperture']
  for l in range(4):merge_box(a,l,x0-.5,y0-.5,x1+.5,y1+.5,-1)
 elif name=='die_carrier':
  for l in range(4):merge_box(a,l,48.7,48.7,51.3,51.3,-1)
for f in sorted(B.GetFootprints(),key=lambda f:f.GetReference()):
 for pad in sorted(f.Pads(),key=lambda pad:pad.GetNumber()):
  if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]:
   hx,hy=xy(pad.GetPosition());block_hole(hx,hy,max(u(pad.GetDrillSize().x),u(pad.GetDrillSize().y))/2+.41)
  net=pad.GetNetCode() or -1;bb=pad.GetBoundingBox();x0=u(bb.GetX());y0=u(bb.GetY());x1=x0+u(bb.GetWidth());y1=y0+u(bb.GetHeight())
  ls=[j for j,l in enumerate(layers) if pad.IsOnLayer(l)]
  if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:
   ls=list(range(4));extra=1.2 if f.GetReference() in ['H1','H2','H3','H4'] else .3
  else:extra=0
  for l in ls:
   merge_box(occ,l,x0-.25-extra,y0-.25-extra,x1+.25+extra,y1+.25+extra,net)
   merge_box(voc,l,x0-.45-extra,y0-.45-extra,x1+.45+extra,y1+.45+extra,net)
  if net>0:endpoints.setdefault(net,[]).append(dict(point=xy(pad.GetPosition()),layers=ls,pos=(u(pad.GetPosition().x),u(pad.GetPosition().y)),ref=f.GetReference(),pad=pad.GetNumber()))

def segment(net,l,a,b):
 if a==b:return
 t=p.PCB_TRACK(B);t.SetStart(V(*a));t.SetEnd(V(*b));t.SetWidth(MM(.2));t.SetLayer(layers[l]);t.SetNetCode(net);B.Add(t)
def via(net,x,y):
 if (x,y) in existing_vias:
  assert existing_vias[x,y]==net;return
 existing_vias[x,y]=net;block_hole(x,y,.56)
 v=p.PCB_VIA(B);v.SetPosition(V(*real(x,y)));v.SetWidth(MM(.6));v.SetDrill(MM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(net);B.Add(v)
def search(net,a,b):
 sx,sy=a['point'];tx,ty=b['point'];goal={(l,ty,tx) for l in b['layers']};heap=[];dist={};prev={}
 def heur(l,y,x):return (abs(x-tx)+abs(y-ty)) * 1.15 + (0 if l in b['layers'] else 18)
 for l in a['layers']:
  key=(l,sy,sx);dist[key]=0;heapq.heappush(heap,(heur(*key),0,key))
 count=0
 while heap:
  _,g,key=heapq.heappop(heap)
  if g!=dist.get(key):continue
  if key in goal:
   path=[key]
   while key in prev:key=prev[key];path.append(key)
   return path[::-1],count
  l,y,x=key;count+=1
  if count>1500000:return None,count
  moves=[]
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   xx=x+dx;yy=y+dy
   if 0<=xx<NX and 0<=yy<NY and int(occ[l,yy,xx]) in [0,net]:moves.append(((l,yy,xx),1))
  if (not holes[y,x] or existing_vias.get((x,y))==net) and all(int(voc[ll,y,x]) in [0,net] for ll in range(4)):
   for ll in range(4):
    if ll!=l:moves.append(((ll,y,x),20))
  for nxt,cost in moves:
   ng=g+cost
   if ng<dist.get(nxt,1e30):dist[nxt]=ng;prev[nxt]=key;heapq.heappush(heap,(ng+heur(*nxt),ng,nxt))
 return None,count

def reserve(net,path):
 for l,y,x in path:
  xx,yy=real(x,y);merge_box(occ,l,xx-.36,yy-.36,xx+.36,yy+.36,net);merge_box(voc,l,xx-.56,yy-.56,xx+.56,yy+.56,net)
 for a,b in zip(path,path[1:]):
  if a[0]!=b[0]:
   l,y,x=a;xx,yy=real(x,y)
   for ll in range(4):merge_box(occ,ll,xx-.56,yy-.56,xx+.56,yy+.56,net);merge_box(voc,ll,xx-.76,yy-.76,xx+.76,yy+.76,net)

def emit(net,path,a,b):
 # Exact pad-center stubs account for pads not on the routing grid.
 segment(net,path[0][0],a['pos'],real(path[0][2],path[0][1]));segment(net,path[-1][0],real(path[-1][2],path[-1][1]),b['pos'])
 start=path[0];last=start;direction=None
 for cur in path[1:]:
  if cur[0]!=last[0]:
   segment(net,last[0],real(start[2],start[1]),real(last[2],last[1]));via(net,last[2],last[1]);start=cur;direction=None
  else:
   dr=(cur[1]-last[1],cur[2]-last[2])
   if direction is not None and dr!=direction:
    segment(net,last[0],real(start[2],start[1]),real(last[2],last[1]));start=last
   direction=dr
  last=cur
 segment(net,last[0],real(start[2],start[1]),real(last[2],last[1]))

# Escape fine-pitch IC pads before global routing can obstruct their exits.
# Stagger the via rows to retain clearance between adjacent signal vias.
for f in sorted(B.GetFootprints(),key=lambda f:f.GetReference()):
 if not f.GetReference().startswith('U'):continue
 cx,cy=u(f.GetPosition().x),u(f.GetPosition().y);groups={}
 for pad in sorted(f.Pads(),key=lambda pad:pad.GetNumber()):
  if pad.GetNetCode()<=0:continue
  px,py=u(pad.GetPosition().x),u(pad.GetPosition().y);dx,dy=px-cx,py-cy
  side=('x',1 if dx>0 else -1) if name=='tester_dock' or abs(dx)>abs(dy) else ('y',1 if dy>0 else -1)
  groups.setdefault(side,[]).append(pad)
 for (axis,sign),pads in groups.items():
  pads.sort(key=lambda a:u(a.GetPosition().y if axis=='x' else a.GetPosition().x))
  for rank,pad in enumerate(pads):
   net=pad.GetNetCode();e=next(z for z in endpoints[net] if z['ref']==f.GetReference() and z['pad']==pad.GetNumber())
   px,py=e['pos'];distance=3.0;spread=2.0
   tx=px+sign*distance if axis=='x' else cx+(px-cx)*spread
   ty=cy+(py-cy)*spread if axis=='x' else py+sign*distance
   gx,gy=xy(V(tx,ty));tx,ty=real(gx,gy)
   # Local fanout is verified geometrically by native DRC after routing.
   ex,ey=(px+sign*1.0,py) if axis=='x' else (px,py+sign*1.0)
   segment(net,0,e['pos'],(ex,ey));segment(net,0,(ex,ey),(tx,ty));via(net,gx,gy)
   # Rasterize the direct escape corridor at the grid sampling resolution.
   path=[]
   for (ax,ay),(bx,by) in [((px,py),(ex,ey)),((ex,ey),(tx,ty))]:
    n=max(1,math.ceil(math.hypot(bx-ax,by-ay)/step))
    path.extend((0,round((ay+(by-ay)*i/n-ymin)/step),round((ax+(bx-ax)*i/n-xmin)/step)) for i in range(n+1))
   reserve(net,path+[(3,gy,gx)])
   e['point']=(gx,gy);e['layers']=[0,1,2,3];e['pos']=(tx,ty)

# Local analog paths first, then low-fanout signals, then supply trunks.
names={n:B.FindNet(n).GetNetname() for n in endpoints}
order=sorted(endpoints,key=lambda n:(names[n] in ['VDD','GND'],names[n] not in ['BUF','BUF_DRV','ADC_IN','RESET_DIV','BIAS','PREF'],len(endpoints[n])))
results=[];start=time.monotonic()
for net in order:
 es=endpoints[net];connected=[es[0]];pending=es[1:]
 while pending:
  _,a,b=min(((abs(a['point'][0]-b['point'][0])+abs(a['point'][1]-b['point'][1]),i,j) for i,a in enumerate(connected) for j,b in enumerate(pending)),key=lambda z:z[0])
  a=connected[a];b=pending[b]
  path,visited=search(net,a,b)
  results.append(dict(net=names[net],a=a['ref']+'.'+a['pad'],b=b['ref']+'.'+b['pad'],routed=path is not None,visited=visited))
  if path:emit(net,path,a,b);reserve(net,path)
  print(results[-1],flush=True)
  connected.append(b);pending.remove(b)
 p.SaveBoard(str(D/(name+'.kicad_pcb')),B)
report=dict(seconds=time.monotonic()-start,connections=results,failed=sum(not r['routed'] for r in results))
(D/'routing.json').write_text(json.dumps(report,indent=2)+'\n');print('Finished',name,'failed',report['failed'],flush=True)
