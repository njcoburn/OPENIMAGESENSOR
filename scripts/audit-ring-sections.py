"""Audit four-rail coupon RC, solve physical paths, and verify devices with metal R shorted."""
from pathlib import Path
import json,re,subprocess,hashlib,argparse
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/ring-sections';results={}
pdk=Path('/foss/pdks/gf180mcuD');library=pdk/'libs.ref/gf180mcu_fd_io/spice/gf180mcu_fd_io.spice'
class Union:
 def __init__(self):self.p={}
 def find(self,x):
  self.p.setdefault(x,x);a=x
  while self.p[a]!=a:a=self.p[a]
  while self.p[x]!=x:b=self.p[x];self.p[x]=a;x=b
  return a
 def join(self,a,b):self.p[self.find(a)]=self.find(b)
def value(s):
 m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([a-z]*)',s,re.I);assert m,s
 return float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'meg':1e6}[m[2].lower()]
parser=argparse.ArgumentParser();parser.add_argument('--cases',nargs='+',default=['fill10','fill20','corner','corner_fill']);parser.add_argument('--work-dir',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
if args.work_dir:base=args.work_dir.resolve()
for name in args.cases:
 meta=json.loads((base/name/'geometry.json').read_text());results[name]={}
 for mode in ['full','metal']:
  folder=base/name/mode;status=json.loads((folder/'status.json').read_text());assert status['status']=='exported_unvalidated',(name,mode,status)
  text=re.sub(r'\n\+\s*',' ',(folder/'rc.spice').read_text());lines=[s.split() for s in text.splitlines() if s and s[0] not in '*;']
  ports=next(t[2:] for t in lines if t[0].lower()=='.subckt');assert ports==[p['name'] for p in meta['ports']]
  uf=Union();res=[t for t in lines if t[0][0]=='R'];caps=[t for t in lines if t[0][0]=='C'];assert res
  for t in res:assert value(t[3])>0,('zero/nonpositive extracted R',name,mode,t);uf.join(t[1],t[2])
  rails=['VDD','VSS','DVDD','DVSS']
  groups={r:uf.find(r+'_A') for r in rails}
  shared_ground=groups['VSS']==groups['DVSS']
  assert groups['VDD']!=groups['DVDD'] and all(groups[r]!=groups[g] for r in ['VDD','DVDD'] for g in ['VSS','DVSS']),('power-to-ground short',name,mode)
  assert not shared_ground or (mode=='full' and name.startswith('corner')),('unexpected ground coupling',name,mode)
  measured={}
  for rail in rails:
   a,b=rail+'_A',rail+'_B';assert uf.find(a)==uf.find(b),(name,mode,rail,'open')
   edges=[(t[1],t[2],value(t[3])) for t in res if uf.find(t[1])==uf.find(a)]
   nodes=sorted({n for x,y,r in edges for n in [x,y]}-{b});idx={n:i for i,n in enumerate(nodes)};rr=[];cc=[];vv=[]
   for x,y,r in edges:
    for n in [x,y]:
     if n!=b:rr.append(idx[n]);cc.append(idx[n]);vv.append(1/r)
    if x!=b and y!=b:rr += [idx[x],idx[y]];cc += [idx[y],idx[x]];vv += [-1/r,-1/r]
   g=coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc();current=np.zeros(len(nodes));current[idx[a]]=1
   v=spsolve(g,current);assert np.isfinite(v).all();err=float(np.max(abs(g@v-current)));assert err<1e-6,(name,mode,rail,err)
   measured[rail]={'R_ohm':float(v[idx[a]]),'nodes':len(nodes)+1,'resistors':len(edges),'KCL_residual_A':err};assert v[idx[a]]>0
  # Collapse only the explicitly extracted R network; semiconductor and PDK poly devices remain.
  tied_domain=mode=='full' and name.startswith('corner')
  canon={uf.find(r+'_A'):('AVDD' if r in ['VDD','DVDD'] else 'AVSS') if tied_domain else r for r in rails}
  def node(n):return canon.get(uf.find(n),uf.find(n))
  header='.subckt coupon '+('AVDD AVSS' if tied_domain else 'VDD VSS DVDD DVSS')
  netlist=[header]
  for t in lines:
   if t[0][0] not in 'XD':continue
   model=next(i for i,x in enumerate(t[1:],1) if x.startswith(('nfet_','pfet_','cap_nmos_','ppolyf_','diode_')))
   netlist.append(' '.join([t[0]]+[node(x) for x in t[1:model]]+t[model:]))
  netlist.append('.ends coupon');(folder/'rc_short.spice').write_text('\n'.join(netlist)+'\n')
  verdict='not_applicable_conductor_only'
  if mode=='full':
   reference=[f'.include {library}',header]
   for i,(macro,x) in enumerate(meta['instances']):reference.append(f'X{i} '+('AVDD AVSS AVDD AVSS' if tied_domain else 'DVDD DVSS VDD VSS')+f' gf180mcu_fd_io__{macro}')
   reference.append('.ends coupon');(folder/'reference.spice').write_text('\n'.join(reference)+'\n')
   with (folder/'netgen.log').open('w') as log:subprocess.run(['netgen','-batch','lvs','rc_short.spice coupon','reference.spice coupon',str(pdk/'libs.tech/netgen/gf180mcuD_setup.tcl'),'lvs.log'],cwd=folder,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
   lvs=(folder/'lvs.log').read_text();verdict='unique_match' if 'Final result: Circuits match uniquely.' in lvs else 'failed';assert verdict=='unique_match',(name,lvs[-1500:])
  data={'rails':measured,'resistors':len(res),'capacitors':len(caps),'negative_capacitors':sum(value(t[3])<0 for t in caps),'device_LVS':verdict,'LVS_scope':'tied analog supply domain' if tied_domain else 'four separate macro ports','substrate_ground_connection':shared_ground,'extraction_s':status['elapsed_s'],'rc_sha256':hashlib.sha256((folder/'rc.spice').read_bytes()).hexdigest()}
  results[name][mode]=data;print(name,mode,{r:round(v['R_ohm'],7) for r,v in measured.items()},'LVS',verdict,flush=True)
  (folder/'audit.json').write_text(json.dumps(data,indent=2)+'\n')
summary={'cases':results,'scope':'Physical point-to-point terminal resistance in small macro coupons with added 0.4 um M5 measurement leads; resistance includes these leads; all other ports open for each resistor-only solve. This is not an equipotential-edge model, stitched ring, or validated capacitance/transient model.'}
(args.output or ROOT/'simulations/ring-sections.json').write_text(json.dumps(summary,indent=2)+'\n')
