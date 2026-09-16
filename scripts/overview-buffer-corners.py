import json,base64

def render(root):
 p=root/'simulations/buffer-corners.json'
 if not p.exists():return ''
 d=json.loads(p.read_text());cases=d['cases'];complete=[r for r in cases.values() if r['status']=='complete'];passed=sum(r['screen_pass'] for r in cases.values());rows=''
 for r in cases.values():
  label=f'{r["corner"]} / {r["diode_corner"]}'
  if r['status']!='complete':
   rows+=f'<tr><th>{label}</th><td>{r["temperature_C"]}</td><td colspan="4">Incomplete; inspect the case log.</td></tr>';continue
  lo,hi=r['output_range_V']
  rows+=f'<tr><th>{label}</th><td>{r["temperature_C"]}</td><td>{r["max_hold_error_mV"]:.3f}</td><td>{lo:.3f}–{hi:.3f}</td><td>{r["mean_total_VDD_power_uW"]:.1f}</td><td>{"Pass" if r["screen_pass"] else "Fail"}</td></tr>'
 refinement=''
 if 'worst_corner_refinement' in d:
  check=d['worst_corner_refinement'];refinement=f'<p>Numerical check: rerunning the largest-error case at 0.1 µs with tighter relative tolerance changed sampled voltages by at most {check["max_sample_voltage_change_mV"]:.4f} mV; its pass/fail conclusion was unchanged.</p>'
 fine=''
 if 'fine_margin_check' in d and d['fine_margin_check']['result']['status']=='complete':
  check=d['fine_margin_check'];r=check['result']
  fine=f'<p class="note"><b>Hot-corner margin:</b> a further 0.05 µs / 1e-5 relative-tolerance run gives {r["max_hold_error_mV"]:.3f} mV sampling error. Sampled voltages changed by {check["max_sample_voltage_change_mV"]:.4f} mV from the 0.1 µs run. This is close to the 1 mV screening boundary and should not be treated as comfortable design margin.</p>'
 if d.get('fine_margin_check',{}).get('status')=='simulation_failed':fine='<p class="note"><b>Further refinement was inconclusive:</b> the 0.05 µs / 1e-5 relative-tolerance hot-corner run encountered a timestep failure. The last completed refined error was 0.967 mV; comfortable margin below 1 mV has not been established.</p>'
 image=base64.b64encode((root/'docs/assets/buffer-corners.png').read_bytes()).decode()
 worst=max(complete,key=lambda r:r['max_hold_error_mV']) if complete else None
 finding=f'Largest sampling-capacitor error: {worst["max_hold_error_mV"]:.3f} mV at {worst["corner"]}, {worst["temperature_C"]} °C, {worst["diode_corner"]}.' if worst else 'No completed cases.'
 return f'''<section id="buffer-corners"><h2>Process and temperature screening</h2>
<p><b>{passed} of {len(cases)} cases meet the original-step screening criteria; {len(complete)} simulations completed.</b> {finding} The screen requires both output and sampling-capacitor error below 1 mV and correct brightness ordering across all nine pixels. This is an engineering threshold, not an ADC bit-accuracy specification.</p>
<p>The 20 µA PMOS buffer drives the same 100 pF board and switched 20 pF sampler, with 5 µs acquisition. Five installed MOS model sections—typical, ff, ss, fs and sf—run at −40, 27, 85 and 125 °C with the typical diode model. Four additional cases use fast/slow diode sections at −40 and 125 °C with typical MOS models. Mixed MOS sections use the PDK’s supplied fs/sf parameter sets.</p>
<img src="data:image/png;base64,{image}" alt="Buffer process and temperature error and power sweep">
<table><tr><th>MOS / diode section</th><th>°C</th><th>Worst sample error (mV)</th><th>Sampled output range (V)</th><th>Mean VDD power (µW)</th><th>Screen</th></tr>{rows}</table>
{refinement}{fine}<p>Each case uses its own loaded DC transfer curve at the same corner and temperature. Consequently these error figures measure dynamic tracking; they do not imply that one room-temperature voltage calibration remains valid at other corners or temperatures. The table shows output-voltage shifts separately.</p>
<p class="note">Supply remains 3.3 V. Both reference currents remain ideal and fixed. Temperature is applied to device models, but extracted R/C, external load values, bond/pad estimates and photocurrents remain fixed. This is not a full MOS×diode×interconnect corner cross-product, supply sweep, mismatch/noise analysis, reference-startup test, optical-temperature model or fabrication qualification. The previous BIAS-capacitance approximation remains in use.</p>
<p><b>Before buffer layout:</b> resolve the incomplete cold-corner run and establish more hot-corner sampling margin. A larger acquisition window or more drive current can be investigated next; no such design change is included in this sweep.</p><p>See <a href="buffer-corners.md">scope, interpretation and reproduction</a>. Run <code>bash scripts/run-tools.sh python3 scripts/buffer-corners.py</code>, then rebuild the notebook. Case testbenches, DC curves, waveforms and logs are retained under <code>build/buffer-corners/</code>; source hashes are recorded with the summary.</p></section>'''
