from pathlib import Path
import numpy as np,json
from scipy.linalg import cho_factor,cho_solve
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced/corner-full';edges=[];adj={}
for s in (B/'nominal.spice').read_text().splitlines():
 if s.startswith('R'):
  t=s.split();a,b=t[1:3];g=1/float(t[3]);edges.append((a,b,g));adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
seen=set();out=[]
for n in adj:
 if n in seen:continue
 stack=[n];nodes=[];seen.add(n)
 while stack:
  a=stack.pop();nodes.append(a)
  for b in adj[a]-seen:seen.add(b);stack.append(b)
 ns=sorted(nodes);idx={n:i for i,n in enumerate(ns)};es=[e for e in edges if e[0] in idx];G=np.zeros((len(ns),len(ns)))
 for a,b,g in es:
  i,j=idx[a],idx[b];G[i,i]+=g;G[j,j]+=g;G[i,j]-=g;G[j,i]-=g
 inv=np.zeros_like(G);inv[:-1,:-1]=cho_solve(cho_factor(G[:-1,:-1]),np.eye(len(ns)-1));scores=[]
 for a,b,g in es:
  i,j=idx[a],idx[b];score=g*(inv[i,i]+inv[j,j]-2*inv[i,j]);assert score>=0;scores.append(score)
 cs=np.cumsum(sorted(scores));out.append({'nodes':len(ns),'edges':len(es),'removable_edges_by_energy_bound':{str(e):int(np.searchsorted(cs,e,side='right')) for e in [1e-6,1e-4,.001,.01]}})
(B/'sparsity-inspection.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
