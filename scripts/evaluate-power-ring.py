"""Foundry ring models plus extracted power-lead RC; ring metal RC stays separate."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];adapter='--adapter' in sys.argv;practical='--practical' in sys.argv;fine='--fine' in sys.argv
out=ROOT/('build/power-ring/electrical'+('-adapter' if adapter else '')+('-practical' if practical else '')+('-fine' if fine else ''));out.mkdir(exist_ok=True)
pdk=Path('/foss/pdks/gf180mcuD');source=pdk/'libs.ref/gf180mcu_fd_io/spice/gf180mcu_fd_io.spice'
s=source.read_text();models='\n\n'.join(re.search(r'(?ms)^\.SUBCKT gf180mcu_fd_io__'+name+r' .*?^\.ENDS',s)[0] for name in ['dvdd','dvss','cor','fill10'])+'\n'
(out/'ring-models.spice').write_text(models)
ref=(ROOT/'build/power-ring/power_ring.spice').read_text().replace(str(source),str(out/'ring-models.spice'))
(out/'ring-reference.spice').write_text(ref)
leads=(ROOT/'build/power-ring/leads/power_leads_rc.spice').read_text()
assert len(re.findall(r'(?m)^R',leads))==2
lead_model=re.sub(r'w_\w+#','SUB',leads).replace('VDD_RING VSS_RING\n','VDD_RING VSS_RING SUB\n')
(out/'power-leads-sim.spice').write_text(lead_model)
res={}
for line in leads.splitlines():
 if line.startswith('R'):
  t=line.split();res['VDD' if 'VDD' in t[1] else 'VSS']=float(t[3])
results={}
for name,temp,v,dio in [('nominal',27,3.3,'diode_typical'),('hot',125,3.,'diode_ff')]:
 if '--hot-only' in sys.argv and name!='hot':continue
 folder=out/name;folder.mkdir(exist_ok=True)
 lib=pdk/'libs.tech/ngspice/sm141064.ngspice'
 deck=f'''Physical power-ring load test: schematic macro internals + extracted lead RC
.include {pdk}/libs.tech/ngspice/design.ngspice
.lib {lib} typical
.lib {lib} {dio}
.lib {lib} res_ss
.lib {lib} moscap_ss
.include {out}/ring-reference.spice
.include {out}/power-leads-sim.spice
.temp {temp}
.options gmin=1e-17 abstol=1e-12 reltol=5e-5 chgtol=1e-16 trtol=3 method=gear
Vsource SOURCE 0 PWL(0 0 1m {v})
Rboard SOURCE LEAD .5
Lboard LEAD RING_VDD 2n
Rdec RING_VDD DCAP .1
Ldec DCAP CAP 1n
Cdec CAP 0 100n
Xring RING_VDD 0 power_ring
Xlead CORE_VDD CORE_VSS RING_VDD 0 CORE_VSS power_leads
Rload CORE_VDD CORE_VSS 33k
Istep CORE_VDD CORE_VSS PULSE(0 100u 1.25m 10n 10n 18u 60u)
.control
set num_threads=1
set wr_singlescale
set wr_vecnames
save v(RING_VDD) v(CORE_VDD) v(CORE_VSS) i(Vsource)
tran .1u 1.5m uic
wrdata {folder}/wave.txt v(RING_VDD) v(CORE_VDD) v(CORE_VSS) i(Vsource)
quit
.endc
.end
'''
 if practical:deck=deck.replace('reltol=5e-5 chgtol=1e-16','reltol=1e-4 chgtol=1e-14')
 if fine:deck=deck.replace('tran .1u','tran .05u')
 if adapter:
  deck=deck.replace('Xring RING_VDD 0 power_ring','Ering DRIVE 0 RING_VDD 0 1\nVring DRIVE RAIL 0\nFring RING_VDD 0 Vring 1\nXring RAIL 0 power_ring')
  deck=deck.replace('v(CORE_VSS) i(Vsource)', 'v(CORE_VSS) i(Vsource) v(RAIL) i(Vring) i(Ering)')
 key=hashlib.sha256((deck+models+ref+lead_model).encode()).hexdigest();stamp=folder/'success.sha256'
 if not stamp.exists() or stamp.read_text()!=key:
  (folder/'testbench.spice').write_text(deck)
  with (folder/'run.log').open('w') as log:
   try:
    p=subprocess.run(['ngspice','-b',str(folder/'testbench.spice')],stdout=log,stderr=subprocess.STDOUT,timeout=900,env={**os.environ,'SPICE_USERINIT_DIR':str(ROOT/'checkpoints/pad-closure/ngspice-init')})
   except subprocess.TimeoutExpired:
    (folder/'status.json').write_text(json.dumps({'status':'timeout','timeout_s':900,'scope':'No completed waveform; no pass claimed'},indent=2)+'\n')
    raise
  text=(folder/'run.log').read_text();assert p.returncode==0 and not re.search(r'aborted|timestep too small|^Error',text,re.M|re.I),text[-1000:]
 a=np.loadtxt(folder/'wave.txt',skiprows=1);assert np.isfinite(a).all() and a[-1,0]>=.0015-1e-12
 stamp.write_text(key)
 (folder/'status.json').write_text(json.dumps({'status':'completed','waveform_end_s':float(a[-1,0])},indent=2)+'\n')
 active=a[:,0]>=.0012;core=a[:,2]-a[:,3];startup=(a[:,0]>=.00119)&(a[:,0]<=.0012)
 r={'temp_C':temp,'supply_V':v,'max_active_core_supply_drop_mV':float(max(v-core[active])*1000),
    'max_active_ground_rise_mV':float(max(a[active,3])*1000),
    'max_source_current_mA':float(max(-a[:,4])*1000),
    'startup_supply_error_pct':float(max(abs(core[startup]/v-1))*100),
    'rail_screen_pass':bool(max(abs(core[active]/v-1))<.01 and max(abs(core[startup]/v-1))<.01)}
 if adapter:
  r['interface_rail_difference_V']=float(np.max(abs(a[:,1]-a[:,5])))
  r['interface_current_balance_A']=float(np.max(abs(a[:,6]+a[:,7])))
  assert r['interface_rail_difference_V'] < 1e-7 and r['interface_current_balance_A'] < 1e-12
 results[name]=r;print(name,r,flush=True)
summary={'cases':results,'lead_R_ohm':res,'clamps':10,'filler_instances':125,
 'scope':'Installed schematic models for ring macro devices plus Magic RC from isolated actual connecting wires. '
 'Ring metal resistance and full assembly coupling are NOT included in this test. '
 'Substrate capacitances of the isolated wires reference core ground. 33k core load plus 100uA load pulses; not a camera-image scan.',
 'adapter':adapter,'practical_tolerance':practical,'fine_step':fine,'source_model_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(ROOT/('simulations/power-ring-load'+('-adapter' if adapter else '')+('-practical' if practical else '')+('-fine' if fine else '')+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
assert all(r['rail_screen_pass'] for r in results.values())
