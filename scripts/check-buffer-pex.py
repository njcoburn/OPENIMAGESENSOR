"""Numerically refine extracted-buffer cold and worst screening cases."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json
root=Path(__file__).resolve().parents[1];p=root/'simulations/buffer-pex.json';d=json.loads(p.read_text());rows=d['cases']
assert all(r['status']=='complete' for r in rows.values()),'Resolve incomplete runs first'
rc=[r for r in rows.values() if r['buffer_model']=='RC'];worst=max(rc,key=lambda r:r['max_hold_error_mV'])
cases={(worst['corner'],worst['temp_C'],worst['diode']),('ss',-40,'diode_typical')}
sim=runpy.run_path(str(root/'scripts/simulate-buffer-pex.py'))['simulate']
def check(case):
 c,t,dio=case;name,r=sim(c,t,dio,'RC',.05);assert r['status']=='complete',r
 old=next(v for v in rc if (v['corner'],v['temp_C'],v['diode'])==case)
 delta=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(old['samples'],r['samples']))
 assert delta<.1 and r['screen_pass']==old['screen_pass'],(delta,r)
 return name,{'result':r,'max_output_change_mV':delta,'step_us':.05,'reltol':1e-5}
d['refinements']=dict(ThreadPoolExecutor(max_workers=2).map(check,sorted(cases)));p.write_text(json.dumps(d,indent=2)+'\n');print('Numerical refinement complete')
