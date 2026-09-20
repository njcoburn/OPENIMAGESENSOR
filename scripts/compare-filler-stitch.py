"""Independent, conductor-only finite-volume comparison of stitched and monolithic geometry.

This checks a DC partition interface. It is NOT a replacement for Magic RC/device extraction.
"""
from pathlib import Path
import argparse,json,hashlib,time,subprocess,re
import numpy as np
from scipy.sparse import coo_matrix,save_npz
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/filler-stitch'
p=argparse.ArgumentParser();p.add_argument('--step-um',type=float,default=1);p.add_argument('--skip-spice',action='store_true',help='Run mesh/stitch audit only; no independent ngspice pass claimed');p.add_argument('--electrode-model',choices=['legacy','equipotential'],default='legacy');p.add_argument('--geometry-file',type=Path);p.add_argument('--output-dir',type=Path);p.add_argument('--align-vias',action='store_true');args=p.parse_args();start=time.monotonic()
geometry_file=args.geometry_file or base/'geometry.json';geo=json.loads(geometry_file.read_text())
out=args.output_dir or base/(('mesh-' if args.electrode_model=='legacy' else 'electrode-')+str(args.step_um)+('-via-grid' if args.align_vias else ''));out.mkdir(exist_ok=True)
metals=[34,36,42,46,81];vias=[(35,34,36),(38,36,42),(40,42,46),(41,46,81)];rects={int(z):r for z,r in geo['rects'].items()};seam=geo['seam_dbu'];dbu=geo['dbu_um']
# Align every metal edge and finite electrode edge exactly. Via conductance is apportioned by exact overlap area.
xs={seam};ys=set()
for z in metals+([35,38,40,41] if args.align_vias else []):
 for a,b,c,d in rects[z]:xs.update([a,c]);ys.update([b,d])
for port in geo['ports']:
 for sign in [-1,1]:
  xs.add(round((port['x']+sign*port.get('half_x_um',.1))/dbu));ys.add(round((port['y']+sign*port.get('half_y_um',.1))/dbu))
def refine(values):
 a=sorted(values);v=set(a)
 for lo,hi in zip(a,a[1:]):v.update(np.rint(np.linspace(lo,hi,int(np.ceil((hi-lo)*dbu/args.step_um))+1)).astype(int))
 return np.array(sorted(v))
x=refine(xs);y=refine(ys);dx=np.diff(x);dy=np.diff(y);xc=(x[:-1]+x[1:])/2;yc=(y[:-1]+y[1:])/2;nx=len(dx);ny=len(dy);jseam=int(np.searchsorted(x,seam));shape=(ny,nx)
# Build masks independently for each partition from clipped rectangles, not by dividing an extracted network.
def masks_for(lo,hi):
 masks={z:np.zeros(shape,dtype=bool) for z in metals};areas={}
 for z in metals:
  area=0
  for a,b,c,d in rects[z]:
   a=max(a,lo);c=min(c,hi)
   if a>=c:continue
   j0,j1=np.searchsorted(x,[a,c]);i0,i1=np.searchsorted(y,[b,d]);masks[z][i0:i1,j0:j1]=True;area+=(c-a)*(d-b)
  measured=float(np.sum(masks[z]*dy[:,None]*dx[None,:]));assert abs(measured-area)<1e-5,(z,measured,area)
  areas[z]=area
 return masks,areas
full_masks,full_area=masks_for(x[0],x[-1]);lm,la=masks_for(x[0],seam);rm,ra=masks_for(seam,x[-1])
for z in metals:assert np.array_equal(lm[z]|rm[z],full_masks[z]) and not np.any(lm[z]&rm[z]) and la[z]+ra[z]==full_area[z]
face_rows={z:np.flatnonzero(full_masks[z][:,jseam-1]&full_masks[z][:,jseam]) for z in metals}
intervals={}
for z,rows in face_rows.items():
 runs=np.split(rows,np.where(np.diff(rows)>1)[0]+1);intervals[z]=[[int(y[r[0]]),int(y[r[-1]+1])] for r in runs if len(r)]
assert sum(map(len,intervals.values()))==geo.get('expected_intervals',81),intervals
class Graph:
 def __init__(self):self.next=0;self.parts=[];self.ports={};self.boundary={};self.via_conductance={};self.ranges=[]
 def new(self,count=1):a=self.next;self.next+=count;return a
 def edge(self,a,b,g):
  a=np.asarray(a).ravel();b=np.asarray(b).ravel();g=np.broadcast_to(np.asarray(g).ravel(),a.shape);ok=(a!=b)&(a>=0)&(b>=0);assert np.all(g[ok]>0);self.parts.append((a[ok],b[ok],g[ok]))
 def add(self,masks,lo,hi,side=None):
  begin=len(self.parts)
  ids={};electrodes={z:np.zeros(shape,dtype=bool) for z in metals}
  for z in metals:
   q=np.full(shape,-1,dtype=np.int64);n=int(masks[z].sum());q[masks[z]]=np.arange(self.new(n),self.next);ids[z]=q
  for port in geo['ports']:
   if not (lo<port['x']/dbu<hi):continue
   electrode=(abs(xc-port['x']/dbu)<port.get('half_x_um',.1)/dbu-1e-6)[None,:]&(abs(yc-port['y']/dbu)<port.get('half_y_um',.1)/dbu-1e-6)[:,None]
   assert electrode.any() and np.all(masks[81][electrode]),port
   electrodes[81] |= electrode
   pid=int(ids[81][electrode][0]);ids[81][electrode]=pid;self.ports[port['name']]=pid
  for z,q in ids.items():
   sheet=geo['sheet_ohm_per_square'][str(z)]
   free=(~electrodes[z]).astype(float) if args.electrode_model=='equipotential' else np.ones(shape)
   dist_y=(dy[:-1,None]*free[:-1,:]+dy[1:,None]*free[1:,:])/2
   dist_x=(dx[None,:-1]*free[:,:-1]+dx[None,1:]*free[:,1:])/2
   # Electrode cells have no internal voltage drop; retain only the free-metal half cell.
   gy=dx[None,:]/np.where(dist_y>0,dist_y,1)/sheet
   gx=dy[:,None]/np.where(dist_x>0,dist_x,1)/sheet
   a,b=q[:,:-1],q[:,1:];ok=(a>=0)&(b>=0);self.edge(a[ok],b[ok],np.broadcast_to(gx,a.shape)[ok])
   a,b=q[:-1,:],q[1:,:];ok=(a>=0)&(b>=0);self.edge(a[ok],b[ok],np.broadcast_to(gy,a.shape)[ok])
   if side:
    j=jseam-1 if side=='left' else jseam
    for i in face_rows[z]:
     key=f'M{z}_Y{y[i]}_{y[i+1]}'
     if key not in self.boundary:self.boundary[key]=self.new()
     self.edge([q[i,j]],[self.boundary[key]],[2*dy[i]/dx[j]/sheet])
  for z,lower,upper in vias:
   total=0
   for a,b,c,d in rects[z]:
    if not (lo<=(a+c)/2<hi):continue
    assert lo<=a and c<=hi
    js=np.flatnonzero((x[:-1]<c)&(x[1:]>a));is_=np.flatnonzero((y[:-1]<d)&(y[1:]>b));ii,jj=np.meshgrid(is_,js,indexing='ij')
    overlap=(np.minimum(x[jj+1],c)-np.maximum(x[jj],a))*(np.minimum(y[ii+1],d)-np.maximum(y[ii],b));assert overlap.sum()==(c-a)*(d-b)
    g=overlap/((c-a)*(d-b)*geo['via_ohm_per_cut'][str(z)]);assert np.all(ids[lower][ii,jj]>=0) and np.all(ids[upper][ii,jj]>=0)
    self.edge(ids[lower][ii,jj],ids[upper][ii,jj],g);total+=float(g.sum())
   self.via_conductance[z]=self.via_conductance.get(z,0)+total
  self.ranges.append((side or 'whole',begin,len(self.parts)))
 def finish(self):
  a=np.concatenate([p[0] for p in self.parts]);b=np.concatenate([p[1] for p in self.parts]);g=np.concatenate([p[2] for p in self.parts]);used=np.unique(np.r_[a,b]);remap=np.full(self.next,-1,dtype=np.int64);remap[used]=np.arange(len(used));a=remap[a];b=remap[b]
  self.remap=remap
  self.ports={n:int(remap[i]) for n,i in self.ports.items()};self.boundary={n:int(remap[i]) for n,i in self.boundary.items()}
  G=coo_matrix((np.r_[g,g,-g,-g],(np.r_[a,b,a,b],np.r_[a,b,b,a])),shape=(len(used),len(used))).tocsc();G.sum_duplicates()
  return G
mono=Graph();mono.add(full_masks,x[0],x[-1]);Gm=mono.finish()
stitched=Graph();stitched.add(lm,x[0],seam,'left');stitched.add(rm,seam,x[-1],'right');Gs=stitched.finish()
assert mono.via_conductance.keys()==stitched.via_conductance.keys()
for z in mono.via_conductance:assert abs(mono.via_conductance[z]-stitched.via_conductance[z])<1e-7
expected_boundary={f'M{z}_Y{y[i]}_{y[i+1]}' for z in metals for i in face_rows[z]}
assert set(stitched.boundary)==expected_boundary
assert set(list(stitched.boundary)[1:])!=expected_boundary  # Missing-port negative control.
print('Meshes:',Gm.shape,Gs.shape,'boundary ports',len(stitched.boundary),flush=True)
# Condense each assembled model to its eight outer measurement electrodes.
def solve(G,graph):
 _,groups=connected_components(G,directed=False);rails=[p['name'][:-2] for p in geo['ports'] if p['name'].endswith('_A')];assert len({groups[graph.ports[r+'_A']] for r in rails})==len(rails)
 results={}
 for rail in rails:
  pa,pb=graph.ports[rail+'_A'],graph.ports[rail+'_B'];assert groups[pa]==groups[pb]
  nodes=np.flatnonzero(groups==groups[pa]);nodes=nodes[nodes!=pb];at=int(np.flatnonzero(nodes==pa)[0]);A=G[nodes,:][:,nodes];rhs=np.zeros(len(nodes));rhs[at]=1
  lu=splu(A);v=lu.solve(rhs);res=float(np.max(abs(A@v-rhs)));assert res<1e-7,res;R=float(v[at]);assert R>0
  energy=float(v@(A@v));assert abs(energy-R)/R<1e-8
  results[rail]={'R_ohm':R,'KCL_residual_A':res,'network_nodes':len(nodes)+1,'energy_relative_error':abs(energy-R)/R}
 return results
mr=solve(Gm,mono);sr=solve(Gs,stitched);errors={r:abs(sr[r]['R_ohm']/mr[r]['R_ohm']-1) for r in mr};assert max(errors.values())<1e-8,errors
# Export an actual two-subcircuit resistor netlist and check it with ngspice.
# Every boundary face appears as a distinct shared port; no per-rail ideal shortcut is added.
port_order=[p['name'] for p in geo['ports']]
outer={i:n for n,i in stitched.ports.items()}
subcircuits=[];instances=[]
for side,begin,end in stitched.ranges:
 terminal_ids=[stitched.ports[n] for n in port_order if n.endswith('_A' if side=='left' else '_B')]+list(stitched.boundary.values())
 tokens=['n'+str(i) for i in terminal_ids]
 subcircuits.append('.subckt half_'+side+' '+' '.join(tokens))
 count=0
 for a,b,g in stitched.parts[begin:end]:
  for aa,bb,gg in zip(stitched.remap[a],stitched.remap[b],g):
   subcircuits.append(f'R{count} n{aa} n{bb} {1/gg:.16g}');count+=1
 subcircuits.append('.ends half_'+side)
 instances.append('X'+side+' '+' '.join(outer.get(i,'n'+str(i)) for i in terminal_ids)+' half_'+side)
subcircuits+=['.subckt filler_stitched '+' '.join(port_order)]+instances+['.ends filler_stitched']
(out/'stitched.spice').write_text('\n'.join(subcircuits)+'\n')
bench=['Stitched conductor-only DC audit',f'.include {out}/stitched.spice','Xtest '+' '.join(n[:-2] if n.endswith('_A') else '0' for n in port_order)+' filler_stitched']
bench += [f'I{r} 0 {r} 1' for r in mr]
bench += ['.options reltol=1e-9 abstol=1e-12','.control','op','print '+' '.join('v('+r+')' for r in mr),'quit','.endc','.end']
(out/'testbench.spice').write_text('\n'.join(bench)+'\n')
spice={};spice_errors={};spice_status='not_requested'
if not args.skip_spice:
 with (out/'ngspice.log').open('w') as log:
  try:
   run=subprocess.run(['ngspice','-b',str(out/'testbench.spice')],stdout=log,stderr=subprocess.STDOUT,timeout=120)
   spice_status='completed'
  except subprocess.TimeoutExpired:spice_status='timeout'
 (out/'ngspice-attempt.json').write_text(json.dumps({'status':spice_status,'timeout_s':120},indent=2)+'\n')
 if spice_status=='completed':
  log=(out/'ngspice.log').read_text();assert run.returncode==0 and not re.search(r'Error|singular matrix|timestep too small',log,re.I),log[-2000:]
  spice={r:float(re.search(r'v\('+r.lower()+r'\)\s*=\s*([+eE.0-9-]+)',log)[1]) for r in sr}
  spice_errors={r:abs(spice[r]/sr[r]['R_ohm']-1) for r in sr};assert max(spice_errors.values())<2e-6,spice_errors

# Preserve matrices, external terminal maps and EVERY independently joined boundary port.
save_npz(out/'monolithic-conductance.npz',Gm);save_npz(out/'stitched-conductance.npz',Gs)
(out/'ports.json').write_text(json.dumps({'monolithic':mono.ports,'stitched':stitched.ports,'boundary_ports':stitched.boundary,'boundary_intervals_dbu':intervals},indent=2)+'\n')
result={'ngspice_R_ohm':spice,'ngspice_relative_error':spice_errors,'ngspice_check_pass':spice_status=='completed','ngspice_status':spice_status,'step_um':args.step_um,'via_edges_aligned':args.align_vias,'electrode_model':args.electrode_model,'geometry_file':str(geometry_file),'method':'Independent conductor-only finite-volume DC network; exact Manhattan metal coverage; per-cut via conductance distributed by overlap area; outer electrode geometry from ports; treatment recorded in electrode_model. No devices/substrate/capacitance.','monolithic':mr,'stitched':sr,'relative_stitch_error':errors,'stitch_limit':1e-8,'stitch_pass':True,'boundary_intervals':sum(map(len,intervals.values())),'boundary_ports':len(stitched.boundary),'metal_area_dbu2':full_area,'via_conductance_S':mono.via_conductance,'node_counts':[Gm.shape[0],Gs.shape[0]],'geometry_sha256':hashlib.sha256(geometry_file.read_bytes()).hexdigest(),'elapsed_s':time.monotonic()-start}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
