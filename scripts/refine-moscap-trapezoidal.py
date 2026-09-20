"""Refine the isolated-clamp trapezoidal candidate before any promotion."""
import importlib.util,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('branch',R/'scripts/diagnose-moscap-branch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
deck=(m.B/'clamp-localFalse-smoothFalse/test.spice').read_text();body=deck[deck.index('\nX1 ')+1:deck.index('.control')]
log=(m.B/'integration-trapezoidal/ngspice.log').read_text()
assert 'ngspice-46 done' in log and 'aborted' not in log
base=np.loadtxt(m.B/'integration-trapezoidal/tran.dat',skiprows=1,ndmin=2);assert base[-1,0]>=152.99e-6

def run(case):
 name,options=case
 row=m.simulate(name,body,'v(vb,gb) v(db,dg) v(a_56346_55631#,DVSS_B.t335) i(Vport0)',step='50n',extra_options=options)
 if row['completed']:
  a=np.loadtxt(m.B/name/'tran.dat',skiprows=1,ndmin=2)
  t=np.unique(np.r_[base[base[:,0]>=150e-6,0],a[a[:,0]>=150e-6,0]])
  dif=np.array([np.interp(t,a[:,0],a[:,i])-np.interp(t,base[:,0],base[:,i]) for i in range(1,5)])
  row['post_startup_max_difference']={'rail_V':float(np.max(abs(dif[:2]))),'moscap_V':float(np.max(abs(dif[2]))),'source_A':float(np.max(abs(dif[3])))}
  row['load_sample_151_5us_difference_V']=[float(np.interp(151.5e-6,a[:,0],a[:,i])-np.interp(151.5e-6,base[:,0],base[:,i])) for i in [1,2]]
  row['rail_refinement_pass']=bool(np.max(abs(dif[:2]))<10e-6)
 return row
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,[('trap-halfstep','.options method=trap'),('trap-halfstep-strict','.options method=trap reltol=1e-7 abstol=1e-14')]))
(m.B/'refinement.json').write_text(json.dumps(dict(runs=rows,rail_comparison_limit_V=10e-6,scope='Isolated clamp, post-startup 150–153us including load edges; not full-corner or ADC qualification'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
