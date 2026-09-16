import json,base64

def render(root):
 p=root/'simulations/buffer-pex.json'
 if not p.exists():return ''
 d=json.loads(p.read_text());cases=d['cases'];rc=[r for r in cases.values() if r['buffer_model']=='RC'];complete=[r for r in rc if r['status']=='complete'];n=sum(r['screen_pass'] for r in rc)
 red=d['reduction'];worst=max(complete,key=lambda r:r['max_hold_error_mV']);table=''
 for r in cases.values():
  label=f'{r["buffer_model"]}: {r["corner"]}/{r.get("diode","diode_typical")}, {r["temp_C"]} °C'
  if r['status']!='complete':table+=f'<tr><th>{label}</th><td colspan="3">Incomplete simulation</td></tr>';continue
  table+=f'<tr><th>{label}</th><td>{r["max_hold_error_mV"]:.3f}</td><td>{r["max_output_shift_vs_schematic_mV"]:.3f}</td><td>{r["mean_total_VDD_power_uW"]:.1f}</td></tr>'
 picture=base64.b64encode((root/'docs/assets/buffer-pex.png').read_bytes()).decode()
 refined=''
 if 'refinements' in d:refined='<p>Cold and worst-case refinement at 0.05 µs / 1e-5 relative tolerance preserved the screening conclusions. Maximum change in sampled voltage: '+f'{max(v["max_output_change_mV"] for v in d["refinements"].values()):.4f} mV.</p>'
 return f'''<section id="buffer-pex"><h2>Buffer wiring extracted: three-block electrical model</h2>
<p><b>{n}/{len(rc)} RC corner cases pass the 0.5 mV screen.</b> The largest completed sampling-capacitor error is {worst['max_hold_error_mV']:.3f} mV. The 40 µA reference and 20 µs all-row startup reset are retained.</p>
<p>The verified buffer GDS yields {red['resistors']} resistors and {red['raw_capacitors']:,} raw capacitors. Eliminating {red['eliminated_capacitive_nodes']:,} purely capacitive floating nodes leaves {red['output_capacitors']} effective capacitors. All three PMOS devices remain. The buffer capacitance network passes the passivity, charge/energy and reduction-error checks without a negative-shunt redistribution correction.</p>
<p>Netgen matches the extracted buffer devices to the independent schematic after resistors are shorted and capacitors removed. The device-only simulation is a second control; C-only retains the extracted capacitance with ideal wires. Both controls use the nominal corner at 27 °C.</p>
<img src="data:image/png;base64,{picture}" alt="Extracted-buffer sampling errors and output shifts over process and temperature">
<table><tr><th>Buffer model / corner</th><th>Sample error (mV)</th><th>Output change vs schematic (mV)</th><th>VDD power (µW)</th></tr>{table}</table>
<p>Sampling error uses each model’s own loaded DC transfer curve. Output change compares identical sample times against the preceding schematic-buffer run, and includes static voltage offsets caused by wiring resistance. Small dynamic error does not imply unchanged voltage calibration. The plots show typical-diode sweeps; the table also includes fast/slow diode endpoint tests.</p>
{refined}<p class="note">The array, readout and buffer are extracted separately and joined by ideal wires. Inter-block routing and a common physical supply/ground network remain unmodeled. The earlier readout BIAS-shunt approximation is still present; this new buffer extraction adds no such correction. R/C and external-load values remain nominal while device process/temperature models vary. References, timing, package estimates and sampling load remain idealized; no pad/ESD circuit, real ADC, noise, mismatch or optical characterization is included.</p>
<p>Exact compact buffer models, reduction audit, original extraction and LVS report are saved in <code>checkpoints/output-buffer/pex/</code>. See <a href="buffer-pex.md">reproduction details</a>. Next: integrate the physical blocks and their supply/ground routing, then extract the combined layout.</p></section>'''
