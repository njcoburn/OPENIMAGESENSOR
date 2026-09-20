"""Eliminate only passive floating-fill nodes from the lumped-C baseline.
Schur complement at zero initial floating charge. No resistor/device removal and
no positive-capacitance threshold. Independent edge charge/energy checks gate output.
"""
from pathlib import Path
from array import array
import hashlib,json,time,resource
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
R=Path(__file__).resolve().parents[1];B=R/'build/filled-electrical-baseline';src=B/'filled_charge_reference.spice';out=B/'filled_condensed.spice';out.unlink(missing_ok=True)
resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3));start=time.monotonic()
manifest=dict(completed=False,accepted_full_chip_rc=False,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),scope='Exact constant-C Schur reduction at zero floating charge, within recorded numerical checks. No distributed wire R. All semiconductor records retained.')
(B/'reduction.json').write_text(json.dumps(manifest,indent=2)+'\n')
body=[];ret=set()
for l in src.open():
 if l.startswith('C'):continue
 body.append(l);t=l.split()
 if not t:continue
 if t[0]=='.subckt':ret.update(t[2:])
 elif t[0]=='+':ret.update(t[1:])
 elif t[0].startswith('X'):
  end=next(i for i,z in enumerate(t) if '=' in z)-1;ret.update(t[1:end])
 elif t[0].startswith('D'):ret.update(t[1:3])
 elif t[0].startswith('R'):ret.update(t[1:3])
names=sorted(ret);idx={n:i for i,n in enumerate(names)};K=len(names);aa=array('i');bb=array('i');cc=array('d')
for l in src.open():
 if not l.startswith('CREF'):continue
 t=l.split();assert t[3].endswith('f');v=float(t[3][:-1]);assert v>0
 for n in t[1:3]:
  if n not in idx:idx[n]=len(names);names.append(n)
 aa.append(idx[t[1]]);bb.append(idx[t[2]]);cc.append(v)
a=np.frombuffer(aa,dtype=np.int32);b=np.frombuffer(bb,dtype=np.int32);c=np.frombuffer(cc,dtype=np.float64);N=len(names)
diag=np.bincount(a,weights=c,minlength=N)+np.bincount(b,weights=c,minlength=N)
M=coo_matrix((np.r_[-c,-c,diag],(np.r_[a,b,np.arange(N)],np.r_[b,a,np.arange(N)])),shape=(N,N)).tocsr()
ncomp,labels=connected_components(M,directed=False);attached=np.isin(labels,np.unique(labels[:K]));floating=np.flatnonzero(attached & (np.arange(N)>=K));disconnected=np.flatnonzero(~attached)
print('Nodes',N,'retained',K,'floating',len(floating),'disconnected',len(disconnected),'C pairs',len(c),flush=True)
assert np.all(diag[floating]>0)
F=M[floating,:][:,floating].tocsc();P=M[floating,:K].tocsc();PP=M[:K,:K].toarray();scale=1/np.sqrt(F.diagonal());Ds=diags(scale);A=(Ds@F@Ds).tocsc()
print('Factoring scaled floating-node matrix',A.shape,A.nnz,'elapsed',time.monotonic()-start,flush=True)
lu=splu(A,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0,options={'SymmetricMode':True})
print('Factored; L+U entries',lu.L.nnz+lu.U.nnz,'elapsed',time.monotonic()-start,flush=True)
S=PP.copy();max_residual=0
for j in range(0,K,8):
 rhs=P[:,j:j+8].toarray();W=scale[:,None]*lu.solve(scale[:,None]*rhs);S[:,j:j+8]-=P.T@W
 residual=F@W-rhs;max_residual=max(max_residual,float(np.max(abs(residual))))
 if j%64==0:print('Condensed columns',min(j+8,K),'/',K,flush=True)
symerr=float(np.max(abs(S-S.T)));assert symerr<1e-8,symerr;S=(S+S.T)/2
# Graph representation enforces common-mode invariance. Only tiny positive
# off-diagonal roundoff can be zeroed, with an explicit matrix-error check.
E=np.zeros_like(S);pairs=[];max_positive_offdiag=0
for i in range(K):
 for j in range(i+1,K):
  v=-S[i,j]
  if v<0:max_positive_offdiag=max(max_positive_offdiag,-v);assert -v<1e-9,('nonpassive off-diagonal',i,j,v);continue
  if v>0:pairs.append((i,j,v));E[i,i]+=v;E[j,j]+=v;E[i,j]-=v;E[j,i]-=v
representation_error=float(np.max(abs(E-S)));assert representation_error<1e-7,representation_error
checks=[]
for case in ['common-mode',17,23,31]:
 vp=np.ones(K) if case=='common-mode' else np.random.default_rng(case).uniform(-1,1,K)
 vf=-scale*lu.solve(scale*(P@vp));volt=np.zeros(N);volt[:K]=vp;volt[floating]=vf
 drop=volt[a]-volt[b];edge_charge=c*drop
 q=np.bincount(a,weights=edge_charge,minlength=N)-np.bincount(b,weights=edge_charge,minlength=N)
 expected=E@vp;limit=1e-9+1e-9*abs(q[:K]);ratio=float(np.max(abs(q[:K]-expected)/limit))
 energy=float(np.dot(c,drop*drop));reduced_energy=float(vp@E@vp);energy_error=abs(energy-reduced_energy);energy_limit=1e-9+1e-9*abs(energy)
 floating_residual=float(np.max(abs(q[floating])))
 check=dict(case=case,max_port_charge_error_fC=float(np.max(abs(q[:K]-expected))),max_charge_error_limit_ratio=ratio,twice_energy_error_fJ=energy_error,twice_energy_error_limit_fJ=energy_limit,max_floating_charge_residual_fC=floating_residual,passed=ratio<=1 and energy_error<=energy_limit and floating_residual<1e-8)
 checks.append(check);print(check,flush=True);assert check['passed'],check
with out.open('w') as f:
 f.write('* Final-GDS lumped-C reference, floating-node Schur reduction; no distributed R\n')
 for l in body:
  if not l.startswith(('*','.ends')):f.write(l)
 for n,(i,j,v) in enumerate(pairs):f.write(f'CFLOAT{n} {names[i]} {names[j]} {v:.17g}f\n')
 f.write('.ends routed_flat\n')
# Device identity and serialization are re-read rather than inferred from export success.
old_devices=[l for l in body if l.startswith(('X','D','R'))];new_devices=[l for l in out.open() if l.startswith(('X','D','R'))];assert old_devices==new_devices
for line,(i,j,v) in zip((l for l in out.open() if l.startswith('CFLOAT')),pairs):
 t=line.split();assert t[1:3]==[names[i],names[j]] and float(t[3][:-1])==v
manifest.update(completed=True,nodes=N,retained_nodes=K,floating_nodes_eliminated=len(floating),disconnected_nodes=len(disconnected),original_capacitor_pairs=len(c),condensed_capacitor_pairs=len(pairs),factor_nonzeros=lu.L.nnz+lu.U.nnz,symmetry_error_fF=symerr,representation_max_entry_error_fF=representation_error,max_positive_offdiagonal_roundoff_fF=max_positive_offdiag,max_basis_floating_residual_fF=max_residual,checks=checks,seconds=time.monotonic()-start,output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),devices_unchanged=True)
(B/'reduction.json').write_text(json.dumps(manifest,indent=2)+'\n');(R/'simulations/filled-capacitance-reduction.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Completed reduction',json.dumps({k:v for k,v in manifest.items() if k!='checks'}),flush=True)
