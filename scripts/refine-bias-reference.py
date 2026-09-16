"""Timestep checks for worst sampling, startup and lowest-drive cases."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,runpy
root=Path(__file__).resolve().parents[1];p=root/'simulations/bias-reference.json';d=json.loads(p.read_text());rows=list(d['cases'].values())
assert len(rows)==d['planned_cases'] and all(r['status']=='complete' for r in rows)
selected=[max(rows,key=lambda r:r['max_hold_error_mV']),max(rows,key=lambda r:r['startup_reference_relative_error']),min(rows,key=lambda r:r['mean_buffer_reference_uA'])]
fields=['corner','temp_C','supply_V','diode','rcol_scale','rbuf_scale','ramp_us','external_bias_C_pF']
tasks=list(dict.fromkeys(tuple(r[k] for k in fields) for r in selected));scan=runpy.run_path(str(root/'scripts/bias-reference.py'))['scan']
def check(t):
 name,r=scan(*t,step=.05);assert r['status']=='complete',r
 old=next(v for v in rows if tuple(v[k] for k in fields)==t)
 delta=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(r['samples'],old['samples']))
 assert delta<.1 and r['screen_pass']==old['screen_pass'],(name,delta,r)
 return name,{'result':r,'max_sample_change_mV':delta}
d['refinements']=dict(ThreadPoolExecutor(max_workers=3).map(check,tasks));p.write_text(json.dumps(d,indent=2)+'\n');print('Bias-reference refinements complete')
