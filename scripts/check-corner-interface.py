"""Verify an exact eight-port E/V/F reformulation, then retry corner startup.
No hardware buffer, parasitic, or PDK device is added or removed.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess, os, json, re, argparse
import numpy as np
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--strict',action='store_true')
parser.add_argument('--startup-practical',action='store_true',help='Use the preceding ramp baseline tolerances for diagnostic startup')
parser.add_argument('--diagnostic-startup',action='store_true',help='Run startup even if equivalence misses its screen; never promote that screen to a pass')
parser.add_argument('--seed',action='store_true')
parser.add_argument('--reuse-equivalence',action='store_true',help='Validate and reuse completed equivalence decks in this output directory')
args=parser.parse_args()
B=R/('build/corner-interface-seeded' if args.seed else 'build/corner-interface-strict' if args.strict else 'build/corner-interface'); B.mkdir(exist_ok=True)
P=R/'build/charge-reduced/corner-full'
ports='VDD_A VDD_B VSS_A VSS_B DVDD_A DVDD_B DVSS_A DVSS_B'.split()
external='feed vb 0 gb feed db 0 dg'.split()

def run(mode,adapter,analysis):
 d=B/f'{mode}-{"adapter" if adapter else "direct"}-{analysis}';d.mkdir(exist_ok=True)
 original=(P/f'{mode}.spice').read_text()
 # Flatten only the coupon wrapper, retaining every device and passive record.
 model='\n'.join(l for l in original.splitlines() if not l.lower().startswith(('.subckt','.ends')))+'\n'
 (d/'model.spice').write_text(model)
 base=(P/f'practical-{mode}/test.spice').read_text()
 base=base[:base.index('.control')]
 if args.strict and analysis!='startup-practical':base=base.replace('reltol=5e-5 abstol=1e-12','reltol=1e-7 abstol=1e-14')
 interface=[]
 for i,(port,ext) in enumerate(zip(ports,external)):
  if adapter:
   interface.extend([f'Eport{i} drive{i} 0 {ext} 0 1',f'Vport{i} drive{i} {port} 0',f'Fport{i} {ext} 0 Vport{i} 1'])
  else: interface.append(f'Vport{i} {ext} {port} 0')
 if args.seed and adapter and analysis=='equivalence':
  raw=(B/f'{mode}-direct-equivalence/op.raw').read_text()
  variables,values=raw.split('Variables:\n')[1].split('Values:\n')
  names=[line.split()[1] for line in variables.splitlines()]
  vals=[float(line.split()[-1]) for line in values.splitlines() if line.strip()]
  assert len(names)==len(vals)
  base+=''.join(f'.nodeset {name}={value:.17g}\n' for name,value in zip(names,vals) if name.startswith('v('))
 base+='\n'.join(interface)+'\n.control\nset klu\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\n'
 vectors=' '.join(['v(vb,gb)','v(db,dg)','i(Vsrc)']+[f'i(Vport{i})' for i in range(8)])
 if analysis=='equivalence':
  base+=f'op\nset filetype=ascii\nwrite op.raw all\nwrdata dc.dat {vectors}\nac dec 10 1k 1g\nwrdata ac.dat {vectors}\n'
 else:
  base=base.replace('Vsrc src 0 DC 3.3 AC 1','Vsrc src 0 PWL(0 0 100u 3.3)').replace('1m 1u 1n','1m 151u 1n').replace('reltol=5e-5','reltol=1e-6')
  base+=f'tran 100n 153u 0 100n uic\nwrdata tran.dat {vectors}\n'
 base+='quit\n.endc\n.end\n';(d/'test.spice').write_text(base)
 row=dict(mode=mode,adapter=adapter,analysis=analysis)
 try:
  with (d/'ngspice.log').open('w') as f:
   p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=600,env={**os.environ,'SPICE_USERINIT_DIR':str(R/'checkpoints/pad-closure/ngspice-init')})
  errors=[l for l in (d/'ngspice.log').read_text().splitlines() if re.search('aborted|timestep too small|^Error',l,re.I)]
  assert p.returncode==0 and not errors,errors[-4:]
  for name in (['dc','ac'] if analysis=='equivalence' else ['tran']):
   a=np.loadtxt(d/f'{name}.dat',skiprows=1,ndmin=2);assert np.isfinite(a).all()
   if name=='tran':assert a[-1,0]>=152.99e-6
  row['completed']=True
 except Exception as e:row.update(completed=False,error=str(e))
 print(row,flush=True);return row

if __name__=='__main__':
 cases=[(m,a,'equivalence') for m in ['nominal','remote'] for a in [False,True]]
 if args.reuse_equivalence:
  rows=[]
  for m,a,kind in cases:
   d=B/f'{m}-{"adapter" if a else "direct"}-equivalence'
   log=(d/'ngspice.log').read_text()
   assert 'ngspice-46 done' in log and not re.search('aborted|timestep too small|^Error',log,re.I|re.M)
   rows.append(dict(mode=m,adapter=a,analysis=kind,completed=True))
 elif args.seed:
  with ThreadPoolExecutor(max_workers=2) as pool: rows=list(pool.map(lambda m:run(m,False,'equivalence'),['nominal','remote']))
  with ThreadPoolExecutor(max_workers=2) as pool: rows+=list(pool.map(lambda m:run(m,True,'equivalence'),['nominal','remote']))
 else:
  with ThreadPoolExecutor(max_workers=2) as pool: rows=list(pool.map(lambda c:run(*c),cases))
 checks=[]
 if rows:
  for m in ['nominal','remote']:
   if not all(r['completed'] for r in rows if r['mode']==m):continue
   for kind in ['dc','ac']:
    x,y=[np.loadtxt(B/f'{m}-{a}-equivalence/{kind}.dat',skiprows=1,ndmin=2) for a in ['direct','adapter']]
    assert x.shape==y.shape and np.isfinite(x).all() and np.isfinite(y).all()
    if kind=='ac':assert np.array_equal(x[:,0],y[:,0])
    # First two vectors are voltage; remaining nine are currents.
    n=2 if kind=='dc' else 4
    tolerance=np.r_[np.full(n,1e-8),np.full(x.shape[1]-1-n,1e-12)]
    ratio=float(np.max(abs(x[:,1:]-y[:,1:])/(tolerance+1e-5*abs(x[:,1:]))))
    checks.append(dict(mode=m,analysis=kind,max_mixed_error_ratio=ratio,passed=ratio<=1))
 result=dict(runs=rows,equivalence=checks,scope='27C typical; common-mode AC 1kHz–1GHz; eight port currents plus rail voltages; no physical buffer')
 (B/('summary-practical-startup.json' if args.startup_practical else 'summary.json')).write_text(json.dumps(result,indent=2)+'\n')
 if args.diagnostic_startup or (len(checks)==4 and all(c['passed'] for c in checks)):
  result['startup_is_diagnostic']=not (len(checks)==4 and all(c['passed'] for c in checks))
  with ThreadPoolExecutor(max_workers=2) as pool: result['startup']=list(pool.map(lambda m:run(m,True,'startup-practical' if args.startup_practical else 'startup'),['nominal','remote']))
 (B/('summary-practical-startup.json' if args.startup_practical else 'summary.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
