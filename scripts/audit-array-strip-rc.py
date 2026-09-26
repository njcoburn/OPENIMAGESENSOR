"""Audit strip R networks and explicitly repair negative reset shunt placement.
Signed capacitance per original net pair is conserved. Both placements are kept.
"""
from pathlib import Path
import argparse, hashlib, json, re, runpy
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
R=Path(__file__).resolve().parents[1]
Union=runpy.run_path(str(R/'scripts/prepare-array-strips.py'))['Union']
def val(s):
    m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([a-z]*)',s,re.I);return float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3}[m[2].lower()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();out=Path(a.directory).resolve()
for d in sorted(out.glob('r*c*')):
    meta=json.loads((d/'extraction.json').read_text());lines=(d/'rc.spice').read_text().splitlines();ts=[l.split() for l in lines if l and l[0] in 'RCDX'];res=[t for t in ts if t[0][0]=='R'];caps=[t for t in ts if t[0][0]=='C'];uf=Union()
    for t in res:uf.join(t[1],t[2])
    negatives=[t for t in caps if val(t[3])<0];corrections=[];removed=set();replacement={'port':[],'gate':[]}
    for r in range(meta['rows']):
        net=f'RST{r}';members=[t for t in caps if t[2]=='GND' and uf.find(t[1])==uf.find(net)]
        if not any(t in negatives for t in members):continue
        assert all(t[2]=='GND' for t in members)
        total=sum(val(t[3]) for t in members);assert total>0
        removed.update(t[0] for t in members)
        gate=meta['roles']['rc'][f'{r}_0']['reset_gate']
        replacement['port'].append(f'CFIX{r} {net} GND {total:.16g}')
        replacement['gate'].append(f'CFIX{r} {gate} GND {total:.16g}')
        corrections.append({'net':net,'original_shunts':members,'signed_total_F':total,'alternate_gate':gate})
    assert all(t[0] in removed for t in negatives),negatives
    def pairs(cs):
        result={}
        for t in cs:
            key=tuple(sorted([uf.find(t[1]),uf.find(t[2])]))
            if key[0]!=key[1]:result[key]=result.get(key,0)+val(t[3])
        return result
    original=pairs(caps)
    for placement in ['port','gate']:
        updated=[l for l in lines[:-1] if not l or l.split()[0] not in removed]+replacement[placement]+[lines[-1]]
        newcaps=[l.split() for l in updated if l.startswith('C')]
        assert all(val(t[3])>=0 for t in newcaps)
        after=pairs(newcaps);assert original.keys()==after.keys()
        error=max(abs(original[key]-after[key]) for key in original);assert error<1e-25,error
        target=d/f'rc-{placement}.spice';target.write_text('\n'.join(updated)+'\n')
    # Unit-current effective resistance from each port to each observed device terminal.
    metrics={}
    for net,role in [('VDD','vdd'),('GND','gnd'),('COL0','column')]+[(f'ROW{r}','select_gate') for r in range(meta['rows'])]+[(f'RST{r}','reset_gate') for r in range(meta['rows'])]:
        edges=[t for t in res if uf.find(t[1])==uf.find(net)]
        nodes=sorted({n for t in edges for n in t[1:3]}-{net});ix={n:i for i,n in enumerate(nodes)};rr=[];cc=[];vv=[]
        for t in edges:
            x,y=t[1:3];g=1/val(t[3])
            for n in [x,y]:
                if n!=net:rr.append(ix[n]);cc.append(ix[n]);vv.append(g)
            if x!=net and y!=net:rr.extend([ix[x],ix[y]]);cc.extend([ix[y],ix[x]]);vv.extend([-g,-g])
        lu=splu(coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc());values={}
        for key,v in meta['roles']['rc'].items():
            n=v[role]
            if uf.find(n)!=uf.find(net):continue
            b=np.zeros(len(nodes))
            if n==net:values[key]=0.;continue
            b[ix[n]]=1;values[key]=float(lu.solve(b)[ix[n]])
        metrics[net]={'effective_resistance_ohm':values,'max_ohm':max(values.values()),'total_incident_C_F':sum(v for pair,v in original.items() if uf.find(net) in pair)}
    report={'negative_capacitors':len(negatives),'corrections':corrections,'collapsed_capacitance_matrix_max_error_F':error,'net_metrics':metrics,'models_sha256':{f'rc-{x}.spice':sha(d/f'rc-{x}.spice') for x in ['port','gate']},'scope':'All extracted resistors/devices/coupling retained. Only signed reset-net shunts with negative local entries are lumped at reset port (main) or local reset gate (sensitivity). This conserves R-collapsed capacitance but approximates its placement; not signoff distributed capacitance.'}
    (d/'rc-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(d.name,'negative shunts',len(negatives),'max R', {k:round(v['max_ohm'],3) for k,v in metrics.items() if k in ['VDD','GND','COL0','ROW0','RST0']},flush=True)
