"""Publish pad functional evaluation and preserve its simulation evidence."""
from pathlib import Path
import json,base64,hashlib,tarfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
def data(n):return json.loads((root/f'simulations/{n}.json').read_text())
char=data('pad-characterization');dc=data('pad-dc');pad=data('pad-pad-only');secondary=data('pad-secondary');smooth=data('pad-secondary-smooth');fine=data('pad-refinements')
assert len(char['cases'])==36
assert all(len(v)==84 for v in dc['cases'].values())
assert all(len(d['cases'])==5 for d in [pad,secondary,smooth])
assert len(fine['cases'])==3
assert all(r['status']=='complete' for d in [smooth,fine] for r in d['cases'].values())
pins=['BIAS','PREF','VRESET','BUF_low','BUF_high']
caps=[[r['pins'][p]['capacitance_F']*1e12 for r in char['cases'].values()] for p in pins]
leak=max(r['max_abs_rail_range_leakage_A'] for r in char['cases'].values())*1e9
nom=char['cases']['diode_typical_27C_3.3V']['pins']
fig,axs=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
lo=np.array([min(x) for x in caps]);hi=np.array([max(x) for x in caps]);mid=(lo+hi)/2
axs[0].errorbar(range(5),mid,yerr=[mid-lo,hi-mid],fmt='o',capsize=6,color='#146379');axs[0].set(xticks=range(5),xticklabels=pins,ylabel='Signal capacitance (pF)',title='Installed analog pad, 1 kHz\nDiode corners / −40…125 °C / 3.0…3.6 V');axs[0].tick_params(axis='x',rotation=25)
for i,(m,label) in enumerate([('pad-only','Pad'),('secondary','Pad + secondary')]):
 vals=[max(abs(r[k]) for r in dc['cases'][m].values()) for k in ['column_change_percent','buffer_change_percent']]
 axs[1].bar(np.arange(2)+(i-.5)*.32,vals,width=.32,label=label)
axs[1].set(xticks=range(2),xticklabels=['Column reference','Buffer reference'],ylabel='Maximum absolute change (%)',title='Core reference currents\n84 matched DC cases per candidate');axs[1].legend()
labels=[];vals=[]
for r in smooth['cases'].values():labels.append(f'{r["corner"]}\n{r["temp_C"]}°C\n{r["supply_V"]}V');vals.append(r['max_hold_error_mV'])
axs[2].bar(range(len(vals)),vals,color='#146379');axs[2].axhline(.5,color='#c55c13',ls='--',label='0.5 mV screen');axs[2].set(xticks=range(len(vals)),xticklabels=labels,ylabel='Maximum HOLD error (mV)',title='Pad + secondary protection\nFinite-transition ADC model');axs[2].legend();axs[2].tick_params(axis='x',labelsize=9)
for ax in axs:ax.grid(axis='y',alpha=.2)
asset=root/'docs/assets/pad-evaluation.png';fig.savefig(asset,dpi=160);plt.close(fig)
rows=''
for p in pins:
 a=[r['pins'][p] for r in char['cases'].values()]
 rows+=f'<tr><th>{p}</th><td>{nom[p]["voltage_V"]:.2f}</td><td>{min(x["capacitance_F"] for x in a)*1e12:.3f}–{max(x["capacitance_F"] for x in a)*1e12:.3f}</td><td>{max(abs(x["leakage_into_pad_A"]) for x in a)*1e9:.4f}</td></tr>'
worst=max(r['max_hold_error_mV'] for r in smooth['cases'].values());passes=sum(r['screen_pass'] for r in smooth['cases'].values())
refined=[r for k,r in fine['cases'].items() if k.startswith('secondary')][0]
coarse=next(r for r in smooth['cases'].values() if r['corner']==refined['corner'] and r['temp_C']==refined['temp_C'] and r['supply_V']==refined['supply_V'])
delta=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(coarse['samples'],refined['samples']))
switchdelta=[]
for k,r in fine['cases'].items():
 if k.startswith('pad-only'):
  old=next(x for x in pad['cases'].values() if x['corner']==r['corner'] and x['temp_C']==r['temp_C'] and x['supply_V']==r['supply_V'])
  if old['status']=='complete':switchdelta.append(max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(old['samples'],r['samples'])))
summary={'isolated_cases':36,'dc_cases_per_candidate':84,'secondary_finite_switch_pass':passes,'secondary_finite_switch_cases':5,'worst_hold_error_mV':worst,'refined_hot_hold_error_mV':refined['max_hold_error_mV'],'refined_hot_max_sample_change_mV':delta,'pad_only_matched_switch_max_sample_change_mV':max(switchdelta),'max_rail_range_leakage_nA':leak,'ideal_secondary_failed_cases':sum(r['status']!='complete' for r in secondary['cases'].values())}
(root/'simulations/pad-evaluation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
img=base64.b64encode(asset.read_bytes()).decode()
html=f'''<section id="pad-evaluation"><h2>Analog pad evaluation: leakage, bias and sampling</h2>
<p><b>Functional circuit candidate: {passes}/5 selected imaging cases pass with a finite-transition ADC model.</b> The installed <code>gf180mcu_fd_io__asig_5p0</code> was evaluated on BIAS, PREF, VRESET and BUF. The extracted sensor GDS is unchanged.</p>
<img src="data:image/png;base64,{img}" alt="Pad capacitance ranges, reference-current changes and selected imaging sampling errors">
<h3>Leakage and capacitance</h3><p>36 isolated-pad conditions cover three diode sections, four temperatures (−40, 27, 85, 125 °C) and three supplies (3.0, 3.3, 3.6 V). Signal capacitance is differential AC capacitance at 1 kHz with ideal AC-grounded supply rails; it excludes bond wires and metal extraction. The pad's rail MOS capacitor uses its typical section. Representative pin voltages are shown below; BUF endpoints are test points, not a guaranteed output range.</p>
<table><tr><th>Connection</th><th>Test voltage (V)</th><th>Capacitance range (pF)</th><th>Maximum |leakage| (nA)</th></tr>{rows}</table>
<p>The maximum modeled leakage anywhere in the 0-to-supply voltage sweeps is {leak:.4f} nA. At the representative BIAS voltage it is about 0.0605 nA, below the proposed 5 nA budget. These are model predictions, not guaranteed manufactured-pad leakage specifications.</p>
<h3>Candidate secondary protection</h3><p>Each pin uses a 100 Ω ideal series resistor, with a diode pair at the core side: 3.3 V N+/substrate and P+/well junctions, each 12 µm² area and 26 µm perimeter. For a physical implementation the resistor must become an appropriate poly resistor. The <a href="https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/analog.html">foundry documentation</a> calls for local secondary protection; the tested dimensions alone do not establish ESD robustness or thin-oxide protection.</p>
<p>All 84 DC conditions converge for each of the pad-only and pad-plus-secondary candidates. Relative to matching unpadded resistor-bias cases, the secondary candidate changes the column reference by at most {max(abs(r['column_change_percent']) for r in dc['cases']['secondary'].values()):.4f}% and the buffer reference by at most {max(abs(r['buffer_change_percent']) for r in dc['cases']['secondary'].values()):.4f}%. Actual current entering the core is measured after the protection network, excluding its leakage.</p>
<h3>Sampling and numerical checks</h3><p>Worst HOLD error across the five finite-switch secondary-protection cases: <b>{worst:.3f} mV</b>, compared with the 0.5 mV screen. The tests retain the generic 20 pF switched ADC sampling capacitor, 100 pF board load, 100 Ω board isolation resistor and bond-wire model. The old assumed pad capacitance is replaced with device models plus a separate 1 pF external allowance at each bias pin and at the output package node. VRESET remains an ideal ramped 2 V external source.</p>
<p class="note">All five secondary-protection runs with the original discontinuous ideal ADC switches failed with timestep-too-small errors. These failed decks and logs are retained. The successful runs replace the ADC switches with smooth conductance transitions (100 Ω on, 1 TΩ off; tanh control width 0.1 V over the existing 10 ns control edges). This is still a behavioral ADC load, not a selected ADC's transistor model.</p>
<p>Two matched pad-only controls change sampled output by at most {max(switchdelta):.5f} mV when switching to the finite-transition model. The hot secondary case rerun at 0.05 µs and tighter relative tolerance gives {refined['max_hold_error_mV']:.3f} mV HOLD error and changes sampled output by at most {delta:.5f} mV.</p>
<p><b>Decision:</b> retain this analog-pad/protection topology as a candidate for physical implementation. Next resolve the pad-ring rails and clamps, digital-input voltage compatibility, realizable poly resistor and local diode layout, then rerun pad-inclusive DRC/LVS and extraction. ESD pulses, clamp effectiveness, supply inductance/coupling, powered-input/unpowered-core cases, resistor process variation, photoleakage and assembly contamination are not qualified here.</p>
<p><a href="pad-evaluation.md">Reproduction and evidence</a>.</p></section>'''
(root/'docs/pad-evaluation.html').write_text(html)
print(json.dumps(summary,indent=2))
# Preserve decks, logs and waveforms as a reviewable checkpoint, including failures.
files=sorted(p for p in (root/'build/pad-evaluation').rglob('*') if p.is_file() and p.name!='success.sha256')
files += sorted((root/'simulations').glob('pad-*.json'))
files += [root/p for p in ['scripts/evaluate-pads.py','scripts/check-pad-refinements.py','scripts/report-pad-evaluation.py','scripts/bias-reference.py','scripts/run-tools.sh','circuits/board-bias.spice','circuits/bias-dc-template.spice','circuits/bias-scan-template.spice','checkpoints/integrated/pex/sensor_reduced.spice','checkpoints/pad-evaluation/analog-pad.spice','docs/pad-evaluation.md','docs/pad-evaluation.html']]
files += [root/'simulations/bias-reference-dc.json']
pdk=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')
provenance={'pdk_model_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pdk.glob('*') if p.is_file() and p.suffix in ['.spice','.ngspice']},'gds_sha256':hashlib.sha256((root/'checkpoints/integrated/sensor_3x3.gds').read_bytes()).hexdigest(),'scope':'Functional SPICE evaluation only; no new physical pad implementation or ESD qualification.'}
prov=root/'checkpoints/pad-evaluation/provenance.json';prov.write_text(json.dumps(provenance,indent=2)+'\n');files.append(prov)
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(root/'checkpoints/pad-evaluation/evidence.tar.gz','w:gz',compresslevel=3) as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(root)))
(root/'checkpoints/pad-evaluation/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Archived',len(files),'evidence files')
