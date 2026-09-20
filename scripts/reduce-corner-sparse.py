"""Exact bounded-degree star-mesh elimination avoids a dense terminal clique."""
from pathlib import Path
from collections import defaultdict
import json,heapq,itertools
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced/corner-full';lines=(R/'build/charge-reference/corner-full/reference.spice').read_text().splitlines();header=next(s for s in lines if s.startswith('.subckt'));keep=set(header.split()[2:]);devices=[];edges=[];graph=defaultdict(dict)
for s in lines:
 t=s.split()
 if not t:continue
 if t[0].startswith('R'):
  a,b=t[1:3];g=1/float(t[3]);edges.append((a,b,g));graph[a][b]=graph[a].get(b,0)+g;graph[b][a]=graph[b].get(a,0)+g
 elif t[0].startswith(('X','D')):
  devices.append(s);i=next(i for i,x in enumerate(t[1:],1) if x.startswith(('nfet_','pfet_','cap_nmos_','ppolyf_','diode_')));keep.update(t[1:i])
for mode in ['nominal','remote']:
 for s in (B/f'{mode}.spice').read_text().splitlines():
  if s.startswith('C'):keep.update(s.split()[1:3])
heap=[(len(v),n) for n,v in graph.items() if n not in keep and len(v)<=12];heapq.heapify(heap);eliminated=0
while heap:
 deg,n=heapq.heappop(heap)
 if n not in graph or n in keep or len(graph[n])!=deg or deg>12:continue
 ns=list(graph[n].items());total=sum(g for _,g in ns)
 for a,g in ns:del graph[a][n]
 for (a,ga),(b,gb) in itertools.combinations(ns,2):
  g=ga*gb/total;v=graph[a].get(b,0)+g;graph[a][b]=v;graph[b][a]=v
 del graph[n];eliminated+=1
 for a,g in ns:
  if a not in keep and len(graph[a])<=12:heapq.heappush(heap,(len(graph[a]),a))
print('Eliminated',eliminated,'retained',len(graph),'edges',sum(map(len,graph.values()))//2,flush=True)
retained=sorted(graph);removed=sorted({n for a,b,g in edges for n in (a,b)}-set(retained));order=retained+removed;idx={n:i for i,n in enumerate(order)};k=len(retained)
def matrix(es,size,index):
 rr=[];cc=[];vv=[]
 for a,b,g in es:
  i,j=index[a],index[b];rr.extend([i,j,i,j]);cc.extend([i,j,j,i]);vv.extend([g,g,-g,-g])
 return coo_matrix((vv,(rr,cc)),shape=(size,size)).tocsc()
newedges=[(a,b,g) for a,v in graph.items() for b,g in v.items() if a<b];G=matrix(edges,len(order),idx);H=matrix(newedges,k,{n:i for i,n in enumerate(retained)});lu=splu(G[k:,k:]);Q=G[k:,:k];checks=[];rng=np.random.default_rng(71)
for _ in range(3):
 v=rng.normal(size=k);z=lu.solve(-Q@v);full=np.r_[v,z];current=(G@full)[:k];err=float(np.max(abs(current-H@v)))/max(float(np.max(abs(current))),1e-30);energy=abs(float(full@(G@full)-v@(H@v)))/max(abs(float(full@(G@full))),1e-30);assert err<1e-6 and energy<1e-6,(err,energy);checks.append({'relative_current_error':err,'relative_energy_error':energy})
for mode in ['nominal','remote']:
 caps=[s for s in (B/f'{mode}.spice').read_text().splitlines() if s.startswith('C')]
 net=['* Sparse exact resistor-only reduction; maximum eliminated degree 12',header,*devices]+[f'RSP{i} {a} {b} {1/g:.15g}' for i,(a,b,g) in enumerate(newedges)]+caps+['.ends coupon'];(B/f'sparse-{mode}.spice').write_text('\n'.join(net)+'\n')
(B/'sparse-reduction.json').write_text(json.dumps({'original_resistors':len(edges),'reduced_resistors':len(newedges),'eliminated_nodes':eliminated,'retained_nodes':len(retained),'max_eliminated_degree':12,'checks':checks,'method':'Exact star-mesh elimination, no resistor pruning. Extra internal nodes retained to avoid dense Schur output.'},indent=2)+'\n');print('Sparse reduction verified',flush=True)
