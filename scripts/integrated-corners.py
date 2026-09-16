"""Full 24-case device process/temperature screen of the connected RC layout."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,runpy,hashlib
root=Path(__file__).resolve().parents[1]
module=runpy.run_path(str(root/'scripts/simulate-integrated.py'));simulate=module['simulate']
cases=[(c,t,'diode_typical') for c in ['typical','ff','ss','fs','sf'] for t in [-40,27,85,125]]
cases += [('typical',t,d) for d in ['diode_ff','diode_ss'] for t in [-40,125]]
baseline=json.loads((root/'simulations/buffer-pex.json').read_text())['cases']
sources=['checkpoints/integrated/sensor_3x3.gds','build/integrated-pex/sensor_reduced.spice','build/integrated-pex/sensor_alternate.spice','scripts/simulate-integrated.py','scripts/buffer-hardening.py','scripts/output-buffer.py','circuits/output-buffer-template.spice']
d={'cases':{},'planned_cases':24,'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},'scope':'24 device process/temperature cases: five MOS sections times four temperatures with typical diode, plus typical MOS with fast/slow diode at cold/hot endpoints. Connected RC with nominal wire R/C, 3.3V supply, ideal 40uA/0.5uA references, generic ADC load; not full MOS/diode/interconnect cross-product or supply/noise/mismatch qualification. DC calibration selects all rows with reset on and mux off; transient uses rolling selection. BIAS/OUT signed-shunt placement approximation retained.'}
p=root/'simulations/integrated-corners.json'
def save():p.write_text(json.dumps(d,indent=2)+'\n')
with ThreadPoolExecutor(max_workers=4) as pool:
 futures={pool.submit(simulate,*c):c for c in cases}
 for f in as_completed(futures):
  name,r=f.result();c,t,dio=futures[f];r.update(corner=c,temp_C=t,diode=dio)
  if r['status']=='complete':
   old=next(v for v in baseline.values() if v['buffer_model']=='RC' and (v['corner'],v['temp_C'],v['diode'])==(c,t,dio))
   r['max_output_shift_vs_separate_blocks_mV']=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(r['samples'],old['samples']))
  d['cases'][name]=r;save()
  print('Progress',len(d['cases']),'/',len(cases),flush=True)
# Deterministic table order independent of worker completion order.
d['cases']=dict(sorted(d['cases'].items()));save()
assert len(d['cases'])==24
print('RC screen:',sum(v['screen_pass'] for v in d['cases'].values()),'/ 24',flush=True)
