"""Check that the numerical E/V/F interface preserves the real clamp loading.

Compare direct and reformulated foundry clamp pairs behind a 1 ohm source,
including DC leakage and complex small-signal response from 1 Hz to 1 GHz.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy, subprocess, os, re, json, time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
e=runpy.run_path(str(ROOT/'scripts/evaluate-supply-clamps.py'))
out=ROOT/'build/clamp-interface-check'

def test(case):
    t,v,d,adapter,source_r=case
    folder=out/f'{t}C_R{source_r:g}_{"adapter" if adapter else "direct"}'
    folder.mkdir(parents=True,exist_ok=True)
    s=e['header']('res_ss','moscap_typical',d,t,v)
    s=s[:s.index('Vdd VDD')]
    s+=f'Vdd SOURCE 0 {v} AC 1\nRsource SOURCE VDD {source_r}\n.include {ROOT}/circuits/sensor-supply-pads.spice\n'
    if adapter:
        s+='Eclamp CLAMPDRIVE 0 VDD 0 1\nVclamp CLAMPDRIVE CLAMPRAIL 0\nFclamp VDD 0 Vclamp 1\nXsupply CLAMPRAIL 0 sensor_supply_pads\n'
    else:s+='Xsupply VDD 0 sensor_supply_pads\n'
    s+=f'.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\nop\nwrdata {folder}/dc.txt v(VDD) i(Vdd)\nac dec 20 1 1g\nwrdata {folder}/ac.txt v(VDD) i(Vdd)\nrusage all\nquit\n.endc\n.end\n'
    (folder/'testbench.spice').write_text(s)
    with (folder/'run.log').open('w') as f:
        p=subprocess.run(['ngspice','-b',str(folder/'testbench.spice')],stdout=f,stderr=subprocess.STDOUT,timeout=120,
                         env={**os.environ,'SPICE_USERINIT_DIR':str(ROOT/'checkpoints/pad-closure/ngspice-init')})
    assert p.returncode==0 and not re.search('^Error|aborted', (folder/'run.log').read_text(),re.M|re.I)
    return t,adapter,source_r,np.loadtxt(folder/'dc.txt',skiprows=1,ndmin=2),np.loadtxt(folder/'ac.txt',skiprows=1)

if __name__=='__main__':
    rows=list(ThreadPoolExecutor(max_workers=2).map(test,[(t,v,d,a,rs) for t,v,d in [(27,3.3,'diode_typical'),(125,3.,'diode_ff')] for a in [False,True] for rs in [1,1000]]))
    result={}
    for t,rs in [(t,rs) for t in [27,125] for rs in [1,1000]]:
        direct=next(r for r in rows if r[0]==t and not r[1] and r[2]==rs);adapt=next(r for r in rows if r[0]==t and r[1] and r[2]==rs)
        dc0,ac0=direct[3:];dc1,ac1=adapt[3:]
        assert np.array_equal(ac0[:,0],ac1[:,0])
        assert all(np.isfinite(x).all() for x in [dc0,ac0,dc1,ac1])
        voltage0=ac0[:,1]+1j*ac0[:,2];voltage1=ac1[:,1]+1j*ac1[:,2]
        current0=ac0[:,3]+1j*ac0[:,4];current1=ac1[:,3]+1j*ac1[:,4]
        r={'source_R_ohm':rs,'temp_C':t,'dc_rail_difference_V':float(abs(dc0[0,1]-dc1[0,1])),
           'dc_source_current_difference_A':float(abs(dc0[0,2]-dc1[0,2])),
           'max_complex_rail_difference_V':float(np.max(abs(voltage0-voltage1))),
           'max_relative_complex_source_current_difference':float(np.max(abs(current0-current1)/np.maximum(abs(current0),1e-14))),
           'max_complex_source_current_difference_A':float(np.max(abs(current0-current1))),
           'max_mixed_current_error_ratio':float(np.max(abs(current0-current1)/(1e-12+1e-5*abs(current0)))),
           'frequency_count':len(ac0),'frequency_min_Hz':float(ac0[0,0]),'frequency_max_Hz':float(ac0[-1,0])}
        r['pass']=bool(r['dc_rail_difference_V']<1e-9 and r['dc_source_current_difference_A']<1e-12 and r['max_complex_rail_difference_V']<1e-8 and r['max_mixed_current_error_ratio']<1)
        result[f'{t}C_R{rs}']=r
    (ROOT/'simulations/clamp-interface-check.json').write_text(json.dumps({'cases':result,'current_comparison_tolerance':{'absolute_A':1e-12,'relative':1e-5},'scope':'Exact algebraic port equivalence check, full clamp models, 1/1000ohm source; no decoupling hiding clamp admittance.'},indent=2)+'\n')
    print(json.dumps(result,indent=2));assert all(r['pass'] for r in result.values())
