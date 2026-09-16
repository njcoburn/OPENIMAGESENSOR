"""Report verified local protection separately from unresolved primary-pad DRC."""
from pathlib import Path
import json,re,hashlib,base64,shutil,tarfile,xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];b=root/'build/pad-layout';dest=root/'checkpoints/pad-layout';dest.mkdir(exist_ok=True)
def markers(n):return sorted((i.findtext('category'),tuple(v.text for v in i.findall('./values/value'))) for i in ET.parse(b/(n+'-klayout.lyrdb')).findall('.//items/item'))
def drc(n):return int(re.search(r'(?:SECONDARY|INTERFACE)_DRC_COUNT=(\d+)',(b/(n+'-magic.log')).read_text())[1])
def lvs(n):return 'Circuits match uniquely.' in (b/(n+'-lvs.log')).read_text()
assert drc('secondary')==0 and not markers('secondary') and lvs('secondary')
assert drc('interface')==0 and lvs('interface')
assert len(markers('stock-pad'))==87 and markers('stock-pad')==markers('interface')
im=json.loads((root/'simulations/pad-layout-imaging.json').read_text());dc=json.loads((root/'simulations/pad-layout-dc.json').read_text());fine=json.loads((root/'simulations/pad-layout-refinement.json').read_text())['result']
assert len(im['cases'])==5 and all(r['screen_pass'] for r in im['cases'].values()) and fine['screen_pass']
assert len(dc['cases'])==36
coarse=next(v for k,v in im['cases'].items() if k.startswith('res_ss/typical_125'))
delta=max(abs(a['output_V']-c['output_V'])*1000 for a,c in zip(fine['samples'],coarse['samples']))
summary={'local_magic_drc':0,'local_klayout_drc':0,'local_lvs_unique':True,'wrapper_magic_drc':0,'wrapper_lvs_unique':True,'wrapper_klayout_drc':87,'stock_pad_klayout_drc':87,'inherited_markers_exact_match':True,'dc_cases':36,'selected_imaging_pass':5,'worst_hold_error_mV':max(r['max_hold_error_mV'] for r in im['cases'].values()),'fine_hold_error_mV':fine['max_hold_error_mV'],'fine_sample_change_mV':delta,'nominal_resistance_ohm':dc['resistor_ohm']['res_typical_27'],'resistance_range_ohm':[min(dc['resistor_ohm'].values()),max(dc['resistor_ohm'].values())],'gds_sha256':{n:hashlib.sha256((b/n).read_bytes()).hexdigest() for n in ['analog_secondary.gds','analog_pad_interface.gds']},'scope':'Local physical protection cell verified; full wrapper has 87 inherited CUP.3 findings. No supply clamp/full ring or ESD qualification. Simulations use extracted local capacitance and PDK poly resistor, schematic primary-pad model; metal wire resistance omitted.'}
(root/'simulations/pad-layout-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(11,4.7),layout='constrained')
for res,c in [('res_ff','#218355'),('res_typical','#146379'),('res_ss','#c55c13')]:
 ts=[-40,27,85,125];axes[0].plot(ts,[dc['resistor_ohm'][f'{res}_{t}'] for t in ts],'o-',label=res,color=c)
axes[0].set(xlabel='Temperature (°C)',ylabel='Resistance (Ω)',title='Physical poly resistor: 3.2 × 1 µm');axes[0].legend()
labels=[];vals=[]
for k,r in im['cases'].items():labels.append(f'{k.split("/")[0]}\n{r["corner"]} / {r["temp_C"]}°C\n{r["supply_V"]} V');vals.append(r['max_hold_error_mV'])
axes[1].bar(range(5),vals,color='#146379');axes[1].axhline(.5,ls='--',color='#c55c13',label='0.5 mV screen');axes[1].set(xticks=range(5),xticklabels=labels,ylabel='Maximum HOLD error (mV)',title='Physical devices + local extracted C');axes[1].tick_params(axis='x',labelsize=8);axes[1].legend()
for ax in axes:ax.grid(axis='y',alpha=.2)
fig.savefig(root/'docs/assets/pad-layout-performance.png',dpi=160);plt.close(fig)
def image(n):return 'data:image/png;base64,'+base64.b64encode((root/'docs/assets'/n).read_bytes()).decode()
html=f'''<section id="pad-layout"><h2>Physical analog interface: local protection verified</h2>
<p><b>The local protection cell passes Magic DRC, the full installed KLayout deck and unique Netgen LVS.</b> The combined pad wrapper also matches LVS and is Magic-clean, but retains 87 KLayout CUP.3 findings inherited from the untouched library bond pad. This is a single-interface test coupon, not a complete pad ring or ESD-qualified sensor.</p>
<div class="grid"><figure><img style="max-height:650px;object-fit:contain" src="{image('pad-interface-layout.png')}" alt="Actual single analog-pad wrapper layout"><figcaption>Primary pad below; routed local protection above. Supply stripes are joined into one sensor voltage domain. No supply clamp or complete ring is included.</figcaption></figure><figure><img src="{image('pad-secondary-layout.png')}" alt="Local poly resistor and two protection diodes with routed supplies"><figcaption>Local functional geometry before density fill: poly resistor on the left, N+/substrate diode in the middle, P+/Nwell diode on the right. The checked density-filled cell is 31 × 22 µm. Each junction is 1 × 12 µm with 26 µm perimeter.</figcaption></figure></div>
<h3>Replacing the ideal resistor</h3><p>The PDK poly device is {summary['nominal_resistance_ohm']:.2f} Ω nominal, with a tested range of {summary['resistance_range_ohm'][0]:.2f}–{summary['resistance_range_ohm'][1]:.2f} Ω. This first physical candidate is accepted for further evaluation on its simulated performance; it is not a 100 Ω device. Thirty-six DC cases cover three resistor corners, four temperatures and three supplies with typical MOS/diode models.</p>
<img src="{image('pad-layout-performance.png')}" alt="Resistor process-temperature curves and physical protection sampling checks">
<p>All five selected imaging cases pass. Worst HOLD error: <b>{summary['worst_hold_error_mV']:.3f} mV</b> against the 0.5 mV screen. The finer hot check gives {fine['max_hold_error_mV']:.3f} mV and changes sampled output by at most {delta:.5f} mV. The ADC retains the finite-transition behavioral model from the prior evaluation.</p>
<h3>What was extracted</h3><p>The local physical resistor and both junctions are retained, with wiring and floating-fill capacitance reduced at zero net charge. The protected CORE node has about 11.46 fF total local terminal capacitance. Metal wiring resistance and full primary-pad/ring parasitics are not included; the primary pad uses its library device model. The existing sensor core GDS is unchanged.</p>
<h3>Remaining pad-ring decision</h3><p class="note">The full rule deck reports exactly the same 87 CUP.3 slot-spacing markers on the stock pad and on the combined wrapper. None have been waived. The library describes a non-CUP pad; the flagged checks are circuit-under-pad rules. Bonding choice and the accepted rule configuration must be resolved before claiming complete-interface DRC closure. The new routing adds no findings in this comparison.</p>
<p>The wrapper's original signal/ground crossing was corrected by changing metal level. Hierarchical extraction is used because a flat export produced an incorrect diode-perimeter unit; independent assertions now verify 26 µm perimeter and 12 µm² area. Raw reports and the failed first wrapper are preserved.</p>
<p>Next: resolve the non-CUP bond-pad rule applicability with the shuttle/assembly requirements; choose and evaluate supply clamps and digital-input voltage domains; then build the complete ring and perform full pad-inclusive extraction. Thin-oxide ESD protection is not established by these DRC/LVS and functional simulation results. <a href="pad-layout.md">Reproduction, source references and limits</a>.</p></section>'''
(root/'docs/pad-layout.html').write_text(html)
for name in ['analog_secondary.gds','secondary-functional.gds','analog_pad_interface.gds','secondary_extracted.spice','interface_extracted.spice','secondary_pex.spice','secondary-capacitance.json','secondary-magic.log','secondary-lvs.log','secondary-klayout.lyrdb','interface-magic.log','interface-lvs.log','interface-klayout.lyrdb','stock-pad-klayout.lyrdb']:
 shutil.copyfile(b/name,dest/name)
files=[p for p in b.rglob('*') if p.is_file() and p.suffix in ['.spice','.log','.gds','.lyrdb','.json']]
files += [p for p in (root/'build/pad-layout-sim').rglob('*') if p.is_file() and p.name!='success.sha256']
files += list((root/'simulations').glob('pad-layout-*.json'))
files += [root/p for p in ['layout/pad-primitives.tcl','layout/pad-interface.py','layout/check-pad-secondary.tcl','layout/check-pad-interface.tcl','layout/extract-pad-secondary.tcl','circuits/analog-secondary.spice','circuits/analog-pad-interface.spice','scripts/build-pad-interface.sh','scripts/reduce-pad-secondary.py','scripts/simulate-pad-layout.py','scripts/refine-pad-layout.py','scripts/report-pad-layout.py','scripts/render-pad-layout.py','docs/pad-layout.md','docs/pad-layout.html']]
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(dest/'evidence.tar.gz','w:gz',compresslevel=3) as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(root)))
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2));print('Archived',len(files),'files')
