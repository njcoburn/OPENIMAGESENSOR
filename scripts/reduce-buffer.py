"""Preserve RC/device terminals; eliminate charge-neutral capacitive-only fill.
Schur complement in femtofarads. No grounding of floating fill, no fitted devices.
"""
from pathlib import Path
import re,json,hashlib
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
root=Path(__file__).resolve().parents[1]
def value(s):
 m=re.fullmatch(r'([+-]?[\d.]+(?:[eE][+-]?\d+)?)([a-zA-Z]*)',s);assert m,s
 return float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3}[m[2].lower()]
class Union:
 def __init__(self):self.p={}
 def find(self,x):
  if x not in self.p:self.p[x]=x
  if self.p[x]!=x:self.p[x]=self.find(self.p[x])
  return self.p[x]
 def join(self,a,b):self.p[self.find(a)]=self.find(b)
for variant in ['buffer-pex']:
 path=root/'build'/variant;source=path/'buffer_rc.spice';text=source.read_text();lines=[x.split() for x in text.splitlines() if x and x[0] not in '*+']
 raw_capacitor_count=sum(t[0][0]=='C' for t in lines)
 ports=next(t[2:] for t in lines if t[0]=='.subckt');devices=[t for t in lines if t[0][0] in 'XD'];resistors=[t for t in lines if t[0][0]=='R'];caps=[(t[1],t[2],value(t[3])*1e15) for t in lines if t[0][0]=='C']
 assert sum(t[0][0]=='X' for t in devices)==3 and sum(t[0][0]=='D' for t in devices)==0
 uf=Union()
 for t in resistors:uf.join(t[1],t[2]);assert value(t[3])>0
 assert len({uf.find(p) for p in ports})==5
 negative=[(a,b,c) for a,b,c in caps if c < -1e-9]
 assert not negative,negative
 roles={};physical={}
 keep=set(ports)
 for t in resistors:keep.update(t[1:3])
 for t in devices:keep.update(t[1:5] if t[0][0]=='X' else t[1:3])
 keep.discard('GND');kn=sorted(keep);floating=sorted({n for a,b,c in caps for n in (a,b)}-keep-{'GND'});nodes=kn+floating;idx={n:i for i,n in enumerate(nodes)}
 rr=[];cc=[];vv=[]
 for a,b,c in caps:
  if a==b or c==0:continue
  for n in (a,b):
   if n!='GND':i=idx[n];rr.append(i);cc.append(i);vv.append(c)
  if a!='GND' and b!='GND':i,j=idx[a],idx[b];rr.extend([i,j]);cc.extend([j,i]);vv.extend([-c,-c])
 mat=sparse.coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc();k=len(kn);pp=mat[:k,:k].toarray();fp=mat[k:,:k];residual=0
 if floating:
  ff=mat[k:,k:];lu=splu(ff);solution=lu.solve(fp.toarray());reduced=pp-fp.T@solution
  residual=float(np.max(np.abs(ff@solution-fp.toarray())))
  assert residual<1e-7,residual
  rng=np.random.default_rng(42);v=rng.normal(size=k);vf=-solution@v;full=np.r_[v,vf]
  charge_error=float(np.max(np.abs((mat@full)[:k]-reduced@v)))
  energy_error=float(abs(full@(mat@full)-v@reduced@v));assert charge_error<1e-7 and energy_error<1e-6
 else:reduced=pp;charge_error=energy_error=0
 assert np.max(np.abs(reduced-reduced.T))<1e-7
 reduced=(reduced+reduced.T)/2
 eig=float(np.linalg.eigvalsh(reduced)[0]);assert eig>-1e-7,eig
 names={n:(n if n in ports else f'n{i}') for i,n in enumerate(kn)};names['GND']='GND'
 output=['* RC from verified GDS; capacitive-only nodes eliminated at zero net charge.','.subckt buffer_pex '+' '.join(ports)]
 for t in devices+resistors:
  x=t.copy();count=4 if t[0][0]=='X' else 2
  for i in range(1,count+1):x[i]=names[t[i]]
  output.append(' '.join(x))
 rebuilt=np.zeros_like(reduced);num=0;minimum=1e-6
 for i in range(k):
  for j in range(i+1,k):
   c=-reduced[i,j];assert c>-1e-7,(kn[i],kn[j],c)
   if c>minimum:
    output.append(f'Cpex{num} {names[kn[i]]} {names[kn[j]]} {c:.12g}f');num+=1
    rebuilt[i,i]+=c;rebuilt[j,j]+=c;rebuilt[i,j]-=c;rebuilt[j,i]-=c
  c=float(reduced[i].sum());assert c>-1e-7,(kn[i],c)
  if c>minimum:output.append(f'Cpex{num} {names[kn[i]]} GND {c:.12g}f');num+=1;rebuilt[i,i]+=c
 truncation=float(np.max(np.sum(np.abs(reduced-rebuilt),axis=1)));assert truncation<.001,truncation
 output.append('.ends buffer_pex');(path/'buffer_reduced.spice').write_text('\n'.join(output)+'\n')
 # Collapse only the extracted resistors for an independent connectivity comparison.
 canon={uf.find(p):p for p in ports}
 for key,r in roles.items():canon[uf.find(r['sense'])]=f's{key}';canon[uf.find(r['sf'])]=f'f{key}'
 def collapsed(n):return canon[uf.find(n)]
 ref=['* Extracted devices with wiring resistors shorted and parasitic C omitted.','.subckt buffer_devices '+' '.join(ports)]
 for t in devices:
  x=t.copy()
  for i in range(1,5 if t[0][0]=='X' else 3):x[i]=collapsed(t[i])
  ref.append(' '.join(x))
 ref.append('.ends buffer_devices');(path/'buffer_devices.spice').write_text('\n'.join(ref)+'\n')
 # C-only comparison shorts the same resistance network while retaining reduced C.
 conly=['* Same extracted capacitance with ideal wires.','.subckt buffer_c '+' '.join(ports)]
 for line in output[2:-1]:
  t=line.split();kind=t[0][0]
  if kind=='R':continue
  x=t.copy();inverse={v:k for k,v in names.items()}
  for i in range(1,5 if kind=='X' else 3):x[i]=collapsed(inverse[t[i]])
  if kind=='C' and x[1]==x[2]:continue
  conly.append(' '.join(x))
 conly.append('.ends buffer_c');(path/'buffer_c.spice').write_text('\n'.join(conly)+'\n')
 report={'raw_netlist_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'resistors':len(resistors),'raw_capacitors':raw_capacitor_count,'retained_nodes_including_ground':k+1,'eliminated_capacitive_nodes':len(floating),'output_capacitors':num,'max_schur_residual_fF':residual,'random_voltage_charge_error_fC':charge_error,'random_voltage_energy_error_fJ_times2':energy_error,'min_capacitance_eigenvalue_fF':eig,'max_capacitance_matrix_row_error_fF':truncation,'node_map':{key:{n:names[x] for n,x in role.items()} for key,role in roles.items()},'physical_devices':physical,'method':'Schur complement; floating fill at zero net charge. C below 1e-6 fF omitted with bounded row-sum error.'}
 (path/'reduction.json').write_text(json.dumps(report,indent=2)+'\n');np.save(path/'capacitance-matrix-fF.npy',reduced)
 print(variant,{x:report[x] for x in ('resistors','raw_capacitors','eliminated_capacitive_nodes','output_capacitors','max_capacitance_matrix_row_error_fF')},flush=True)
