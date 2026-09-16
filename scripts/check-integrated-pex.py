"""Numerical and shunt-placement sensitivity of the connected model."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,runpy
root=Path(__file__).resolve().parents[1];p=root/'simulations/integrated-pex.json';d=json.loads(p.read_text())
rc=[r for r in d['cases'].values() if r['model']=='RC'];assert all(r['status']=='complete' for r in rc)
worst=max(rc,key=lambda r:r['max_hold_error_mV'])
simulate=runpy.run_path(str(root/'scripts/simulate-integrated.py'))['simulate']
tasks=[(r['corner'],r['temp_C'],r['diode'],.1,'alternate') for r in rc]+[(worst['corner'],worst['temp_C'],worst['diode'],.05,'RC'),('ss',-40,'diode_typical',.05,'RC')]
tasks=list(dict.fromkeys(tasks))
def check(t):
 name,r=simulate(*t);assert r['status']=='complete',r
 base=next(v for v in rc if (v['corner'],v['temp_C'],v['diode'])==t[:3])
 delta=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(r['samples'],base['samples']))
 assert delta<.1 and r['screen_pass']==base['screen_pass'],(name,delta,r)
 return name,{'result':r,'max_output_change_mV':delta,'kind':'shunt-placement' if t[4]=='alternate' else 'timestep'}
d['checks']=dict(ThreadPoolExecutor(max_workers=3).map(check,tasks));p.write_text(json.dumps(d,indent=2)+'\n');print('Sensitivity checks complete')
