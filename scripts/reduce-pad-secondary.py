"""Eliminate floating fill at zero net charge; retain all terminal capacitance."""
from pathlib import Path
import re,json
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
root=Path(__file__).resolve().parents[1];dest=root/'build/pad-layout'
s=(dest/'secondary_c.spice').read_text();lines=[x.split(';')[0].split() for x in s.splitlines() if x and x[0] in 'CDX']
def val(x):
 m=re.fullmatch(r'([\d.eE+-]+)([a-z]*)',x);return float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6}[m[2]]
dev=[x for x in lines if x[0][0] in 'DX'];assert len(dev)==3
for d in dev:
 if d[0][0]=='D':
  p=dict(x.split('=') for x in d[4:]);assert abs(val(p['pj'])-26e-6)<1e-15 and abs(val(p['area'])-12e-12)<1e-20
caps=[(x[1],x[2],val(x[3])*1e15) for x in lines if x[0][0]=='C' and val(x[3])>0]
assert all(val(x[3])>=0 for x in lines if x[0][0]=='C')
ports=['PAD','CORE','VDD'];nodes=ports+sorted({n for a,b,c in caps for n in [a,b]}-set(ports)-{'VSS'});idx={n:i for i,n in enumerate(nodes)}
a=[];b=[];v=[]
for x,y,c in caps:
 for n in [x,y]:
  if n!='VSS':a.append(idx[n]);b.append(idx[n]);v.append(c)
 if x!='VSS' and y!='VSS':a.extend([idx[x],idx[y]]);b.extend([idx[y],idx[x]]);v.extend([-c,-c])
mat=sparse.coo_matrix((v,(a,b)),shape=(len(nodes),len(nodes))).tocsc();couple=mat[3:,:3].toarray()
eff=mat[:3,:3].toarray()-mat[:3,3:]@splu(mat[3:,3:]).solve(couple)
assert np.linalg.eigvalsh(eff).min()>0
net=['* Extracted local protection: PDK resistor, diodes, Schur-reduced fill/wiring C. Metal wire R not included.','.subckt secondary_pex PAD CORE VDD VSS']+[' '.join(x) for x in dev];record={};j=0
for i,n in enumerate(ports):
 c=float(eff[i].sum());assert c>=-1e-9
 net.append(f'C{j} {n} VSS {max(c,0):.12g}f');record[n+'-VSS']=c;j+=1
 for h in range(i+1,3):
  c=float(-eff[i,h]);assert c>=-1e-9
  net.append(f'C{j} {n} {ports[h]} {max(c,0):.12g}f');record[n+'-'+ports[h]]=c;j+=1
net+=['.ends secondary_pex'];(dest/'secondary_pex.spice').write_text('\n'.join(net)+'\n')
(dest/'secondary-capacitance.json').write_text(json.dumps({'capacitance_fF':record,'raw_capacitors':sum(x[0][0]=='C' for x in lines),'eliminated_floating_nodes':len(nodes)-3,'scope':'Zero-net-charge floating-fill elimination; lumped terminal capacitances. Metal wiring resistance not included.'},indent=2)+'\n')
print(record)
