"""Selected imaging/startup checks following the resistor-reference DC survey."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import runpy,json,hashlib
root=Path(__file__).resolve().parents[1];dc=json.loads((root/'simulations/bias-reference-dc.json').read_text());rows=list(dc['cases'].values());assert len(rows)==84 and all(r['status']=='complete' for r in rows)
scan=runpy.run_path(str(root/'scripts/bias-reference.py'))['scan']
# Nominal supply sweep, former worst hot/diode case, mixed hot/low supply,
# and every measured reference-current extreme (including resistor tolerance).
tasks=[('typical',27,v,'diode_typical',1,1,1,5,.1) for v in [3.0,3.3,3.6]]
tasks += [('typical',125,v,'diode_ff',1,1,1,5,.1) for v in [3.0,3.3,3.6]]
tasks += [('fs',125,3.0,'diode_typical',1,1,1,5,.1)]
extremes=[]
for key in ['column_reference_uA','buffer_reference_uA']:
 for func in [min,max]:
  r=func(rows,key=lambda r:r[key]);t=(r['corner'],r['temp_C'],r['supply_V'],r['diode'],r['rcol_scale'],r['rbuf_scale']);extremes.append(t);tasks.append((*t,1,5,.1))
for c,t,v,d,rc,rb in [('typical',27,3.3,'diode_typical',1,1),extremes[2],extremes[3]]:
 tasks += [(c,t,v,d,rc,rb,ramp,5,.1) for ramp in [100,1000]]
tasks.append((*extremes[2],1000,50,.1))
tasks=list(dict.fromkeys(tasks))
sources=['circuits/board-bias.spice','circuits/bias-scan-template.spice','circuits/bias-dc-template.spice','checkpoints/integrated/pex/sensor_reduced.spice','scripts/bias-reference.py']
d={'cases':{},'planned_cases':len(tasks),'dc_cases':84,'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},'scope':'Board resistors replace both ideal bias current sources; existing extracted on-chip mirrors retained. Selected imaging PVT/tolerance cases and 1/100/1000us supply ramps, 200us post-ramp reset hold. 5pF assumed external capacitance per bias pin, plus one 50pF sensitivity case. VRESET remains externally generated ideal 2V; controller and ADC remain idealized. Not an on-chip regulated reference or pad/ESD verification.'}
p=root/'simulations/bias-reference.json'
with ThreadPoolExecutor(max_workers=4) as pool:
 futures=[pool.submit(scan,*t) for t in tasks]
 for f in as_completed(futures):
  name,r=f.result();d['cases'][name]=r;p.write_text(json.dumps(d,indent=2)+'\n');print('Progress',len(d['cases']),'/',len(tasks),flush=True)
d['cases']=dict(sorted(d['cases'].items()));p.write_text(json.dumps(d,indent=2)+'\n')
print('Screen',sum(r['screen_pass'] for r in d['cases'].values()),'/',len(tasks))
