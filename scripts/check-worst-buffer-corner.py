"""Refine the largest sampling-error corner without changing the design."""
from pathlib import Path
import runpy,json
root=Path(__file__).resolve().parents[1];p=root/'simulations/buffer-corners.json';data=json.loads(p.read_text())
complete=[r for r in data['cases'].values() if r['status']=='complete'];assert complete,'No completed cases for refinement'
worst=max(complete,key=lambda r:r['max_hold_error_mV'])
m=runpy.run_path(str(root/'scripts/buffer-corners.py'));worker=m['worker'];worker.__globals__['REFINE']=True
name,result=worker((worst['corner'],worst['temperature_C'],worst['diode_corner']));assert result['status']=='complete',result
change=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(worst['samples'],result['samples']))
assert change<.1,change
assert result['screen_pass']==worst['screen_pass'],'Screening conclusion changed at smaller timestep'
data['worst_corner_refinement']={'case':name,'result':result,'max_sample_voltage_change_mV':change,'step_us':.1,'reltol':5e-5}
p.write_text(json.dumps(data,indent=2)+'\n');print('Refinement:',name,change,'mV',result['screen_pass'])
