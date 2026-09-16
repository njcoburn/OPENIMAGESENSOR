"""Resolve numerical margin near the 1mV screen; retain every earlier result."""
from pathlib import Path
import json,runpy
root=Path(__file__).resolve().parents[1];p=root/'simulations/buffer-corners.json';d=json.loads(p.read_text());previous=d['worst_corner_refinement'];old=previous['result']
m=runpy.run_path(str(root/'scripts/buffer-corners.py'));worker=m['worker'];g=worker.__globals__;g['REFINE']=True;g['STEP']=.05;g['RELTOL']=1e-5
name,r=worker((old['corner'],old['temperature_C'],old['diode_corner']))
if r['status']!='complete':
 d['fine_margin_check']={'case':name,'result':r,'step_us':.05,'reltol':1e-5,'status':'simulation_failed'}
 p.write_text(json.dumps(d,indent=2)+'\n');print('Fine check inconclusive; see retained log.');raise SystemExit(0)
change=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(old['samples'],r['samples']))
d['fine_margin_check']={'case':name,'result':r,'max_sample_voltage_change_mV':change,'step_us':.05,'reltol':1e-5,'margin_to_limit_mV':1-r['max_hold_error_mV'],'numerical_change_below_margin':change<abs(1-r['max_hold_error_mV'])}
p.write_text(json.dumps(d,indent=2)+'\n');print(d['fine_margin_check'])
