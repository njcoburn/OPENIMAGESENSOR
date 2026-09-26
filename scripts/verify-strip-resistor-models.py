"""Read back and independently audit the serialized equivalent resistor models."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu

p=argparse.ArgumentParser();p.add_argument('directory');args=p.parse_args()
def records(path):
    return [line for line in path.read_text().splitlines() if line and line[0] in 'RCDX']
def edges(lines):
    return [(x[1],x[2],1/float(x[3])) for line in lines if line.startswith('R') for x in [line.split()]]
def matrix(es,nodes):
    ix={n:i for i,n in enumerate(nodes)};rr=[];cc=[];vv=[]
    for x,y,g in es:
        i,j=ix[x],ix[y];rr.extend([i,j,i,j]);cc.extend([i,j,j,i]);vv.extend([g,g,-g,-g])
    return coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc()
for d in sorted(Path(args.directory).glob('r*c*')):
    original=records(d/'rc-port.spice');old=edges(original);allnodes={n for x,y,g in old for n in [x,y]};report={}
    for name in ['rc-compact','rc-reduced']:
        path=d/(name+'.spice');newrecords=records(path);new=edges(newrecords)
        assert [s for s in original if not s.startswith('R')]==[s for s in newrecords if not s.startswith('R')]
        kept=sorted({n for x,y,g in new for n in [x,y]});removed=sorted(allnodes-set(kept))
        L=matrix(old,kept+removed);k=len(kept);V=np.random.default_rng(640064).normal(size=(k,12))
        expected=L[:k,:k]@V-L[:k,k:]@splu(L[k:,k:]).solve(L[k:,:k]@V)
        observed=matrix(new,kept)@V
        error=float(np.max(np.max(np.abs(expected-observed),axis=1)/np.maximum(np.max(np.abs(expected),axis=1),1e-15)))
        assert error<1e-9,(d,name,error)
        report[name]={'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'per_node_relative_current_error':error,'device_and_capacitor_records_identical':True,'boundary_probes':12}
    (d/'serialized-rc-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(d.name,json.dumps(report),flush=True)
