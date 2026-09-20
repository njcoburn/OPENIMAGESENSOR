"""Eliminate resistor-only nodes by Schur complement, keeping both capacitor placements."""
from pathlib import Path
from collections import defaultdict
import json,re,heapq,hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced';B.mkdir(exist_ok=True)
class Union:
 def __init__(self):self.p={}
 def find(self,x):
  self.p.setdefault(x,x);a=x
  while self.p[a]!=a:a=self.p[a]
  while self.p[x]!=x:y=self.p[x];self.p[x]=a;x=y
  return a
 def join(self,a,b):self.p[self.find(a)]=self.find(b)
summary={}
for case in ['fill10-full','fill10-metal','corner-full','corner-metal']:
 src=R/'build/charge-reference'/case;meta=json.loads((src/'audit.json').read_text());lines=(src/'reference.spice').read_text().splitlines();header=next(s for s in lines if s.startswith('.subckt'));ports=header.split()[2:];res=[];devices=[];caps=[];u=Union();keep=set(ports)
 for s in lines:
  t=s.split()
  if not t:continue
  if t[0].startswith('R'):res.append((t[1],t[2],float(t[3])));u.join(t[1],t[2])
  elif t[0].startswith(('X','D')):
   devices.append(s);i=next(i for i,x in enumerate(t[1:],1) if x.startswith(('nfet_','pfet_','cap_nmos_','ppolyf_','diode_')));keep.update(t[1:i])
  elif t[0].startswith('C'):caps.append(t);keep.update(t[1:3])
 coords={}
 for s in (R/meta['source']/'coupon.res.ext').read_text().splitlines():
  if s.startswith('rnode '):t=s.split();coords[t[1].strip('"')]=(int(t[4]),int(t[5]))
 members=defaultdict(list)
 for n in list(u.p):members[u.find(n)].append(n)
 move={};placements={}
 for entry in meta['mapping'].values():
  a=entry['anchor'];options=[n for n in members.get(u.find(a),[]) if n in coords]
  if a in coords and options:
   x,y=coords[a];b=max(options,key=lambda n:((coords[n][0]-x)**2+(coords[n][1]-y)**2,n));distance=float(np.hypot(coords[b][0]-x,coords[b][1]-y))
  else:b=a;distance=0
  move[a]=b;placements[a]={'alternative':b,'distance_layout_units':distance};keep.add(b)
 altcaps=[[t[0],move.get(t[1],t[1]),move.get(t[2],t[2]),*t[3:]] for t in caps]
 for a,b in move.items():assert u.find(a)==u.find(b)
 groups=defaultdict(list)
 for a,b,r in res:groups[u.find(a)].append((a,b,r))
 output=[];checks=[];removed=0;kept_count=0
 for gid,edges in groups.items():
  nodes=sorted({n for a,b,r in edges for n in [a,b]});p=sorted(set(nodes)&keep);q=sorted(set(nodes)-keep)
  if not p:removed+=len(nodes);continue
  ordered=p+q;idx={n:i for i,n in enumerate(ordered)};k=len(p);rr=[];cc=[];vv=[]
  for a,b,r in edges:
   i,j=idx[a],idx[b];g=1/r;rr.extend([i,j,i,j]);cc.extend([i,j,j,i]);vv.extend([g,g,-g,-g])
  G=coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc();P=G[:k,:k].toarray();Q=G[k:,:k]
  if q:
   lu=splu(G[k:,k:]);S=P.copy()
   for start in range(0,k,8):
    sol=lu.solve(Q[:,start:start+8].toarray());S[:,start:start+8]-=Q.T@sol
  else:S=P.copy();lu=None
  asym=float(np.max(abs(S-S.T)));scale=max(float(np.max(abs(S))),1e-30);assert asym/scale<1e-8,(case,asym,scale)
  S=(S+S.T)*.5;off=S.copy();np.fill_diagonal(off,0);positive=float(max(0,np.max(off)));assert positive/scale<1e-8
  H=np.zeros_like(S)
  for i in range(k):
   for j in range(i+1,k):
    g=-S[i,j]
    if g<=0:continue
    output.append((p[i],p[j],1/g));H[i,i]+=g;H[j,j]+=g;H[i,j]-=g;H[j,i]-=g
  reconstruction=float(np.max(abs(H-S)))/scale;assert reconstruction<1e-7,(case,reconstruction)
  rng=np.random.default_rng(33);max_current=0;max_energy=0
  for _ in range(3):
   v=rng.normal(size=k);z=lu.solve(-Q@v) if q else np.empty(0);allv=np.r_[v,z];curr=(G@allv)[:k];reduced=H@v
   err=float(np.max(abs(curr-reduced)))/max(float(np.max(abs(curr))),1e-20);energy=float(abs(allv@(G@allv)-v@(H@v)))/max(abs(float(allv@(G@allv))),1e-20)
   assert err<1e-6 and energy<1e-6,(case,err,energy);max_current=max(max_current,err);max_energy=max(max_energy,energy)
  checks.append({'retained':k,'eliminated':len(q),'resistors_before':len(edges),'max_relative_current_error':max_current,'max_relative_energy_error':max_energy,'relative_matrix_reconstruction_error':reconstruction,'positive_offdiag_roundoff_S':positive});removed+=len(q);kept_count+=k
  print(case,'component',k,'retained',len(q),'eliminated',flush=True)
 d=B/case;d.mkdir(exist_ok=True)
 for mode,cs in [('nominal',caps),('remote',altcaps)]:
  net=['* Reference model: exact resistor-only reduction; lumped C placement assumption',header,*devices]+[f'RRED{i} {a} {b} {r:.15g}' for i,(a,b,r) in enumerate(output)]+[' '.join(t) for t in cs]+['.ends coupon']
  (d/f'{mode}.spice').write_text('\n'.join(net)+'\n')
 report={'source_sha256':hashlib.sha256((src/'reference.spice').read_bytes()).hexdigest(),'original_resistors':len(res),'reduced_resistors':len(output),'eliminated_nodes':removed,'retained_resistor_nodes':kept_count,'devices':len(devices),'capacitors':len(caps),'component_checks':checks,'placements':placements,'scope':'Remote anchor is a geometric sensitivity probe, not a proven worst-case bound. All device/port/capacitor nodes for both placements are retained.'}
 (d/'reduction.json').write_text(json.dumps(report,indent=2)+'\n');summary[case]=report
 print(case,len(res),'to',len(output),'resistors',flush=True)
(B/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
