"""Small GF180 MOS-cap tests and an extracted single-clamp isolation fixture."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import argparse, subprocess, os, json, re, hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
R=Path(__file__).resolve().parents[1];B=R/'build/moscap-branch';B.mkdir(exist_ok=True)
P=R/'build/charge-reduced/corner-full'
header='\n'.join((P/'practical-nominal/test.spice').read_text().splitlines()[1:6])+'\n'
env={**os.environ,'SPICE_USERINIT_DIR':str(R/'checkpoints/pad-closure/ngspice-init')}

def simulate(name,body,vectors='v(gate) i(Vsrc)',step='100n',stop='153u',extra_options=''):
 d=B/name;d.mkdir(exist_ok=True)
 deck='MOS-capacitor isolated diagnostic\n'+header+'.temp 27\n.options gmin=1e-17 reltol=1e-6 abstol=1e-12 chgtol=1e-16 trtol=3 method=gear\n'+extra_options+'\n'+body+f'\n.control\nset klu\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\ntran {step} {stop} 0 {step} uic\nwrdata tran.dat {vectors}\nquit\n.endc\n.end\n'
 (d/'test.spice').write_text(deck);row={'case':name,'completed':False}
 try:
  with (d/'ngspice.log').open('w') as f:p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=180)
  log=(d/'ngspice.log').read_text();errors=[l for l in log.splitlines() if re.search('aborted|timestep too small|^Error',l,re.I)]
  if (d/'tran.dat').exists():
   a=np.loadtxt(d/'tran.dat',skiprows=1,ndmin=2);row.update(points=len(a),last_time_s=float(a[-1,0]))
  assert p.returncode==0 and not errors,errors[-3:]
  assert len(a)>1 and np.isfinite(a).all() and a[-1,0]>=float(stop[:-1])*1e-6*.9999
  row['completed']=True
 except Exception as e:row['error']=str(e)
 print(row,flush=True);return row

def ramp(smooth):
 return ('Vsrc shape drive 0\nBdrive shape 0 V=3.3*(time<100u ? (0.5-0.5*cos(3.141592653589793*time/100u)) : 1)' if smooth else 'Vsrc drive 0 PWL(0 0 100u 3.3)')

def small(case):
 count,res,adapter,smooth=case;body=ramp(smooth)+f'\nRdrive drive gate {res}\n'
 for i in range(count):
  if adapter:body+=f'Ecap{i} out{i} 0 gate 0 1\nVsense{i} out{i} c{i} 0\nFcap{i} gate 0 Vsense{i} 1\n'
  body+=f'X{i} {"c"+str(i) if adapter else "gate"} 0 cap_nmos_06v0 c_width=25u c_length=10u\n'
 return simulate(f'small-n{count}-r{res}-{adapter}-{smooth}',body)

class Union:
 def __init__(self):self.p={}
 def find(self,a):
  self.p.setdefault(a,a)
  if self.p[a]!=a:self.p[a]=self.find(self.p[a])
  return self.p[a]
 def join(self,a,b):self.p[self.find(a)]=self.find(b)

def isolate():
 lines=(P/'nominal.spice').read_text().splitlines();ports=next(l.split()[2:] for l in lines if l.startswith('.subckt'));u=Union();res=[];devices=[];caps=[]
 for l in lines:
  t=l.split()
  if not t:continue
  if t[0].startswith('R'):res.append((t[1],t[2],float(t[3])));u.join(t[1],t[2])
  elif t[0].startswith('X'):
   end=next(i for i,x in enumerate(t) if x.startswith(('nfet_','pfet_','cap_nmos_','ppolyf_','diode_')))
   devices.append((l,t[1:end]))
  elif t[0].startswith('C'):caps.append(l)
 rails={u.find(p) for p in ports}|{u.find('0')}
 target=next(ns for l,ns in devices if l.startswith('X354 '));signals={u.find(n) for n in target}-rails
 chosen=set()
 while True:
  prev=len(chosen)
  for l,ns in devices:
   nets={u.find(n) for n in ns}-rails
   if nets&signals:chosen.add(l);signals.update(nets)
  if len(chosen)==prev:break
 selected=[l for l,ns in devices if l in chosen]
 keep=set(ports)
 for l,ns in devices:
  if l in chosen:keep.update(ns)
 for l in caps:keep.update(l.split()[1:3])
 groups=defaultdict(list)
 for a,b,r in res:groups[u.find(a)].append((a,b,r))
 out=[];checks=[]
 for edges in groups.values():
  nodes={n for a,b,r in edges for n in [a,b]};p=sorted(nodes&keep);q=sorted(nodes-keep)
  if not p:continue
  if len(p)==1:
   checks.append(dict(terminals=1,eliminated=len(q),current_error=0,reason='One-terminal resistor-only component has identically zero port admittance'));continue
  idx={n:i for i,n in enumerate(p+q)};k=len(p);rr=[];cc=[];vv=[]
  for a,b,r in edges:
   i,j=idx[a],idx[b];g=1/r;rr.extend([i,j,i,j]);cc.extend([i,j,j,i]);vv.extend([g,g,-g,-g])
  G=coo_matrix((vv,(rr,cc)),shape=(len(idx),len(idx))).tocsc();S=G[:k,:k].toarray();Q=G[k:,:k];lu=splu(G[k:,k:]) if q else None
  if q:S-=Q.T@lu.solve(Q.toarray())
  S=(S+S.T)*.5;H=np.zeros_like(S)
  for i in range(k):
   for j in range(i+1,k):
    g=-S[i,j]
    if g>0:out.append(f'Riso{len(out)} {p[i]} {p[j]} {1/g:.15g}');H[i,i]+=g;H[j,j]+=g;H[i,j]-=g;H[j,i]-=g
  error=0
  for seed in [31,32,33]:
   v=np.random.default_rng(seed).normal(size=k);z=lu.solve(-Q@v) if q else np.empty(0);current=(G@np.r_[v,z])[:k]
   error=max(error,float(np.max(abs(current-H@v)))/max(float(np.max(abs(current))),1e-20))
  assert error<1e-6,(k,len(q),error);checks.append(dict(terminals=k,eliminated=len(q),current_error=error))
 model='\n'.join(selected+out+caps)+'\n';(B/'isolated.spice').write_text(model)
 meta=dict(selected_devices=selected,removed_device_count=len(devices)-len(selected),resistors=len(out),wiring_caps=len(caps),checks=checks,source_sha256=hashlib.sha256((P/'nominal.spice').read_bytes()).hexdigest(),scope='Single signal-connected clamp device group; other semiconductor groups omitted. Entire rail wiring R/C retained or resistor-only reduced. Diagnostic, not a full-corner equivalent.')
 (B/'isolation.json').write_text(json.dumps(meta,indent=2)+'\n');print('Isolated',len(selected),'devices',len(out),'resistors',flush=True)
 return model,ports

def clamp(case):
 model,ports,adapter,smooth=case
 if adapter:
  updated=[]
  for l in model.splitlines():
   t=l.split()
   if l.startswith('X') and 'cap_nmos_06v0' in t:
    tag=t[0];g,b=t[1:3];t[1]='cap_'+tag
    updated.extend([f'E{tag} drv_{tag} {b} {g} {b} 1',f'V{tag} drv_{tag} cap_{tag} 0',f'F{tag} {g} {b} V{tag} 1',' '.join(t)])
   else:updated.append(l)
  model='\n'.join(updated)
 body=model+'\n'+ramp(smooth)+'\nRsource drive feed 2\n'
 for i,(port,ext) in enumerate(zip(ports,'feed vb 0 gb feed db 0 dg'.split())):body+=f'Vport{i} {ext} {port} 0\n'
 body+='Rstandby1 vb gb 100k\nRstandby2 db dg 100k\nIload1 vb gb PULSE(0 1m 151u 1n 1n 1u 10u)\nIload2 db dg PULSE(0 1m 151u 1n 1n 1u 10u)\n'
 return simulate(f'clamp-local{adapter}-smooth{smooth}',body,'v(vb,gb) v(db,dg) v(a_56346_55631#,DVSS_B.t335) i(Vport0)')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--small-only',action='store_true');args=parser.parse_args()
 cases=[(n,r,a,s) for n in [1,8] for r in [1,1000,1000000] for a in [False,True] for s in [False,True]]
 with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(small,cases))
 (B/'small.json').write_text(json.dumps(rows,indent=2)+'\n')
 if not args.small_only:
  model,ports=isolate()
  with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(clamp,[(model,ports,a,s) for a in [False,True] for s in [False,True]]))
  (B/'clamp.json').write_text(json.dumps(rows,indent=2)+'\n')
