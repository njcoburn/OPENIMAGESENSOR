"""Check filled RC sampled outputs against a smaller transient step."""
from pathlib import Path
import subprocess,json,numpy as np
root=Path(__file__).resolve().parents[1]
p=root/'build/parasitics/sim/RC_filled';dest=root/'build/parasitics/sim/RC_filled_refined';dest.mkdir(exist_ok=True)
s=(p/'testbench.spice').read_text().replace('tran 0.2u','tran 0.1u').replace('reltol=1e-4','reltol=5e-5').replace(str(p/'wave.txt'),str(dest/'wave.txt'))
(dest/'testbench.spice').write_text(s)
r=subprocess.run(['ngspice','-b',str(dest/'testbench.spice')],capture_output=True,text=True)
(dest/'run.log').write_text(r.stdout+r.stderr)
assert r.returncode==0 and 'aborted' not in r.stdout+r.stderr
wave=np.loadtxt(dest/'wave.txt',skiprows=1);assert wave[-1,0]>=.00905
samples=np.array([[[np.interp(f*.003+row*.001+.00102,wave[:,0],wave[:,4+c]) for c in range(3)] for row in range(3)] for f in range(3)])
file=root/'simulations/parasitic-results.json';data=json.loads(file.read_text());error=float(np.max(np.abs(samples-np.array(data['cases']['RC_filled']['frames_V'])))*1000)
assert error<.1,error
data['numerical_check']={'half_step_us':.1,'relative_tolerance':5e-5,'max_all_samples_difference_mV':error,'acceptance_limit_mV':.1}
file.write_text(json.dumps(data,indent=2)+'\n');print(data['numerical_check'])
