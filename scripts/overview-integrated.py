"""Connected-layout results for the living notebook."""
import json,base64
def render(root):
 p=root/'simulations/integrated-verification.json'
 if not p.exists():return ''
 v=json.loads(p.read_text())
 def img(name):return 'data:image/png;base64,'+base64.b64encode((root/'docs/assets'/name).read_bytes()).decode()
 results='';p=root/'simulations/integrated-pex.json'
 if p.exists():
  d=json.loads(p.read_text());r=d['reduction'];rows=''
  for c in d['cases'].values():
   label=f'{c["model"]}: {c["corner"]}, {c["temp_C"]} °C, {c.get("diode","unknown")}'
   if c['status']!='complete':rows+=f'<tr><th>{label}</th><td colspan="3">Simulation incomplete</td></tr>';continue
   rows+=f'<tr><th>{label}</th><td>{c["max_hold_error_mV"]:.3f}</td><td>{c["max_output_shift_vs_separate_blocks_mV"]:.3f}</td><td>{"Pass" if c["screen_pass"] else "Fail"}</td></tr>'
  checks=''
  if 'checks' in d:
   for kind in ['timestep','shunt-placement']:
    values=[v['max_output_change_mV'] for v in d['checks'].values() if v['kind']==kind]
    if values:checks+=f'<li>{kind}: maximum sampled-output change {max(values):.5f} mV.</li>'
  corrections='; '.join(f'{n}: {a["signed_sum_fF"]:.3f} fF' for n,a in r['shunt_placement_approximation'].items())
  resistance=''
  low=next((v for v in d['cases'].values() if v.get('model')=='lowR' and v['status']=='complete'),None)
  nominal=next((v for v in d['cases'].values() if v.get('model')=='RC' and v['temp_C']==27 and v['corner']=='typical'),None)
  if low and nominal:
   delta=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(low['samples'],nominal['samples']))
   resistance=f'<p>Reducing all extracted resistances to 10% changes nominal sampled output by at most {delta:.3f} mV. This suggests the much larger shift from the separate blocks mainly reflects the changed capacitance network, including regenerated fill. It is brightness-dependent, not simply a fixed voltage offset. This test does not isolate individual capacitance contributions.</p>'
  results=f'''<h3>Connected RC simulation</h3><p>{r['resistors']} resistors; {r['raw_capacitors']:,} raw capacitors reduced to {r['output_capacitors']:,} effective capacitors. All 37 MOS devices and nine diodes remain.</p>
<p>The initial three selected RC conditions and nominal sensitivity controls are shown below. The full matrix is reported separately in the connected-corner section. The device-only and C-only transients stop at the ideal sampling-switch transition; they are incomplete, not passing controls. The device-only failure persists with a finer step and higher iteration limit. Extracted-device LVS passes independently. “lowR” retains the full capacitance and scales every extracted resistor to 10%.</p>
<img src="{img('integrated-comparison.png')}" alt="Sampling errors and output shifts for the connected layout">
<table><tr><th>Model / condition</th><th>Hold error (mV)</th><th>Output change vs separate blocks (mV)</th><th>0.5 mV screen</th></tr>{rows}</table>
<p>Tracking error uses this model’s loaded DC transfer with OUT forced, all rows selected, mux off and resets on. Active-readout supply loading can differ. Absolute output change is a separate calibration effect.</p>
{resistance}
<p>Magic’s negative local shunts on BIAS and OUT require a placement approximation: preserve each signed net-to-ground sum at the port ({corrections}). No negative value is simply discarded. Resistance and coupling remain. The sensitivity model moves the conserved totals to the most resistively distant nodes.</p><ul>{checks}</ul>'''
 return f'''<section id="integrated"><h2>Connected 3×3 layout: array → mux → output buffer</h2>
<p><b>Magic DRC: {v['magic_drc_count']}; KLayout DRC: {v['klayout_drc_count']}; LVS: {'unique match' if v['lvs_unique_match'] else 'not matched'}.</b> The filled physical layout contains 34 NMOS, three PMOS and nine photodiodes.</p>
<figure><img src="{img('integrated-functional.png')}" alt="Connected sensor geometry without density fill"><figcaption>Actual layout with fill hidden: pixel array above; seven-transistor bias/mux at lower left; three-PMOS buffer at lower right. Horizontal routes in the gap carry columns, mux output and shared supplies. Photodiodes retain their 20 × 20 µm junctions.</figcaption></figure>
<details><summary>Final filled layout</summary><img src="{img('integrated-layout.png')}" alt="Verified integrated layout with density fill"></details>
<p>New routes avoid the existing 26 × 26 µm optical keepouts. The filled region is approximately 336 × 243 µm; this is a test core without bond pads. Top-level observation terminals are not a pad ring.</p>
{results}<p class="note">References, controls and external ADC/package loads remain idealized. Device corners vary with nominal extracted wire R/C. No noise, mismatch or optical performance is established.</p>
<p><a href="integrated-layout.md">Reproduction and model details</a>. See the <a href="#integrated-corners">full connected-layout corner matrix</a> for subsequent checks. Physical reference and pad/ESD interface design remain ahead.</p></section>'''
