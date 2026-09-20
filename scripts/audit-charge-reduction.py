"""Audit serialized reductions: device records, C-net pairs, and DC rail resistance."""
from pathlib import Path
from collections import defaultdict
import json,argparse
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced';prior=json.loads((R/'build/capacitance-candidate/dc-audit.json').read_text())['cases'];out={}
class U:
 def __init__(self):self.p={}
 def f(self,x):
  self.p.setdefault(x,x);a=x
  while self.p[a]!=a:a=self.p[a]
  while self.p[x]!=x:y=self.p[x];self.p[x]=a;x=y
  return a
 def j(self,a,b):self.p[self.f(a)]=self.f(b)
parser=argparse.ArgumentParser();parser.add_argument('--sparse-corner',action='store_true');args=parser.parse_args();prefix='sparse-' if args.sparse_corner else ''
for case in (['corner-full'] if args.sparse_corner else ['fill10-full','fill10-metal','corner-full','corner-metal']):
 original=(R/'build/charge-reference'/case/'reference.spice').read_text().splitlines();u=U();dev=[s for s in original if s.startswith(('X','D'))]
 for s in original:
  if s.startswith('R'):t=s.split();u.j(t[1],t[2])
 def capmat(lines):
  caps=defaultdict(float)
  for s in lines:
   if s.startswith('C'):
    t=s.split();assert t[3].endswith('f');v=float(t[3][:-1]);assert v>=0;a,b=u.f(t[1]),u.f(t[2])
    if a!=b:caps[tuple(sorted((a,b)))]+=v
  return caps
 expected=capmat(original);checks={}
 for mode in ['nominal','remote']:
  lines=(B/case/f'{prefix}{mode}.spice').read_text().splitlines();assert dev==[s for s in lines if s.startswith(('X','D'))]
  actual=capmat(lines);assert set(actual)==set(expected);err=max([abs(actual[p]-expected[p]) for p in expected] or [0]);assert err<1e-9
  checks[mode]={'unchanged_device_records':True,'max_collapsed_C_pair_error_fF':err}
 edges=[]
 for s in (B/case/f'{prefix}nominal.spice').read_text().splitlines():
  if s.startswith('R'):
   t=s.split();a,b=t[1:3];r=float(t[3]);assert r>0 and u.f(a)==u.f(b);edges.append((a,b,r))
 dc={};name,geom=case.split('-')
 for rail in ['VDD','VSS','DVDD','DVSS']:
  a,b=rail+'_A',rail+'_B';es=[e for e in edges if u.f(e[0])==u.f(a)];nodes=sorted({n for x,y,r in es for n in (x,y)}-{b});idx={n:i for i,n in enumerate(nodes)};rr=[];cc=[];vv=[]
  for x,y,r in es:
   for n in (x,y):
    if n!=b:rr.append(idx[n]);cc.append(idx[n]);vv.append(1/r)
   if x!=b and y!=b:rr.extend([idx[x],idx[y]]);cc.extend([idx[y],idx[x]]);vv.extend([-1/r,-1/r])
  G=coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc();i=np.zeros(len(nodes));i[idx[a]]=1;v=spsolve(G,i);measured=float(v[idx[a]]);ref=prior[name][geom]['rails'][rail]['R_ohm'];error=abs(measured/ref-1);assert np.isfinite(v).all() and error<1e-6,(case,rail,error)
  dc[rail]={'reduced_R_ohm':measured,'unreduced_R_ohm':ref,'relative_error':error}
 out[case]={'placements':checks,'dc':dc};print(case,'serialized capacitance/device checks and four DC rail comparisons pass',flush=True)
(B/('audit-sparse.json' if args.sparse_corner else 'audit.json')).write_text(json.dumps(out,indent=2)+'\n')
