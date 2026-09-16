"""Recheck stronger buffer and global startup reset across the prior matrix."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json
root=Path(__file__).resolve().parents[1];m=runpy.run_path(str(root/'scripts/buffer-hardening.py'));run=m['combined']
cases=[(c,t,'diode_typical') for c in ['typical','ff','ss','fs','sf'] for t in [-40,27,85,125]]+[('typical',t,d) for d in ['diode_ff','diode_ss'] for t in [-40,125]]
def worker(case):
 c,t,d=case;name,r=run(c,t,40,step=.1,diode=d,variant='_startup_reset')
 r['screen_pass']=bool(r['status']=='complete' and r['brightness_order_ok'] and r['max_hold_error_mV']<.5 and r['max_tracking_error_mV']<.5)
 return name,r
results=dict(ThreadPoolExecutor(max_workers=4).map(worker,cases))
(root/'simulations/buffer-hardened-corners.json').write_text(json.dumps({'cases':results,'target_mV':.5,'bias_uA':40,'startup_reset_us':20,'scope':'All rows reset at startup; original rolling resets and sampling schedule retained. No mux precharge. Fixed 3.3V supply, ideal current references, nominal extracted R/C, assumed photocurrent and load values; buffer schematic-only. Same 24-case process/temperature matrix as prior report.'},indent=2)+'\n')
print('SUMMARY',sum(r['screen_pass'] for r in results.values()),'of',len(results),flush=True)
