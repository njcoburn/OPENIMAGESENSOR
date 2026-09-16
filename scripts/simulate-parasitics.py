"""Same three-frame scan through schematic, C-only and RC extracted models."""
from pathlib import Path
import json,re,subprocess,hashlib
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];out=root/'build/parasitics/sim';out.mkdir(exist_ok=True)
base=(root/'build/size-study/20um/build/array-sim/array_tb.spice').read_text()
cases=[('schematic',None,None),('extracted_devices','rc-filled','array_devices'),('C_unfilled','rc-probe','array_c'),('C_filled','rc-filled','array_c'),('RC_unfilled','rc-probe','array_reduced'),('RC_filled','rc-filled','array_reduced')]
results={};waves={}
for name,variant,file in cases:
 dest=out/name;dest.mkdir(exist_ok=True)
 if variant:
  path=root/'build/parasitics'/variant;netlist=path/f'{file}.spice';mapping=json.loads((path/'reduction.json').read_text())['node_map']
  if file=='array_reduced':nodes={key:{k:'xarray.'+v for k,v in r.items()} for key,r in mapping.items()}
  else:nodes={f'{r}{c}':{'sense':f'xarray.s{r}{c}','sf':f'xarray.f{r}{c}','anode':'0'} for r in range(3) for c in range(3)}
 else:
  netlist=root/'build/size-study/20um/build/array_schematic.spice';nodes={f'{r}{c}':{'sense':f'xarray.x{r}{c}.sense','sf':f'xarray.x{r}{c}.sf','anode':'0'} for r in range(3) for c in range(3)}
 sub=next(x.split() for x in netlist.read_text().splitlines() if x.lower().startswith('.subckt'))
 source=base.replace('/foss/designs/build/array_schematic.spice',str(netlist))
 source=re.sub(r'(?m)^Xarray .*','Xarray '+' '.join('0' if x=='GND' else x for x in sub[2:])+' '+sub[1],source)
 for key,r in nodes.items():
  source=source.replace(f'xarray.x{key}.sense',r['sense']).replace(f'xarray.x{key}.sf',r['sf'])
  source=re.sub(rf'(?m)^(Ilight{key} \S+) 0 ',rf'\1 {r["anode"]} ',source)
 vectors=' '.join('v('+n['sense']+')' if n['anode']=='0' else 'v('+n['sense']+')-v('+n['anode']+')' for n in (nodes[f'{r}{c}'] for r in range(3) for c in range(3)))
 source=re.sub(r'wrdata .*',f'wrdata {dest}/wave.txt v(ROW0) v(ROW1) v(ROW2) v(COL0) v(COL1) v(COL2) {vectors}',source)
 source=source.replace('abstol=1e-16 reltol=1e-5 chgtol=1e-18 trtol=1','abstol=1e-14 reltol=1e-4 chgtol=1e-16 trtol=3')
 (dest/'testbench.spice').write_text(source)
 run=subprocess.run(['ngspice','-b',str(dest/'testbench.spice')],capture_output=True,text=True)
 (dest/'run.log').write_text(run.stdout+run.stderr)
 assert run.returncode==0 and not re.search(r'(?im)^error|timestep too small|simulation.*aborted',run.stdout+run.stderr),(name,(run.stdout+run.stderr)[-2000:])
 d=np.loadtxt(dest/'wave.txt',skiprows=1);assert d.shape[1]==16 and np.isfinite(d).all() and d[-1,0]>=.00905
 at=lambda t,c:float(np.interp(t,d[:,0],d[:,c]));frames=[[[at(f*.003+r*.001+.00102,4+c) for c in range(3)] for r in range(3)] for f in range(3)]
 pattern=np.array([[0,80,240],[240,0,80],[80,240,0]])
 for row in range(3):assert np.all(np.diff(np.array(frames[-1][row])[np.argsort(pattern[row])])<0)
 samples=frames[-1][0];signal=[1000*(samples[0]-x) for x in samples]
 result={'frames_V':frames,'row0_dark_subtracted_mV':signal,'max_frame2_to3_change_uV':float(np.max(np.abs(np.array(frames[-1])-np.array(frames[-2])))*1e6),'max_reset_error_mV':max(abs(2-at(.006069+r*.001,7+3*r+c))*1000 for r in range(3) for c in range(3)),'dark_column_change_25_to_50us_mV':max(abs(at(.00702+r*.001,4+r)-at(.006995+r*.001,4+r))*1000 for r in range(3)),'netlist_sha256':hashlib.sha256(netlist.read_bytes()).hexdigest()}
 results[name]=result;waves[name]=d;print(name,json.dumps(result),flush=True)
assert np.max(np.abs(np.array(results['schematic']['frames_V'])-np.array(results['extracted_devices']['frames_V'])))<1e-5,'Extracted devices differ before parasitics'
fig,ax=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
for name in ['schematic','C_unfilled','C_filled','RC_filled']:
 d=waves[name];mask=(d[:,0]>.00608)&(d[:,0]<.00702)
 ax[0].plot((d[mask,0]-.00607)*1000,d[mask,8],label=name)
 ax[1].plot([0,.2,.6],results[name]['row0_dark_subtracted_mV'],'o-',label=name)
ax[0].set(xlabel='Time after reset release (ms)',ylabel='Sense voltage (V)',title='Medium light · 80 pA')
ax[1].set(xlabel='Assumed photocurrent density (pA/µm²)',ylabel='Dark-subtracted column signal (mV)',title='Third-frame sampled response')
for a in ax:a.grid(alpha=.2);a.legend()
fig.savefig(root/'docs/assets/parasitic-comparison.png',dpi=160);plt.close(fig)
checks=json.loads((root/'build/size-study/20um/simulations/array-verification.json').read_text());assert checks['gds_sha256']==hashlib.sha256((root/'build/size-study/20um/build/array_3x3.gds').read_bytes()).hexdigest()
summary={'gds_sha256':checks['gds_sha256'],'cases':results,'reductions':{v:json.loads((root/f'build/parasitics/{v}/reduction.json').read_text()) for v in ['rc-probe','rc-filled']},'scope':'Typical-corner extraction of the 20um array. Linear floating-fill C reduced at zero net charge; extracted resistance retained. No optical calibration, noise, package or external amplifier/ADC model.'}
(root/'simulations/parasitic-results.json').write_text(json.dumps(summary,indent=2)+'\n')
