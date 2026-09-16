from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json
root=Path(__file__).resolve().parents[1];p=root/'simulations/buffer-hardened-corners.json';data=json.loads(p.read_text());rows=data['cases']
assert all(r['screen_pass'] for r in rows.values()),'Review revised corner failures before accepting candidate'
worst=max(rows.values(),key=lambda r:r['max_hold_error_mV']);cases={(worst['corner'],worst['temp_C'],worst['diode']),('ss',-40,'diode_typical')}
m=runpy.run_path(str(root/'scripts/buffer-hardening.py'));run=m['combined']
def check(case):
 c,t,d=case;name,r=run(c,t,40,step=.05,diode=d,variant='_startup_reset')
 assert r['status']=='complete' and r['max_hold_error_mV']<.5 and r['max_tracking_error_mV']<.5 and r['brightness_order_ok'],r
 coarse=next(v for v in rows.values() if (v['corner'],v['temp_C'],v['diode'])==case)
 difference=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(coarse['samples'],r['samples']));assert difference<.1,difference
 return name,{'result':r,'max_output_change_mV':difference,'step_us':.05,'reltol':1e-5}
data['refinements']=dict(ThreadPoolExecutor(max_workers=2).map(check,sorted(cases)));p.write_text(json.dumps(data,indent=2)+'\n');print('Refinement checks passed')
