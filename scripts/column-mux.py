"""Break-before-make 3:1 NMOS mux, extracted array, 0.5 uA mirror."""
from pathlib import Path
import re,json,subprocess
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];out=root/'build/column-mux';out.mkdir(exist_ok=True)
base=(root/'build/column-bias/mirror_0.5uA/testbench.spice').read_text()
# NMOS passes the demonstrated ~0.44–0.99 V range with 3.3 V gate drive.
extra=''
for c in range(3):
 extra+=f'Xmux{c} OUT SEL{c} COL{c} 0 nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u\n'
 # Selection windows inside each selected-row interval; 2us dead time.
 extra+=f'Vsel{c} SEL{c} 0 PULSE(0 3.3 {975+18*c}u 10n 10n 16u 1m)\n'
extra+='Cout OUT 0 1p\nRout OUT 0 1G\n.ic v(OUT)=0\n'
s=base.replace('.control',extra+'.control')
s=re.sub(r'wrdata .*',f'wrdata {out}/wave.txt v(COL0) v(COL1) v(COL2) v(OUT) v(SEL0) v(SEL1) v(SEL2)',s)
(out/'testbench.spice').write_text(s)
p=subprocess.run(['ngspice','-b',str(out/'testbench.spice')],capture_output=True,text=True);(out/'run.log').write_text(p.stdout+p.stderr)
assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',p.stdout+p.stderr,re.I|re.M)
d=np.loadtxt(out/'wave.txt',skiprows=1);assert d[-1,0]>=.00905
baseline=np.loadtxt(root/'build/column-bias/mirror_0.5uA/wave.txt',skiprows=1)
rows=[]
for r in range(3):
 for c in range(3):
  start=.006975+r*.001+c*18e-6
  errors={str(us):float((np.interp(start+us*1e-6,d[:,0],d[:,4])-np.interp(start+us*1e-6,d[:,0],d[:,1+c]))*1000) for us in [1,2,5,10,15]}
  rows.append({'row':r,'col':c,'tracking_error_mV':errors,'sample_V':float(np.interp(start+10e-6,d[:,0],d[:,4])), 'column_disturbance_10us_mV':float((np.interp(start+10e-6,d[:,0],d[:,1+c])-np.interp(start+10e-6,baseline[:,0],baseline[:,4+c]))*1000)})
assert max(abs(r['tracking_error_mV']['10']) for r in rows)<1
fig,ax=plt.subplots(figsize=(11,4.5),layout='constrained');m=(d[:,0]>=.00697)&(d[:,0]<=.007032)
for i,label in enumerate(['COL0','COL1','COL2','OUT'],1):ax.plot((d[m,0]-.00697)*1e6,d[m,i],label=label)
ax.set(xlabel='Time after row selection (µs)',ylabel='Voltage (V)',title='3:1 mux · third-frame row 0 · 1 pF output load');ax.grid(alpha=.2);ax.legend();fig.savefig(root/'docs/assets/column-mux.png',dpi=160)
(root/'simulations/column-mux.json').write_text(json.dumps({'samples':rows,'max_10us_tracking_error_mV':max(abs(r['tracking_error_mV']['10']) for r in rows),'scope':'Schematic NMOS mux and mirror on extracted array; ideal 3.3V select signals; 2us break-before-make; 1pF/1Gohm output load, not ADC model. Samples occur at different exposure times.'},indent=2)+'\n')
print(rows)
