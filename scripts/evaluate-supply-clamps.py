"""Normal-voltage DC/startup evaluation of the foundry supply-pad clamp pair.
This is not an HBM/CDM or thin-oxide ESD qualification model.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,re,json,hashlib,itertools,os
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'build/supply-clamps';out.mkdir(exist_ok=True)
pdk=Path('/foss/pdks/gf180mcuD');lib=pdk/'libs.tech/ngspice/sm141064.ngspice'
source=pdk/'libs.ref/gf180mcu_fd_io/spice/gf180mcu_fd_io.spice';text=source.read_text()
checkpoint=root/'checkpoints/pad-closure';checkpoint.mkdir(exist_ok=True)
parts=[re.search(r'(?ms)^\.SUBCKT gf180mcu_fd_io__'+name+r' .*?^\.ENDS',text)[0] for name in ['dvdd','dvss']]
model=text[:text.index('.SUBCKT')]+ '\n\n'.join(parts)+'\n';modelpath=checkpoint/'supply-pad-models.spice';modelpath.write_text(model)
(checkpoint/'clamp-model-provenance.json').write_text(json.dumps({'source_path':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256(model.encode()).hexdigest(),'mos_section':'typical; installed high-voltage MOS models are not independently swept by resistor/capacitor/diode section changes'},indent=2)+'\n')
def header(res,cap,dio,t,v):
 return f'Supply-pad clamp pair: normal-voltage characterization\n.include {pdk}/libs.tech/ngspice/design.ngspice\n.lib {lib} typical\n.lib {lib} {res}\n.lib {lib} {cap}\n.lib {lib} {dio}\n.include {modelpath}\n.temp {t}\n.options gmin=1e-17 abstol=1e-15 reltol=1e-5 method=gear\nVdd VDD 0 {v}\nVbranch1 VDD VP 0\nVbranch2 VDD VG 0\nXvdd VP 0 0 gf180mcu_fd_io__dvdd\nXvss VG 0 VG gf180mcu_fd_io__dvss\n'
def control(folder,analysis,vectors):return f'.control\nset num_threads=1\nset wr_vecnames\nset wr_singlescale\n{analysis}\nwrdata {folder}/wave.txt {vectors}\nquit\n.endc\n.end\n'
init=checkpoint/'ngspice-init';init.mkdir(exist_ok=True);(init/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
def run(folder,s):
 folder.mkdir(parents=True,exist_ok=True);(folder/'testbench.spice').write_text(s)
 with (folder/'run.log').open('w') as log:p=subprocess.run(['ngspice','-b',str(folder/'testbench.spice')],stdout=log,stderr=subprocess.STDOUT,timeout=120,env={**os.environ,'SPICE_USERINIT_DIR':str(init)})
 log=(folder/'run.log').read_text()
 if p.returncode or re.search(r'^Error|aborted|timestep too small',log,re.M|re.I):raise RuntimeError(str(folder)+' '+log[-1000:])
 a=np.loadtxt(folder/'wave.txt',skiprows=1,ndmin=2);assert np.isfinite(a).all();return a
def key(case):return '_'.join(map(str,case))
def dc(case):
 res,cap,dio,t,v=case;folder=out/'dc'/key(case);a=run(folder,header(*case)+control(folder,'op','i(Vdd) i(Vbranch1) i(Vbranch2) v(xvdd.n4)'))[0]
 return key(case),dict(res=res,cap=cap,diode=dio,temp_C=t,supply_V=v,total_leakage_A=float(-a[1]),vdd_pad_leakage_A=float(a[2]),vss_pad_leakage_A=float(a[3]),clamp_gate_V=float(a[4]))
def startup(case):
 res,cap,dio,t,v,ramp=case;folder=out/'startup'/key(case);end=ramp+200
 s=header(*case[:5]).replace(f'Vdd VDD 0 {v}',f'Vdd VDD 0 PWL(0 0 {ramp}u {v})')
 a=run(folder,s+control(folder,f'tran .02u {end}u uic','v(VDD) i(Vdd) v(xvdd.n4) v(xvss.n4)'))
 assert a[-1,0]>=end*1e-6-1e-12
 tail=a[:,0]>=(end-10)*1e-6;amps=-a[:,2];i=int(np.argmax(amps))
 ref=DC[key(case[:5])]['total_leakage_A'];settle=float(np.max(abs(amps[tail]-ref)));gate=float(np.max(abs(a[tail,3:5])))
 return key(case),dict(res=res,cap=cap,diode=dio,temp_C=t,supply_V=v,ramp_us=ramp,peak_supply_A=float(amps[i]),peak_time_s=float(a[i,0]),max_clamp_gate_V=float(np.max(a[:,3:5])),tail_current_error_A=settle,tail_gate_V=gate,settled_at_200us=bool(settle<max(1e-9,.01*abs(ref)) and gate<.1),total_charge_C=float(np.trapezoid(amps,a[:,0])))
if __name__=='__main__':
 cases=list(itertools.product(['res_typical','res_ff','res_ss'],['moscap_typical','moscap_ff','moscap_ss'],['diode_typical','diode_ff','diode_ss'],[-40,27,85,125],[3.0,3.3,3.6]))
 DC=dict(ThreadPoolExecutor(max_workers=4).map(dc,cases));(root/'simulations/supply-clamp-dc.json').write_text(json.dumps({'cases':DC,'scope':'One foundry VDD pad and one VSS pad, shared 3.0–3.6V rail. Independent resistor/capacitor/diode corners; high-voltage MOS typical.'},indent=2)+'\n');print('DC',len(DC),'max pair leakage',max(v['total_leakage_A'] for v in DC.values()),flush=True)
 tasks=[('res_typical','moscap_typical','diode_typical',27,v,r) for v in [3.0,3.3,3.6] for r in [.01,1,100,1000]]
 tasks +=[(res,cap,'diode_ff',t,3.6,r) for res,cap in [('res_ff','moscap_ff'),('res_ss','moscap_ss')] for t in [-40,125] for r in [.01,1,1000]]
 rows={}
 for name,r in ThreadPoolExecutor(max_workers=4).map(startup,tasks):
  rows[name]=r;(root/'simulations/supply-clamp-startup.json').write_text(json.dumps({'cases':rows,'scope':'Ideal voltage-source ramp; peak current includes charging current, not only clamp channel current. No supply impedance, no ESD pulse or overvoltage qualification. 200us post-ramp settling screen.'},indent=2)+'\n')
 print('Startup',len(rows),'settled',sum(r['settled_at_200us'] for r in rows.values()),flush=True)
