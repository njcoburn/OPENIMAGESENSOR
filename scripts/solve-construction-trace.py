"""Solve raw diagnostic graphs, retaining parallel edges and contracting exact zero edges."""
from pathlib import Path
import json,shlex
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/network-investigation'
result={}
for d in sorted(base.glob('*-normal'))+sorted(base.glob('*-unreduced'))+sorted(base.glob('*-fixed')):
 if not d.is_dir():continue
 edges=[(t[1],t[2],float(t[3])) for s in (d/'rail.res.ext').read_text().splitlines() if s.startswith('resist ') for t in [shlex.split(s)]]
 names=sorted(set(n for a,b,r in edges for n in [a,b]));parent={n:n for n in names}
 def root(n):
  while parent[n]!=n:parent[n]=parent[parent[n]];n=parent[n]
  return n
 for a,b,r in edges:
  assert r>=0
  if r==0:parent[root(a)]=root(b)
 reduced=[(root(a),root(b),r) for a,b,r in edges if r>0 and root(a)!=root(b)]
 names=sorted(set(n for a,b,r in reduced for n in [a,b]));ix={n:i for i,n in enumerate(names)}
 a=np.array([ix[a] for a,b,r in reduced]);b=np.array([ix[b] for a,b,r in reduced]);g=np.array([1/r for a,b,r in reduced]);G=coo_matrix((np.r_[g,g,-g,-g],(np.r_[a,b,a,b],np.r_[a,b,b,a])),shape=(len(ix),len(ix))).tocsc()
 assert connected_components(G,directed=False)[0]==1
 keep=np.arange(len(ix))!=ix[root('VDD_B')];rhs=np.zeros(len(ix));rhs[ix[root('VDD_A')]]=1
 v=np.zeros(len(ix));v[keep]=spsolve(G[keep][:,keep],rhs[keep]);assert max(abs((G@v-rhs)[keep]))<1e-8
 result[d.name]={'resistors':len(edges),'zero_resistors':sum(r==0 for a,b,r in edges),'R_ohm':float(v[ix[root('VDD_A')]])}
(base/'construction-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
