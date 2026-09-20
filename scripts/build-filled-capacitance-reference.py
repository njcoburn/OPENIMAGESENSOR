"""Preserve the final flat .ext capacitance matrix and unchanged LVS devices.
No distributed R or spatial redistribution. Audit native-export rounding separately.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,re
R=Path(__file__).resolve().parents[1];B=R/'build/filled-electrical-baseline';ext=B/'routed_flat.ext';native=B/'filled_lumped.spice'
assert json.loads((B/'audit.json').read_text())['device_records_match']
class Union:
 def __init__(self):self.p={}
 def find(self,x):
  root=x
  while root in self.p and self.p[root]!=root:root=self.p[root]
  while x in self.p and self.p[x]!=x:parent=self.p[x];self.p[x]=root;x=parent
  return root
 def join(self,a,b):
  a,b=self.find(a),self.find(b)
  if a!=b:self.p[b]=a
u=Union();substrate=None;nodes={};preferred=set();body=[];header=''
for line in native.open():
 if line.startswith('C'):continue
 body.append(line)
 t=line.split()
 if not t:continue
 if t[0]=='.subckt':header=line;preferred.update(t[2:])
 elif t[0]=='+':header+=line;preferred.update(t[1:])
 elif t[0].startswith('X'):
  end=next(i for i,z in enumerate(t) if '=' in z)-1;preferred.update(t[1:end])
 elif t[0].startswith('D'):preferred.update(t[1:3])
nodepat=re.compile(r'^(node|substrate) "([^"\s]+)" (\S+) (\S+) ')
cap=re.compile(r'^cap "([^"\s]+)" "([^"\s]+)" (\S+)\s*$')
equiv=re.compile(r'^equiv "([^"\s]+)" "([^"\s]+)"\s*$')
for line in ext.open():
 if line.startswith('scale '):assert float(line.split()[2])==1
 elif line.startswith(('node ','substrate ')):
  m=nodepat.match(line);assert m,line[:100];nodes[m[2]]=float(m[4])*.001
  if m[1]=='substrate':assert substrate is None;substrate=m[2]
 elif line.startswith('equiv '):
  m=equiv.match(line);assert m,line[:100];u.join(m[1],m[2])
assert substrate=='GND'
canonical={}
for n in sorted(preferred):
 root=u.find(n);assert root not in canonical or canonical[root]==n,('multiple preferred aliases',n,canonical.get(root));canonical[root]=n
for n in sorted(nodes):canonical.setdefault(u.find(n),n)
def canon(n):return canonical.get(u.find(n),u.find(n))
expected=defaultdict(float);roundoff=[]
def add(a,b,c):
 if c<0:
  # fF units: tolerate only <1e-30 F negative residuals; never drop positive C.
  assert abs(c)<1e-15, ('material negative capacitance',a,b,c)
  roundoff.append((a,b,c));return
 a,b=canon(a),canon(b)
 if a!=b and c:expected[tuple(sorted((a,b)))]+=c
for n,c in nodes.items():add(n,substrate,c)
for line in ext.open():
 if line.startswith('cap '):
  m=cap.match(line);assert m,line[:100];add(m[1],m[2],float(m[3])*.001)
print('Parsed',len(nodes),'nodes;',len(expected),'positive capacitance pairs;',len(preferred),'device/port nodes',flush=True)
# Compare the native export at the same original-net coordinates, in fF.
remaining=dict(expected);zeros=0;native_count=0
units={'':1e15,'f':1,'p':1e3,'n':1e6,'u':1e9,'m':1e12}
num=re.compile(r'([+-]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][+-]?\d+)?)([A-Za-z]*)$')
for line in native.open():
 if not line.startswith('C'):continue
 t=line.split();m=num.fullmatch(t[3]);assert m,t[3];v=float(m[1])*units[m[2].lower()];zeros+=v==0;native_count+=1
 a,b=canon(t[1]),canon(t[2]);key=tuple(sorted((a,b)))
 if a!=b:remaining[key]=remaining.get(key,0)-v
maxpair=max(remaining,key=lambda k:abs(remaining[k]));maxerr=abs(remaining[maxpair]);sumerr=sum(abs(v) for v in remaining.values())
# Use the original matrix, rather than trying to repair individual exported values.
out=B/'filled_charge_reference.spice'
with out.open('w') as f:
 f.write('* Final-GDS lumped-C reference from original .ext matrix; no distributed wire R\n')
 for line in body:
  if not line.startswith(('*','.ends')):f.write(line)
 for i,((a,b),c) in enumerate(sorted(expected.items())):f.write(f'CREF{i} {a} {b} {c:.15g}f\n')
 f.write('.ends routed_flat\n')
# Re-read serialized values and endpoints, checking the full saved pair matrix.
seen=set();worst=0
for line in out.open():
 if not line.startswith('CREF'):continue
 t=line.split();key=tuple(sorted(t[1:3]));assert key in expected and key not in seen;seen.add(key);worst=max(worst,abs(float(t[3][:-1])-expected[key]))
assert len(seen)==len(expected) and worst<1e-8
r=dict(ext_sha256=hashlib.sha256(ext.read_bytes()).hexdigest(),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),reference_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),nodes=len(nodes),retained_device_port_nodes=len(preferred),capacitor_pairs=len(expected),native_capacitors=native_count,native_zero_capacitors=zeros,native_max_pair_error_fF=maxerr,native_max_error_pair=list(maxpair),native_sum_absolute_pair_error_fF=sumerr,serialized_reference_max_pair_error_fF=worst,original_matrix_preserved_to_numeric_bound=True,negative_roundoff_entries=len(roundoff),negative_roundoff_sum_abs_F=sum(abs(z[2]) for z in roundoff)*1e-15,capacitance_matrix_infinity_norm_perturbation_bound_F=2*sum(abs(z[2]) for z in roundoff)*1e-15,negative_roundoff_limit_per_entry_F=1e-30,substrate=substrate,scope='Lumped matrix of the final flat extraction, constant wiring C; device records retained; no distributed R or measured capacitance validation',accepted_full_chip_rc=False)
(B/'negative-roundoff.json').write_text(json.dumps(dict(units='fF',entries=roundoff),indent=2)+'\n')
(B/'capacitance-audit.json').write_text(json.dumps(r,indent=2)+'\n');(R/'simulations/filled-capacitance-reference.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
