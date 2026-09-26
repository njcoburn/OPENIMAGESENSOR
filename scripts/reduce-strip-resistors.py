"""Exact star-mesh elimination of internal, resistor-only extraction nodes.

All device terminals, capacitor terminals and ports are protected. No resistance
or capacitance threshold is applied. Audit original and reduced boundary currents
using independent sparse Dirichlet solves before writing the derived model.
"""
from pathlib import Path
import argparse, hashlib, heapq, json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu

p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--max-degree',type=int,default=4);p.add_argument('--model-name',default='rc-compact');a=p.parse_args()
for d in sorted(Path(a.directory).glob('r*c*')):
    source=d/'rc-port.spice';lines=source.read_text().splitlines()
    records=[line.split() for line in lines if line and line[0] in 'RCDX']
    ports=next(line.split()[2:] for line in lines if line.startswith('.subckt'))
    keep=set(ports)
    for x in records:
        if x[0][0] in 'CD':keep.update(x[1:3])
        if x[0][0]=='X':keep.update(x[1:5])
    graph={}
    def connect(x,y,g):
        if x==y:return
        graph.setdefault(x,{})[y]=graph.setdefault(x,{}).get(y,0.)+g
        graph.setdefault(y,{})[x]=graph.setdefault(y,{}).get(x,0.)+g
    original=[]
    for x in records:
        if x[0][0]=='R':
            g=1/float(x[3]);assert g>0
            connect(x[1],x[2],g);original.append((x[1],x[2],g))
    protected=sorted(set(graph)&keep);internal=sorted(set(graph)-keep)
    queue=[(len(graph[n]),n) for n in internal];heapq.heapify(queue)
    removed=[]
    while queue:
        degree,n=heapq.heappop(queue)
        if n not in graph or n in keep:continue
        if len(graph[n])!=degree:
            heapq.heappush(queue,(len(graph[n]),n));continue
        if a.max_degree and degree>a.max_degree:break
        neighbors=list(graph[n].items());total=sum(g for _,g in neighbors)
        assert total>0
        for i,(x,gx) in enumerate(neighbors):
            for y,gy in neighbors[i+1:]:connect(x,y,gx*gy/total)
        for x,_ in neighbors:
            del graph[x][n]
            if x not in keep:heapq.heappush(queue,(len(graph[x]),x))
        del graph[n];removed.append(n)
    assert keep.intersection(set(protected)).issubset(graph)
    protected=sorted(graph);internal=sorted(removed)
    reduced=[(x,y,g) for x,neighbors in graph.items() for y,g in neighbors.items() if x<y]
    def laplacian(edges,nodes):
        ix={n:i for i,n in enumerate(nodes)};rr=[];cc=[];vv=[]
        for x,y,g in edges:
            i,j=ix[x],ix[y];rr.extend([i,j,i,j]);cc.extend([i,j,j,i]);vv.extend([g,g,-g,-g])
        return coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc()
    L=laplacian(original,protected+internal);n=len(protected)
    A,B,D=L[:n,:n],L[:n,n:],L[n:,n:]
    V=np.random.default_rng(640064).normal(size=(n,12))
    expected=A@V-B@splu(D).solve(B.T@V) if internal else A@V
    observed=laplacian(reduced,protected)@V
    relative=float(np.max(np.abs(observed-expected))/np.max(np.abs(expected)))
    assert relative<1e-10,relative
    node_relative=float(np.max(np.max(np.abs(observed-expected),axis=1)/np.maximum(np.max(np.abs(expected),axis=1),1e-15)))
    assert node_relative<1e-9,node_relative
    output=[line for line in lines if not line.startswith('R') and not line.startswith('.ends')]
    output += [f'RK{i} {x} {y} {1/g:.17g}' for i,(x,y,g) in enumerate(sorted(reduced))]
    output += ['.ends array']
    target=d/(a.model_name+'.spice');assert not target.exists();target.write_text('\n'.join(output)+'\n')
    audit=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               model_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
               original_resistors=len(original),reduced_resistors=len(reduced),
               eliminated_resistor_only_nodes=len(removed),protected_nodes=len(protected),
               max_degree=a.max_degree,boundary_current_nodewise_relative_error=node_relative,boundary_current_relative_error=relative,random_boundary_probes=12,
               scope='Exact resistor-network star-mesh elimination in floating-point arithmetic. All capacitor/device terminals and ports retained; all capacitor and device records unchanged; no threshold reduction.')
    (d/(a.model_name+'-audit.json')).write_text(json.dumps(audit,indent=2)+'\n')
    (d/(a.model_name+'-runner.py')).write_bytes(Path(__file__).read_bytes())
    print(d.name,json.dumps(audit),flush=True)
