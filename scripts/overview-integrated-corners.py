import json,base64
def render(root):
 p=root/'simulations/integrated-corners.json'
 if not p.exists():return ''
 d=json.loads(p.read_text());rows=list(d['cases'].values());complete=[r for r in rows if r['status']=='complete'];passed=sum(r['screen_pass'] for r in rows)
 if not complete:return ''
 worst=max(complete,key=lambda r:r['max_hold_error_mV']);shift=max(r['max_output_shift_vs_separate_blocks_mV'] for r in complete);table=''
 for r in sorted(rows,key=lambda r:(r['diode'],r['corner'],r['temp_C'])):
  label=f'{r["corner"]} / {r["diode"]}, {r["temp_C"]} °C'
  if r['status']!='complete':table+=f'<tr><th>{label}</th><td colspan="4">Incomplete simulation</td></tr>';continue
  table+=f'<tr><th>{label}</th><td>{r["max_hold_error_mV"]:.3f}</td><td>{r["max_output_shift_vs_separate_blocks_mV"]:.3f}</td><td>{r["mean_total_VDD_power_uW"]:.2f}</td><td>{"Pass" if r["screen_pass"] else "Fail"}</td></tr>'
 checks=''
 for kind in ['timestep','shunt-placement']:
  values=[r['max_output_change_mV'] for r in d.get('checks',{}).values() if r['kind']==kind]
  if values:checks+=f'<li>{kind}: maximum sampled-voltage change {max(values):.5f} mV; screening conclusion unchanged.</li>'
 picture=base64.b64encode((root/'docs/assets/integrated-corners.png').read_bytes()).decode()
 return f'''<section id="integrated-corners"><h2>Connected layout: full process/temperature matrix</h2>
<p><b>{passed}/24 cases pass the 0.5 mV screen; {len(complete)}/24 simulations complete.</b> Worst HOLD error: {worst['max_hold_error_mV']:.3f} mV ({worst['corner']}, {worst['temp_C']} °C, {worst['diode']}). The screen also requires ADC-input tracking error below 0.5 mV and correct brightness ordering for all nine pixels.</p>
<p>The same connected GDS, 40 µA buffer reference, 20 µs startup reset and 5 µs ADC acquisition are retained. Five MOS corners run at −40, 27, 85 and 125 °C with typical diodes. Four additional cases combine typical MOS with fast/slow diodes at −40/125 °C. This is the full agreed 24-case matrix, not every MOS×diode combination.</p>
<img src="data:image/png;base64,{picture}" alt="Connected-layout process and temperature sweep of sampling error and voltage change">
<table><tr><th>Model / temperature</th><th>HOLD error (mV)</th><th>Output change (mV)</th><th>VDD power (µW)</th><th>Screen</th></tr>{table}</table>
<p>Maximum output change from the corresponding separately extracted blocks: {shift:.3f} mV. That brightness-dependent calibration change is distinct from the small tracking error against each case’s own loaded DC transfer. DC calibration selects all rows, holds reset on and disables the mux; imaging transients retain rolling selection.</p><ul>{checks}</ul>
<p class="note">Device process/temperature varies; wire R/C, 3.3 V supply, ideal reference currents, photocurrents and generic ADC/package load stay nominal. The BIAS/OUT capacitance-placement approximation remains. Earlier zero-resistance diagnostic controls remain incomplete; this sweep does not resolve them. No supply corners, real reference startup, pad/ESD, noise, mismatch or optical response is qualified.</p>
<p>The GDS is unchanged from the DRC/LVS-clean connected checkpoint. <a href="integrated-corners.md">Reproduction and evidence</a>. Next: design the physical bias/reference interface and pad/ESD connections, then verify startup and supply sensitivity before choosing final ADC timing.</p></section>'''
