"""Audit an exported full-ring RC model and measure its two rail paths."""
from pathlib import Path
import argparse,json,re
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('directory',nargs='?',default='build/power-ring/pex-unsimplified');args=p.parse_args();folder=ROOT/args.directory
text=re.sub(r'\n\+\s*',' ',(folder/'ring_rc.spice').read_text())
lines=[s.split() for s in text.splitlines() if s and s[0] not in '*;']
ports=next(t[2:] for t in lines if t[0].lower()=='.subckt')
assert set(ports)=={'AVDD_BOND','AVSS_BOND','AVDD','AVSS'},ports
class Union:
 def __init__(self):self.p={}
 def find(self,x):
  if x not in self.p:self.p[x]=x
  if self.p[x]!=x:self.p[x]=self.find(self.p[x])
  return self.p[x]
 def join(self,a,b):self.p[self.find(a)]=self.find(b)
def value(x):
 m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([a-z]*)',x,re.I);assert m,x
 return float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3}[m[2].lower()]
uf=Union();res=[t for t in lines if t[0][0]=='R'];caps=[t for t in lines if t[0][0]=='C']
assert res,'No distributed resistors exported'
for t in res:
 assert value(t[3])>=0
 uf.join(t[1],t[2])
assert uf.find('AVDD')==uf.find('AVDD_BOND'),'VDD bond/core terminals not connected by extracted R'
assert uf.find('AVSS')==uf.find('AVSS_BOND'),'VSS bond/core terminals not connected by extracted R'
assert uf.find('AVDD')!=uf.find('AVSS'),'Extracted rail short'
measurements={}
for port,bond in [('AVDD','AVDD_BOND'),('AVSS','AVSS_BOND')]:
 edges=[(t[1],t[2],value(t[3])) for t in res if uf.find(t[1])==uf.find(port)]
 assert all(r>0 for a,b,r in edges),'Zero-ohm edges need explicit reduction'
 nodes=sorted({n for a,b,r in edges for n in [a,b]}-{bond});idx={n:i for i,n in enumerate(nodes)}
 rr=[];cc=[];vv=[]
 for a,b,r in edges:
  for n in [a,b]:
   if n!=bond:rr.append(idx[n]);cc.append(idx[n]);vv.append(1/r)
  if a!=bond and b!=bond:rr += [idx[a],idx[b]];cc += [idx[b],idx[a]];vv += [-1/r,-1/r]
 g=coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc();current=np.zeros(len(nodes));current[idx[port]]=1
 voltage=spsolve(g,current);assert np.isfinite(voltage).all()
 residual=float(np.max(abs(g@voltage-current)));assert residual<1e-6,residual
 measurements[port]={'bond_to_core_R_ohm':float(voltage[idx[port]]),'network_nodes':len(nodes)+1,'network_resistors':len(edges),'max_KCL_residual_A_at_1A':residual}
# Functional LVS view: short ONLY extracted metal resistors, retain PDK resistors and all devices.
canonical={uf.find(n):n for n in reversed(ports)}
def name(n):return canonical.get(uf.find(n),uf.find(n))
output=['* Full extracted ring with metal R shorted for device LVS.','.subckt ring_flat '+' '.join(ports)]
for i,n in enumerate(ports):
 if name(n)!=n:output.append(f'Ralias{i} {n} {name(n)} 0')
for t in lines:
 if t[0][0] not in 'XD':continue
 model=next(i for i,x in enumerate(t[1:],1) if x.startswith(('nfet_','pfet_','cap_nmos_','ppolyf_','diode_')))
 output.append(' '.join([t[0]]+[name(x) for x in t[1:model]]+t[model:]))
output.append('.ends ring_flat');(folder/'ring_rc_short.spice').write_text('\n'.join(output)+'\n')
rail_cap=sum(value(t[3]) for t in caps if {uf.find(t[1]),uf.find(t[2])}=={uf.find('AVDD'),uf.find('AVSS')})
summary={'rail_paths':measurements,'raw_resistor_count':len(res),'raw_capacitor_count':len(caps),
 'negative_capacitor_count':sum(value(t[3])<0 for t in caps),'sum_direct_interrail_C_pF':rail_cap*1e12,
 'scope':'DC metal-path solution with semiconductor devices excluded from the resistor-only solve. Interrail C sum is not total bias-dependent ring capacitance. Device LVS must independently pass.'}
(folder/'rc-audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
