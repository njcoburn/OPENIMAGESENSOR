"""Row-scanning testbench for the LVS-matched physical Xschem array."""
from pathlib import Path
import subprocess,re,json
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'build/array-sim';out.mkdir(exist_ok=True)
pattern=[[0,5,15],[15,0,5],[5,15,0]]
lines=['Physical 3x3 GF180 row-scan test','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice','.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical','.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice diode_typical','.include /foss/designs/build/array_schematic.spice','.options gmin=1e-17 abstol=1e-16 reltol=1e-5 chgtol=1e-18 trtol=1 method=gear','Vdd VDD 0 3.3','Vreset VRESET 0 2.0','Xarray VDD VRESET 0 RST0 RST1 RST2 ROW0 ROW1 ROW2 COL0 COL1 COL2 array_3x3']
for row in range(3):
 delay=50+1000*row
 lines += [f'Vr{row} RST{row} 0 PULSE(0 3.3 {delay}u 10n 10n 20u 3m)',f'Vs{row} ROW{row} 0 PULSE(0 3.3 {delay+920}u 10n 10n 60u 3m)']
 for col in range(3):
  lines += [f'Ilight{row}{col} xarray.x{row}{col}.sense 0 {pattern[row][col]}p',f'.ic v(xarray.x{row}{col}.sense)=0 v(xarray.x{row}{col}.sf)=0']
for col in range(3):lines += [f'Rload{col} COL{col} 0 1Meg',f'Cload{col} COL{col} 0 1p',f'.ic v(COL{col})=0']
lines += ['.control','set num_threads=1','set wr_singlescale','set wr_vecnames','tran 0.2u 9.05m uic',f'wrdata {out}/wave.txt v(ROW0) v(ROW1) v(ROW2) v(COL0) v(COL1) v(COL2)','quit','.endc','.end']
(out/'array_tb.spice').write_text('\n'.join(lines)+'\n')
r=subprocess.run(['ngspice','-b',str(out/'array_tb.spice')],capture_output=True,text=True)
(out/'run.log').write_text(r.stdout+r.stderr)
assert r.returncode==0 and not re.search(r'(?im)^error|timestep too small|simulation.*aborted',r.stdout+r.stderr), (r.stdout+r.stderr)[-1500:]
d=np.loadtxt(out/'wave.txt',skiprows=1);assert d.shape[1]==7 and np.isfinite(d).all() and d[-1,0]>=.00905
assert np.max(np.sum(d[:,1:4]>1.65,axis=1))==1,'Overlapping row selects'
frames=[]
for frame in range(3):
 readings=[]
 for row in range(3):
  t=frame*.003+row*.001+.00102
  readings.append([float(np.interp(t,d[:,0],d[:,4+col])) for col in range(3)])
 frames.append(readings)
for row in range(3):
 order=np.argsort(pattern[row]);v=np.array(frames[-1][row]);assert np.all(np.diff(v[order])<0), (row,v)
res={'photocurrent_pA':pattern,'frames_V':frames,'max_frame2_to3_change_V':float(np.max(np.abs(np.array(frames[-1])-np.array(frames[-2])))),'sample_after_reset_rise_us':970,'frame_period_ms':3,'notes':'Schematic simulation with model junction capacitance and assumed external photocurrent. No extracted wiring parasitics.'}
(root/'simulations/array-results.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
