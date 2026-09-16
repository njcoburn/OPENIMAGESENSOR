"""Publish the measured pad checks, including failed numerical trials."""
from pathlib import Path
import json,base64,hashlib,tarfile,xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
def read(name):return json.loads((root/'simulations'/f'{name}.json').read_text())['cases']
dc=read('supply-clamp-dc');startup=read('supply-clamp-startup');strict=read('clamp-supply');practical=read('clamp-supply-practical');original_imaging=read('clamp-imaging');practical_imaging=read('clamp-imaging-practical');charge_imaging=read('clamp-imaging-charge');imaging=read('clamp-imaging-one-frame')
assert (len(dc),len(startup),len(strict),len(practical),len(imaging))==(324,24,18,18,4)
assert len(original_imaging)==len(practical_imaging)==len(charge_imaging)==4
checks={}
for group in ['wafer-space','density','antenna']:
 p=root/'build/pad-closure'/f'interface-{group}.lyrdb'
 checks[group]=len(ET.parse(p).findall('.//items/item'))
 assert checks[group]==0
nom=dc['res_typical_moscap_typical_diode_typical_27_3.3']['total_leakage_A']*1e9
worst=max(r['total_leakage_A'] for r in dc.values())*1e9
soft=[r for r in practical.values() if r['ramp_us']==1000]
complete=[r for r in soft if r.get('status')!='simulation_failed']
summary={'rule_selection':'all,-antenna,-density,-cup','drc_markers':checks,'previous_unfiltered_CUP3':87,'full_die_precheck':False,'nominal_pair_leakage_nA':nom,'max_pair_leakage_nA':worst,'dc_count':len(dc),'ideal_startup_count':len(startup),'ideal_startup_settled':sum(r['settled_at_200us'] for r in startup.values()),'strict_supply_failed':sum(r.get('status')=='simulation_failed' for r in strict.values()),'practical_supply_failed':sum(r.get('status')=='simulation_failed' for r in practical.values()),'soft_start_cases':len(soft),'soft_start_settled':sum(r['settled_at_200us'] for r in soft),'soft_start_peak_source_A':max((r['peak_source_current_A'] for r in complete),default=None),'soft_start_max_drop_V':max((r['peak_source_to_rail_drop_V'] for r in complete),default=None),'original_imaging_failed':sum(not r['screen_pass'] for r in original_imaging.values()),'practical_three_frame_passed':sum(r['screen_pass'] for r in practical_imaging.values()),'charge_three_frame_passed':sum(r['screen_pass'] for r in charge_imaging.values()),'first_frame_passed':sum(r['screen_pass'] for r in imaging.values()),'esd_qualified':False,'gds_sha256':{}}
for path,expected in [('checkpoints/integrated/sensor_3x3.gds','8a2183fd85d5a6b81bcaceb10eeb00f906018574902c4bdfe2199a5c41b222b7'),('checkpoints/pad-layout/analog_pad_interface.gds','3517bdda5385d7037ce8158520db6ab9d38e220ffc478867a3a5a6addcff3ecf')]:
 actual=hashlib.sha256((root/path).read_bytes()).hexdigest();assert actual==expected;summary['gds_sha256'][path]=actual
deltas=[]
for key,r in imaging.items():
 if key.startswith('with-clamps/') and r.get('status')=='complete':
  control=imaging[key.replace('with-clamps/','matched-control/',1)]
  if control.get('status')=='complete':
   deltas.append(max(abs(a['output_V']-b['output_V'])*1e6 for a,b in zip(r['samples'],control['samples'])))
summary['first_frame_max_matched_output_difference_uV']=max(deltas,default=None)
fig,axs=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
for v in [3.,3.3,3.6]:
 rows=[r for r in dc.values() if r['supply_V']==v]
 temps=sorted({r['temp_C'] for r in rows})
 axs[0].semilogy(temps,[max(r['total_leakage_A'] for r in rows if r['temp_C']==t)*1e9 for t in temps],'o-',label=f'{v:g} V')
axs[0].set(xlabel='Temperature (°C)',ylabel='Pair leakage (nA)',title='Worst passive/diode combination\nHV MOS model: typical');axs[0].legend()
for ramp in [1,1000]:
 p=root/'build/supply-clamps/startup'/f'res_typical_moscap_typical_diode_typical_27_3.3_{ramp}'/'wave.txt'
 a=np.loadtxt(p,skiprows=1);axs[1].plot(a[:,0]*1e6/ramp,a[:,3],label=f'{ramp} µs ramp')
axs[1].set(xlabel='Time / ramp duration',ylabel='Main clamp gate (V)',title='Ideal 3.3 V source, 27°C',xlim=(0,2));axs[1].legend()
labels=[];values=[];colors=[]
for key,r in sorted(imaging.items()):
 labels.append(('Pair' if key.startswith('with-clamps') else 'Control')+f"\n{r['temp_C']}°C / {r['supply_V']} V")
 values.append(r.get('max_hold_error_mV',float('nan')));colors.append('#2196a6' if key.startswith('with-clamps') else '#9ca3af')
axs[2].bar(range(len(values)),values,color=colors);
for i,value in enumerate(values):
 if not np.isfinite(value):axs[2].text(i,.04,'Incomplete',ha='center',rotation=90,color='red')
axs[2].set_xticks(range(len(values)),labels);axs[2].axhline(.5,color='red',ls='--',label='0.5 mV screen');axs[2].set(ylabel='Worst sampling error (mV)',title='First camera frame, 1 ms ideal ramp');axs[2].legend()
for ax in axs:ax.grid(alpha=.2)
fig.suptitle('Supply-pad evaluation — normal-voltage simulation, not ESD qualification')
asset=root/'docs/assets/pad-closure.png';fig.savefig(asset,dpi=140);plt.close(fig)
image='data:image/png;base64,'+base64.b64encode(asset.read_bytes()).decode()
diagram=(root/'docs/assets/supply-pad-plan.svg').read_text()
rows=''
for key,r in sorted(imaging.items()):
 rows+=f"<tr><td>{'With pair' if key.startswith('with-clamps') else 'Matched control'}</td><td>{r['temp_C']} °C / {r['supply_V']} V</td><td>{r.get('max_hold_error_mV',float('nan')):.4f} mV</td><td>{'Pass' if r['screen_pass'] else 'Failed; inspect log'}</td></tr>"
finite=''
for key,r in sorted(practical.items()):
 finite+=f"<tr><td>{r['temp_C']} °C</td><td>{r['source_R_ohm']} Ω</td><td>{r['ramp_us']} µs</td><td>{r.get('peak_source_current_A',float('nan'))*1e3:.4g} mA</td><td>{'Settled' if r['settled_at_200us'] else 'Unresolved'}</td></tr>"
section=f'''<section id="pad-closure"><h2>Pad DRC configuration and supply-clamp evaluation</h2>
<p><strong>Published rule-selection checks: zero main, density and antenna markers.</strong> The unchanged single-pad interface passes the selection used by the <a href="https://github.com/wafer-space/gf180mcu-precheck/blob/main/precheck.py">wafer.space precheck</a> and <a href="https://github.com/wafer-space/gf180mcu-project-template/blob/main/librelane/config.yaml">project template</a>: <code>all,-antenna,-density,-cup</code>, with density and antenna separate. The earlier unfiltered report still has 87 CUP.3 markers. This resolves the configuration discrepancy; CUP.3 itself has not passed. This coupon has not undergone a full slot-sized die precheck or bonding qualification.</p>
<h3>Candidate power domain</h3>{diagram}
<p>One foundry <code>dvdd</code> plus one <code>dvss</code> pad, with core and IO stripes sharing 3.3 V AVDD/AVSS. This is an electrical candidate; a full ring is not routed. <a href="https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/power.html">Supply and corner pads contain clamps</a>; adding more changes startup loading. The pinned OCD split-voltage core-supply schematic also uses 6 V clamp devices, so changing libraries alone does not establish thin-oxide protection.</p>
<h3>Measured simulation results</h3>
<ul><li>324 DC cases: nominal pair leakage <strong>{nom:.3f} nA</strong>; maximum <strong>{worst:.2f} nA</strong> across 3.0–3.6 V, −40 to 125°C, and resistor/MOS-capacitor/diode sections. HV MOS remains typical, so this is not full transistor PVT qualification.</li>
<li>24 ideal-source startup cases: {summary['ideal_startup_settled']} settled within 200 µs after the ramp. Fast ramps trigger large modeled clamp current; amp-scale ideal-source peaks are diagnostics, not hardware current ratings.</li>
<li>Finite-source tests: 0.5/5 Ω, 100 nF, 33 kΩ load. Original strict tolerances failed in {summary['strict_supply_failed']}/18 cases; those logs are retained. Practical tolerances (absolute current 1 pA, relative 0.01%) failed in {summary['practical_supply_failed']}/18 cases. Of six 1 ms cases, {summary['soft_start_settled']} settled. This is a source-impedance sensitivity model, not a selected regulator.</li>
<li>Original camera-plus-clamp runs reached the 600 s time limit; original matched controls passed. Separate three-frame tolerance experiments are retained ({summary['practical_three_frame_passed']}/4 practical-current-tolerance screens; {summary['charge_three_frame_passed']}/4 charge-tolerance screens). The bounded first-frame comparison retains the original electrical and numerical settings: {summary['first_frame_passed']}/4 pass the existing 0.5 mV sampling, brightness ordering and 1% reference-startup screens. This first-frame result does not establish three-frame clamp repeatability. Both variants use identical compatibility settings, a 1 ms ideal ramp and 200 µs post-ramp reset hold. Supply-impedance checks are separate.</li></ul>
<img src="{image}" alt="Clamp leakage, startup gate response and matched camera sampling error" style="width:100%">
<table><thead><tr><th>Configuration</th><th>Condition</th><th>Worst sampling error</th><th>Screen</th></tr></thead><tbody>{rows}</tbody></table>
<details><summary>Finite-source results, practical tolerances</summary><table><thead><tr><th>Temperature</th><th>Source R</th><th>Ramp</th><th>Peak source current</th><th>200 µs wait</th></tr></thead><tbody>{finite}</tbody></table><p>Source current includes 100 nF charging and the 33 kΩ load. Failed or incomplete simulations are unresolved, not hardware failures or passes.</p></details>
<h3>Simulator configuration and remaining work</h3>
<p>The library's multi-finger devices require width-per-finger binning: local <code>ngbehavior=hsa</code> and <code>wnflag=1</code>, following the <a href="https://ngspice.sourceforge.io/docs/ngspice-manual.pdf">ngspice manual</a>. No PDK geometry or transistor sizing was changed. Original bin-selection failures are retained.</p>
<p><strong>Use 1 ms soft-start as a candidate, with reset held until the rail is stable.</strong> It is not a characterized minimum ramp time. The long coupled camera/clamp transient remains a numerical verification issue. Resolve that before relying on multi-frame results, then check a selected board supply and complete pad-ring connectivity/extraction. Thin-oxide transient voltage, HBM/CDM, pulse heating and assembly qualification still require accepted stress evidence; normal-voltage SPICE and DRC/LVS do not establish ESD protection.</p>
<p>Reproduce using <code>check-pad-wafer-space.sh</code>, <code>evaluate-supply-clamps.py</code>, <code>check-clamp-supply.py</code>, <code>check-clamp-supply-practical.py</code>, <code>check-clamp-imaging.py</code>, <code>check-clamp-imaging-practical.py</code>, <code>check-clamp-imaging-charge.py</code>, <code>check-clamp-imaging-one-frame.py</code>, then <code>report-pad-closure.py</code> and <code>build-overview.py</code> inside the pinned tools container. Sources, decks, logs and waveforms are checkpointed with hashes.</p></section>'''
(root/'docs/pad-closure.html').write_text(section)
(root/'simulations/pad-closure-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
# Archive raw evidence plus direct report inputs; prior core/local-pad dependencies retain their own checkpoints.
paths=set()
for folder in ['build/pad-closure','build/supply-clamps','build/clamp-supply','build/clamp-supply-practical','build/clamp-imaging','build/clamp-imaging-practical','build/clamp-imaging-charge','build/clamp-imaging-one-frame']:
 paths.update(p for p in (root/folder).rglob('*') if p.is_file())
cp=root/'checkpoints/pad-closure'
paths.update(p for p in cp.rglob('*') if p.is_file() and p.name not in ['evidence.tar.gz','manifest.json'])
for pattern in ['simulations/*clamp*.json','simulations/pad-closure-verification.json','scripts/*clamp*.py','scripts/report-pad-closure.py','scripts/check-pad-wafer-space.sh','circuits/sensor-supply-pads.spice','docs/pad-closure.*','docs/assets/pad-closure.png','docs/assets/supply-pad-plan.svg']:
 paths.update(root.glob(pattern))
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
with tarfile.open(cp/'evidence.tar.gz','w:gz',compresslevel=3) as tar:
 for p in sorted(paths):tar.add(p,arcname=str(p.relative_to(root)))
with tarfile.open(cp/'evidence.tar.gz','r:gz') as tar:
 for name,digest in manifest.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
(cp/'manifest.json').write_text(json.dumps({'files':manifest,'archive_sha256':hashlib.sha256((cp/'evidence.tar.gz').read_bytes()).hexdigest(),'dependencies':summary['gds_sha256']},indent=2)+'\n')
print(json.dumps(summary,indent=2));print('Archived and verified',len(manifest),'files')
