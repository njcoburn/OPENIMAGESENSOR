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
for variant in ['integrated-pex']:
 path=root/'build'/variant;source=path/'sensor_rc.spice';text=re.sub(r'\n\+\s*',' ',source.read_text());lines=[x.split() for x in text.splitlines() if x and x[0] not in '*+']
 ports=next(t[2:] for t in lines if t[0]=='.subckt');devices=[t for t in lines if t[0][0] in 'XD'];resistors=[t for t in lines if t[0][0]=='R'];caps=[(t[1],t[2],value(t[3])*1e15) for t in lines if t[0][0]=='C']
 assert sum(t[0][0]=='X' for t in devices)==37 and sum(t[0][0]=='D' for t in devices)==9
 uf=Union()
 for t in resistors:uf.join(t[1],t[2]);assert value(t[3])>0
 assert len({uf.find(p) for p in ports})==19
 mos=[t for t in devices if t[0][0]=='X'];diodes=[t for t in devices if t[0][0]=='D'];roles={};physical={}
 for d in diodes:
  props=dict(x.split('=') for x in d[4:]);assert abs(value(props['area'])-400e-12)<1e-22 and abs(value(props['pj'])-80e-6)<1e-15
  sense=uf.find(d[2]);rst=next(t for t in mos if sense in (uf.find(t[1]),uf.find(t[3])) and uf.find('VRESET') in (uf.find(t[1]),uf.find(t[3])))
  row=next(r for r in range(3) if uf.find(rst[2])==uf.find(f'RST{r}'))
  sf=next(t for t in mos if uf.find(t[2])==sense and uf.find(t[1])==uf.find('VDD'))
  sel=next(t for t in mos if uf.find(t[2])==uf.find(f'ROW{row}') and uf.find(sf[3]) in (uf.find(t[1]),uf.find(t[3])))
  col=next(c for c in range(3) if uf.find(f'COL{c}') in (uf.find(sel[1]),uf.find(sel[3])))
  key=f'{row}{col}';assert key not in roles
  roles[key]={'sense':d[2],'anode':d[1],'sf':sf[3]};physical[key]={'diode':d[0],'reset':rst[0],'source_follower':sf[0],'select':sel[0]}
 assert len(roles)==9
 negative=[(a,b,c) for a,b,c in caps if c < -1e-9]
 # Magic can assign negative local shunts during distributed-R redistribution.
 # Conserve the signed net-to-global-GND sum; never clip individual values.
 # This approximates shunt placement only on the affected BIAS/OUT nets.
 correction={}
 for net in ['BIAS','OUT']:
  shunts=[t for t in caps if (uf.find(t[0])==uf.find(net) and t[1]=='GND') or (uf.find(t[1])==uf.find(net) and t[0]=='GND')]
  bad=[t for t in shunts if t[2]<-1e-9]
  if not bad:continue
  total=sum(t[2] for t in shunts);assert total>0
  correction[net]={'negative_shunts_fF':bad,'signed_sum_fF':total,'placement':'net port'}
  selected=set(shunts);caps=[t for t in caps if t not in selected]+[(net,'GND',total)]
 assert not [(a,b,c) for a,b,c in caps if c < -1e-9],negative
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
 output=['* RC from verified GDS; capacitive-only nodes eliminated at zero net charge.','.subckt sensor_pex '+' '.join(ports)]
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
 output.append('.ends sensor_pex');(path/'sensor_reduced.spice').write_text('\n'.join(output)+'\n')
 lowr=output.copy()
 for i,line in enumerate(lowr):
  if line.startswith('R'):
   t=line.split();t[3]=f'{value(t[3])*.1:.12g}';lowr[i]=' '.join(t)
 (path/'sensor_lowr.spice').write_text('* Sensitivity: all extracted wire resistances scaled by 0.1; capacitance unchanged.\n'+'\n'.join(lowr)+'\n')
 # Sensitivity model: move each conserved shunt to the farthest R-network node.
 import heapq
 adjacency={}
 for t in resistors:
  a,b=t[1:3];r=value(t[3]);adjacency.setdefault(a,[]).append((b,r));adjacency.setdefault(b,[]).append((a,r))
 alternate=output.copy()
 for net,info in correction.items():
  distance={net:0};queue=[(0,net)]
  while queue:
   dist,node=heapq.heappop(queue)
   if dist!=distance[node]:continue
   for neighbor,r in adjacency.get(node,[]):
    nd=dist+r
    if nd<distance.get(neighbor,float('inf')):distance[neighbor]=nd;heapq.heappush(queue,(nd,neighbor))
  far=max(distance,key=distance.get);info['alternate_node']=names[far];info['resistive_distance_ohm']=distance[far]
  for i,line in enumerate(alternate):
   t=line.split()
   if t[0].startswith('C') and t[1:3]==[net,'GND']:
    remaining=value(t[3])*1e15-info['signed_sum_fF'];assert remaining>-1e-7
    alternate[i]=' '.join(t[:3])+f' {max(remaining,0):.12g}f';break
  else:raise AssertionError('Missing conserved shunt')
  alternate.insert(-1,f'Calternate_{net} {names[far]} GND {info["signed_sum_fF"]:.12g}f')
 (path/'sensor_alternate.spice').write_text('\n'.join(alternate)+'\n')
 # Collapse only the extracted resistors for an independent connectivity comparison.
 canon={uf.find(p):p for p in ports}
 for key,r in roles.items():canon[uf.find(r['sense'])]=f's{key}';canon[uf.find(r['sf'])]=f'f{key}'
 def collapsed(n):return canon[uf.find(n)]
 ref=['* Extracted devices with wiring resistors shorted and parasitic C omitted.','.subckt sensor_devices '+' '.join(ports)]
 for t in devices:
  x=t.copy()
  for i in range(1,5 if t[0][0]=='X' else 3):x[i]=collapsed(t[i])
  ref.append(' '.join(x))
 ref.append('.ends sensor_devices');(path/'sensor_devices.spice').write_text('\n'.join(ref)+'\n')
 # C-only comparison shorts the same resistance network while retaining reduced C.
 conly=['* Same extracted capacitance with ideal wires.','.subckt sensor_c '+' '.join(ports)]
 for line in output[2:-1]:
  t=line.split();kind=t[0][0]
  if kind=='R':continue
  x=t.copy();inverse={v:k for k,v in names.items()}
  for i in range(1,5 if kind=='X' else 3):x[i]=collapsed(inverse[t[i]])
  if kind=='C' and x[1]==x[2]:continue
  conly.append(' '.join(x))
 conly.append('.ends sensor_c');(path/'sensor_c.spice').write_text('\n'.join(conly)+'\n')
 report={'raw_netlist_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'resistors':len(resistors),'raw_capacitors':len(caps),'retained_nodes_including_ground':k+1,'eliminated_capacitive_nodes':len(floating),'output_capacitors':num,'max_schur_residual_fF':residual,'random_voltage_charge_error_fC':charge_error,'random_voltage_energy_error_fJ_times2':energy_error,'min_capacitance_eigenvalue_fF':eig,'max_capacitance_matrix_row_error_fF':truncation,'node_map':{key:{n:names[x] for n,x in role.items()} for key,role in roles.items()},'physical_devices':physical,'method':'Schur complement; floating fill at zero net charge. C below 1e-6 fF omitted with bounded row-sum error.'}
 report['shunt_placement_approximation']=correction
 report['raw_capacitors']=sum(t[0][0]=='C' for t in lines)
 (path/'reduction.json').write_text(json.dumps(report,indent=2)+'\n');np.save(path/'capacitance-matrix-fF.npy',reduced)
 print(variant,{x:report[x] for x in ('resistors','raw_capacitors','eliminated_capacitive_nodes','output_capacitors','max_capacitance_matrix_row_error_fF')},flush=True)
