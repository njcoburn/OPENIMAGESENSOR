"""Compare LVS-checked size variants at equal assumed photocurrent density."""
from pathlib import Path
import json,hashlib,re,subprocess,shutil
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
rows=[]
fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for size in (5,10,20):
 v=root/f'build/size-study/{size}um';checks=json.loads((v/'simulations/array-verification.json').read_text())
 assert checks['klayout_total']==checks['magic_drc_errors']==0
 assert checks['gds_sha256']==hashlib.sha256((v/'build/array_3x3.gds').read_bytes()).hexdigest()
 out=v/'build/size-performance';out.mkdir(exist_ok=True)
 source=(v/'build/array-sim/array_tb.spice').read_text()
 source=source.replace('/foss/designs/build/array_schematic.spice',str(v/'build/array_schematic.spice'))
 nodes=' '.join(f'v(xarray.x{r}{c}.sense)' for r in range(3) for c in range(3))
 source=re.sub(r'wrdata .*',f'wrdata {out}/wave.txt v(ROW0) v(ROW1) v(ROW2) v(COL0) v(COL1) v(COL2) {nodes}',source)
 (out/'testbench.spice').write_text(source)
 run=subprocess.run(['ngspice','-b',str(out/'testbench.spice')],capture_output=True,text=True)
 (out/'run.log').write_text(run.stdout+run.stderr)
 assert run.returncode==0 and not re.search(r'(?im)^error|timestep too small|simulation.*aborted',run.stdout+run.stderr)
 d=np.loadtxt(out/'wave.txt',skiprows=1);assert d.shape[1]==16 and np.isfinite(d).all() and d[-1,0]>=.00905
 at=lambda t,c:float(np.interp(t,d[:,0],d[:,c]))
 samples=[at(.00702,4+c) for c in range(3)]
 signal=[(samples[0]-x)*1000 for x in samples]
 assert samples[0]>samples[1]>samples[2]>0.05
 # Secant effective capacitance during the row-off integration interval, medium light.
 delta=at(.00615,8)-at(.00695,8)
 cap=(.2*size**2*1e-12)*.0008/delta*1e15
 reset_errors=[abs(2-at(.006069+.001*r,7+3*r+c))*1000 for r in range(3) for c in range(3)]
 repeat=max(abs(at(.00702+.001*r,4+c)-at(.00402+.001*r,4+c))*1e6 for r in range(3) for c in range(3))
 row=dict(size_um=size,area_um2=size**2,fill_factor_percent=size**2/4000*100,photocurrents_pA=[0,.2*size**2,.6*size**2],column_samples_V=samples,dark_subtracted_signal_mV=signal,effective_sense_capacitance_fF=cap,max_reset_error_mV=max(reset_errors),frame2_to3_max_change_uV=repeat,verification=checks)
 rows.append(row)
 axes[0].plot([0,.2,.6],signal,'o-',label=f'{size} × {size} µm')
 mask=(d[:,0]>=.006075)&(d[:,0]<=.00702)
 axes[1].plot((d[mask,0]-.00607)*1000,d[mask,8],label=f'{size} × {size} µm')
 for name in ('array-layout.png','pixel-layout.png'):
  shutil.copy2(v/'docs/assets'/name,root/'docs/assets'/f'diode-{size}um-{name}')
axes[0].set(xlabel='Assumed photocurrent density (pA/µm²)',ylabel='Dark minus illuminated column voltage (mV)',title='Equal illumination assumption · third frame')
axes[1].set(xlabel='Time after reset release (ms)',ylabel='Sense-node voltage (V)',title='Medium illumination: 0.2 pA/µm²')
for ax in axes:ax.grid(alpha=.25);ax.legend()
fig.savefig(root/'docs/assets/diode-size-comparison.png',dpi=160);plt.close(fig)
result=dict(scope='Typical-corner LVS-matched schematic simulation. Equal assumed photocurrent density, not calibrated irradiance. No extracted wire/fill parasitics or optical/noise characterization.',exposure_to_sample_us=950,reset_high_us=20,column_load='1 MOhm || 1 pF',variants=rows)
(root/'simulations/diode-size-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
