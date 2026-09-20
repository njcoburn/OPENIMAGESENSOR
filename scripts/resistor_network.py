"""Strict two-terminal resistor-network diagnostic; no production netlist edits."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import connected_components
def solve(edges):
 names=sorted(set(n for a,b,r in edges for n in [a,b]));assert 'VDD_A' in names and 'VDD_B' in names
 assert all(r>0 for a,b,r in edges)
 pairs=[tuple(sorted([a,b])) for a,b,r in edges];assert len(pairs)==len(set(pairs))
 ix={n:i for i,n in enumerate(names)};a=np.array([ix[a] for a,b,r in edges]);b=np.array([ix[b] for a,b,r in edges]);g=np.array([1/r for a,b,r in edges]);G=coo_matrix((np.r_[g,g,-g,-g],(np.r_[a,b,a,b],np.r_[a,b,b,a])),shape=(len(ix),len(ix))).tocsc()
 assert connected_components(G,directed=False)[0]==1
 keep=np.arange(len(ix))!=ix['VDD_B'];rhs=np.zeros(len(ix));rhs[ix['VDD_A']]=1
 v=np.zeros(len(ix));v[keep]=spsolve(G[keep][:,keep],rhs[keep]);assert max(abs((G@v-rhs)[keep]))<1e-8
 return float(v[ix['VDD_A']])
