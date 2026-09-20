"""Build a lumped-C/distributed-R reference preserving the original capacitance matrix.
This is an explicit placement approximation, not distributed-capacitance signoff.
"""
from pathlib import Path
from collections import defaultdict
import re,shlex,json,hashlib
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reference'
class Union:
 def __init__(self):self.p={}
 def find(self,x):
  self.p.setdefault(x,x)
  if self.p[x]!=x:self.p[x]=self.find(self.p[x])
  return self.p[x]
 def join(self,a,b):self.p[self.find(a)]=self.find(b)
cases=[(f'control-{c}',R/'build/capacitance-candidate/controls'/c/'area-fixed') for c in ['tee','tee-rotated','long-tee','long-tee-rotated']]+[(f'{c}-{m}',R/'build/ring-candidate/area-fixed'/c/m) for c in ['fill10','corner'] for m in ['full','metal']]
summary={}
for case,src in cases:
 d=B/case;d.mkdir(parents=True,exist_ok=True);nodes={};caps=[];eu=Union();ru=Union();coords={};sub=None
 for line in (src/'coupon.ext').read_text().splitlines():
  if not line.startswith(('node ','substrate ','equiv ','cap ','scale ')):continue
  t=shlex.split(line)
  if t[0]=='scale':assert float(t[2])==1,'Unsupported capacitance scale'
  elif t[0] in ['node','substrate']:
   nodes[t[1]]={'c':float(t[3])*.001,'xy':(int(t[4]),int(t[5]))}
   if t[0]=='substrate':sub=t[1]
  elif t[0]=='equiv':eu.join(t[1],t[2])
  elif t[0]=='cap':caps.append((t[1],t[2],float(t[3])*.001))
 assert sub
 for n,v in nodes.items():caps.append((n,sub,v['c']))
 original=defaultdict(float)
 for a,b,c in caps:
  assert c>=0,(case,a,b,c)
  a,b=eu.find(a),eu.find(b)
  if a!=b and c:original[tuple(sorted((a,b)))]+=c
 for line in (src/'coupon.res.ext').read_text().splitlines():
  if line.startswith('rnode '):
   t=line.split();coords[t[1].strip('"')]=(int(t[4]),int(t[5]))
 raw=(src/'rc.spice').read_text();rawlines=raw.splitlines();res=[s for s in rawlines if s.startswith('R')];devices=[s for s in rawlines if s.startswith(('X','D'))]
 rn=set()
 for line in res:
  t=line.split();assert float(t[3])>0;ru.join(t[1],t[2]);rn.update(t[1:3])
 groups=defaultdict(set)
 for n in rn:
  base=re.sub(r'\.[nt][0-9]+$','',n)
  if base not in nodes and base not in eu.p and base+'#' in nodes:base+='#'
  if base in nodes or base in eu.p:groups[eu.find(base)].add(n)
 # Every original net represented by R nodes must map to exactly one R component.
 comp_owner={}
 for net,members in groups.items():
  comp={ru.find(n) for n in members};assert len(comp)==1,(case,net,comp)
  key=next(iter(comp));assert key not in comp_owner or comp_owner[key]==net,(case,'unexpected original-net merge');comp_owner[key]=net
 mapping={};reasons={}
 for n in nodes:
  key=eu.find(n)
  if key in mapping:continue
  members=groups.get(key,set())
  if not members:mapping[key]=n;reasons[key]='no extracted resistor network'
  elif n in members:mapping[key]=n;reasons[key]='original named node retained in resistor network'
  else:
   x,y=nodes[n]['xy'];available=[q for q in members if q in coords];assert available
   chosen=min(available,key=lambda q:((coords[q][0]-x)**2+(coords[q][1]-y)**2,q))
   mapping[key]=chosen;reasons[key]='nearest recorded resistor-node coordinate to original node coordinate'
 newcaps=[]
 for (a,b),c in sorted(original.items()):newcaps.append((mapping[a],mapping[b],c))
 # Compare every pair coefficient after collapsing R, which proves full C-matrix equality.
 reverse={ru.find(n):net for net,n in mapping.items()};collapsed=defaultdict(float)
 for a,b,c in newcaps:
  aa,bb=reverse[ru.find(a)],reverse[ru.find(b)]
  if aa!=bb:collapsed[tuple(sorted((aa,bb)))]+=c
 assert set(collapsed)==set(original)
 error=max([abs(collapsed[p]-original[p]) for p in original] or [0]);assert error<1e-9
 header=next(s for s in rawlines if s.startswith('.subckt'))
 netlist=['* Charge-conserving reference: original lumped capacitance; distributed R unchanged',header,*devices,*res]
 netlist += [f'CREF{i} {a} {b} {c:.15g}f' for i,(a,b,c) in enumerate(newcaps)]
 netlist += ['.ends coupon'];(d/'reference.spice').write_text('\n'.join(netlist)+'\n')
 report={'source':str(src.relative_to(R)),'source_rc_sha256':hashlib.sha256((src/'rc.spice').read_bytes()).hexdigest(),'source_ext_sha256':hashlib.sha256((src/'coupon.ext').read_bytes()).hexdigest(),'resistors':len(res),'devices':len(devices),'capacitors':len(newcaps),'max_collapsed_pair_error_fF':error,'all_capacitors_nonnegative':True,'placement':'original lumped C attached to recorded R anchors; not a validated spatial C distribution','substrate':mapping[eu.find(sub)],'mapping':{k:{'anchor':v,'reason':reasons[k]} for k,v in mapping.items()}}
 (d/'audit.json').write_text(json.dumps(report,indent=2)+'\n');summary[case]={k:v for k,v in report.items() if k!='mapping'}
 print(case,len(res),'R',len(devices),'devices',len(newcaps),'C','matrix error',error,flush=True)
(B/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
