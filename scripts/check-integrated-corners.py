"""Refine cold and worst-error conditions; test shunt placement at worst corner."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,runpy
root=Path(__file__).resolve().parents[1];p=root/'simulations/integrated-corners.json';d=json.loads(p.read_text());rows=list(d['cases'].values())
assert len(rows)==24 and all(r['status']=='complete' for r in rows)
worst=max(rows,key=lambda r:max(r['max_hold_error_mV'],r['max_tracking_error_mV']))
condition=(worst['corner'],worst['temp_C'],worst['diode'])
tasks=list(dict.fromkeys([(*condition,.05,'RC'),('ss',-40,'diode_typical',.05,'RC'),(*condition,.1,'alternate')]))
simulate=runpy.run_path(str(root/'scripts/simulate-integrated.py'))['simulate']
def check(t):
 name,r=simulate(*t);assert r['status']=='complete',r
 base=next(v for v in rows if (v['corner'],v['temp_C'],v['diode'])==t[:3])
 delta=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(r['samples'],base['samples']))
 assert delta<.1 and r['screen_pass']==base['screen_pass'],(name,delta,r)
 return name,{'result':r,'max_output_change_mV':delta,'kind':'timestep' if t[4]=='RC' else 'shunt-placement'}
d['checks']=dict(ThreadPoolExecutor(max_workers=3).map(check,tasks));p.write_text(json.dumps(d,indent=2)+'\n');print('Full-matrix refinements complete')
