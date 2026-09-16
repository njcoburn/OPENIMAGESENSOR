"""Finite-impedance board supply sensitivity; no regulator/ESD qualification."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json,re
import numpy as np
root=Path(__file__).resolve().parents[1];e=runpy.run_path(str(root/'scripts/evaluate-supply-clamps.py'));out=root/'build/clamp-supply'
def test(case):
 t,rs,ramp=case;folder=out/f'{t}C_R{rs}_ramp{ramp}us';end=ramp+200
 s=e['header']('res_ss','moscap_ss','diode_ff',t,3.3)
 s=s.replace('Vdd VDD 0 3.3',f'Vdd SOURCE 0 PWL(0 0 {ramp}u 3.3)\nRsource SOURCE VDD {rs}\nCdec VDD 0 100n\nRload VDD 0 33k')
 deck=s+e['control'](folder,f'tran .02u {end}u uic','v(SOURCE) v(VDD) i(Vdd) v(xvdd.n4)')
 try:
  if (folder/'run.log').exists() and (folder/'testbench.spice').read_text()==deck:
   log=(folder/'run.log').read_text()
   if re.search(r'^Error|aborted|timestep too small',log,re.M|re.I):raise RuntimeError('Preserved failed simulation; see run.log')
   a=np.loadtxt(folder/'wave.txt',skiprows=1,ndmin=2)
  else:a=e['run'](folder,deck)
  assert np.isfinite(a).all() and a[-1,0]>=end*1e-6-1e-12
 except Exception as exc:
  return folder.name,{'temp_C':t,'source_R_ohm':rs,'ramp_us':ramp,'status':'simulation_failed','settled_at_200us':False,'error':str(exc)[-1500:]}

 target=3.3*33000/(33000+rs);tail=a[:,0]>=(end-10)*1e-6
 return folder.name,{'temp_C':t,'source_R_ohm':rs,'ramp_us':ramp,'peak_source_current_A':float(np.max(-a[:,3])),'peak_source_to_rail_drop_V':float(np.max(a[:,1]-a[:,2])),'peak_clamp_gate_V':float(np.max(a[:,4])),'tail_min_rail_V':float(np.min(a[tail,2])),'tail_max_gate_V':float(np.max(a[tail,4])),'settled_at_200us':bool(np.min(a[tail,2])>.99*target and np.max(a[tail,4])<.1)}
if __name__=='__main__':
 tasks=[(t,r,p) for t in [-40,27,125] for r in [.5,5] for p in [1,100,1000]];rows={}
 for name,r in ThreadPoolExecutor(max_workers=4).map(test,tasks):
  rows[name]=r;(root/'simulations/clamp-supply.json').write_text(json.dumps({'cases':rows,'scope':'One clamp pair; res_ss/moscap_ss/diode_ff, typical HV MOS. Ideal upstream soft-start, 0.5/5ohm source impedance, 100nF decoupling, 33kohm representative load. Not a selected regulator or sensor transient.'},indent=2)+'\n')
 print('Supply tests',len(rows),'settled',sum(r['settled_at_200us'] for r in rows.values()))
