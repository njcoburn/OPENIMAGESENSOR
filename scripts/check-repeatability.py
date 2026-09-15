"""Controlled finite-reset experiments. Run inside the tools container."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,re
import numpy as np
root=Path(__file__).resolve().parents[1]
out=root/'build/repeatability';out.mkdir(parents=True,exist_ok=True)
base=(root/'simulations/cycles_from_schematic.spice').read_text().split('.control')[0]
base=base.replace('abstol=1e-16 reltol=1e-5','abstol=1e-16 reltol=1e-5 chgtol=1e-18 trtol=1 method=gear')
# Keep reset-to-sample exposure fixed at 950 us; change only named factors.
cases=[('baseline',20,3.3,1),('long_reset',100,3.3,1),('low_reset',20,2.0,1),('mid_reset',20,2.2,1),('low_reset_fine',20,2.0,.2),('low_reset_finer',20,2.0,.05)]
def run(case):
 name,width,vr,step=case;period=width+980;rows=[]
 for light in [0,1e-12,5e-12]:
  tag=f'{name}_{light:g}';folder=out/tag;folder.mkdir(exist_ok=True)
  s=base.replace('Xrst vdd rst sense','Xrst vreset rst sense')
  s=re.sub(r'^Vrst .*',f'Vreset vreset 0 {vr}\nVrst rst 0 PULSE(3.3 0 {width}u 10n 10n 979.98u {period}u)',s,flags=re.M)
  s=re.sub(r'^Vrow .*',f'Vrow row 0 PULSE(0 3.3 {width+900}u 10n 10n 60u {period}u)',s,flags=re.M)
  s=re.sub(r'^Iphoto .*',f'Iphoto sense 0 {light}',s,flags=re.M)
  s+=f'''\n.control
set num_threads=1
set wr_singlescale
set wr_vecnames
tran {step}u {20*period}u uic
wrdata {folder}/wave.txt v(sense) v(col)
quit
.endc
.end
'''
  (folder/'test.spice').write_text(s)
  r=subprocess.run(['ngspice','-b',str(folder/'test.spice')],capture_output=True,text=True)
  (folder/'run.log').write_text(r.stdout+r.stderr)
  if r.returncode or re.search(r'(?im)^error|timestep too small',r.stdout+r.stderr):raise RuntimeError(tag)
  d=np.loadtxt(folder/'wave.txt',skiprows=1);assert np.isfinite(d).all()
  samples=[float(np.interp((i*period+width+950)*1e-6,d[:,0],d[:,2])) for i in range(20)]
  resets=[float(np.interp((i*period+width-1)*1e-6,d[:,0],d[:,1])) for i in range(20)]
  rows.append(dict(light_A=light,samples_V=samples,reset_end_V=resets,last_delta_uV=1e6*(samples[-1]-samples[-2]),last5_span_uV=1e6*np.ptp(samples[-5:])))
 result=dict(name=name,reset_us=width,reset_V=vr,step_us=step,period_us=period,rows=rows)
 print(name,[(r['light_A'],r['last5_span_uV']) for r in rows],flush=True)
 return result
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,cases))
(root/'simulations/repeatability.json').write_text(json.dumps(results,indent=2)+'\n')
a=next(c for c in results if c['name']=='low_reset');b=next(c for c in results if c['name']=='low_reset_fine')
error=max(abs(x-y) for ra,rb in zip(a['rows'],b['rows']) for x,y in zip(ra['samples_V'],rb['samples_V']))
print('Maximum 1 us vs 0.2 us sample difference (uV):',error*1e6)
assert error<1e-4,'Step sensitivity exceeds provisional 100 uV threshold'

c=next(c for c in results if c['name']=='low_reset_finer')
fine_error=max(abs(x-y) for ra,rb in zip(b['rows'],c['rows']) for x,y in zip(ra['samples_V'],rb['samples_V']))
assert fine_error<1e-4, 'Fine timestep sensitivity exceeds 100 uV'
assert all(row['last5_span_uV']<100 for row in c['rows']), 'Candidate is not repeatable to 100 uV in final five cycles'
for i in range(20):assert c['rows'][0]['samples_V'][i]>c['rows'][1]['samples_V'][i]>c['rows'][2]['samples_V'][i]
print('Fine-step maximum difference (uV):', fine_error*1e6)
