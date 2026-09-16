import json,base64
def render(root):
 p=root/'simulations/bias-reference.json'
 if not p.exists() or not (root/'docs/assets/bias-reference-dc.png').exists():return ''
 d=json.loads(p.read_text());rows=list(d['cases'].values());dc=json.loads((root/'simulations/bias-reference-dc.json').read_text());complete=[v for v in rows if v['status']=='complete']
 if not complete:return ''
 def img(n):return 'data:image/png;base64,'+base64.b64encode((root/'docs/assets'/n).read_bytes()).decode()
 worst=max(v['max_hold_error_mV'] for v in complete);startup=max(v['startup_reference_relative_error'] for v in complete)*100;table=''
 for r in rows:
  label=f'{r["corner"]}/{r["diode"]}, {r["temp_C"]} °C, {r["supply_V"]} V; R×{r["rcol_scale"]}/{r["rbuf_scale"]}; ramp {r["ramp_us"]} µs, C {r["external_bias_C_pF"]} pF'
  if r['status']!='complete':table+=f'<tr><th>{label}</th><td colspan="4">Incomplete simulation</td></tr>';continue
  table+=f'<tr><th>{label}</th><td>{r["mean_column_reference_uA"]:.3f} / {r["mean_buffer_reference_uA"]:.2f}</td><td>{r["max_hold_error_mV"]:.3f}</td><td>{100*r["startup_reference_relative_error"]:.5f}%</td><td>{"Pass" if r["screen_pass"] else "Fail"}</td></tr>'
 fine=''
 if d.get('refinements'):fine=f'<p>Finer-step checks change sampled output by at most {max(v["max_sample_change_mV"] for v in d["refinements"].values()):.5f} mV, with unchanged pass/fail results.</p>'
 circuit=(root/'docs/assets/bias-reference-circuit.svg').read_text()
 return f'''<section id="bias-reference"><h2>Physical bias: external resistors and existing on-chip mirrors</h2>
<p><b>{sum(v['screen_pass'] for v in rows)}/{len(rows)} selected power-up/imaging cases pass; {sum(v['status']=='complete' for v in dc['cases'].values())}/{len(dc['cases'])} DC cases converge.</b> Worst sampling error: {worst:.3f} mV against the 0.5 mV screen. Both ideal bias-current sources are replaced in these tests.</p>
{circuit}<p>At nominal conditions, 5.1 MΩ from VDD to BIAS supplies about 0.508 µA; 49.9 kΩ from PREF to ground draws about 39.88 µA. The on-chip reference MOS devices and current mirrors already exist in the verified layout. This is a buildable PCB bias option, not a regulated on-chip reference or a fabricated board.</p>
<img src="{img('bias-reference-dc.png')}" alt="Bias resistor currents across supply, process and temperature">
<p>The 84 DC cases cover five MOS corners, four temperatures and three supplies, diode endpoint checks, and independent ±1% resistor-value combinations at selected conditions. Current ranges are 0.412–0.610 µA and 31.76–48.37 µA. Actual resistor temperature coefficient is not modeled.</p>
<h3>Startup and sampling</h3><img src="{img('bias-reference-startup.png')}" alt="Supply ramps and resistor-current startup traces">
<p>The external controller holds reset through power-up and waits 200 µs after the supply ramp before the original timing sequence begins. Reset drive tracks VDD; the external 2 V reset supply ramps alongside it. Selected 1, 100 and 1000 µs ramps are tested, with 5 pF assumed capacitance on each bias pin and one 50 pF case. Maximum reference-current deviation during the last 10 µs of that wait: {startup:.5f}% versus steady operation (1% criterion). This is not a measured minimum startup time.</p>
<table><tr><th>Condition / component factors</th><th>Column / buffer current (µA)</th><th>HOLD error (mV)</th><th>Pre-scan current error</th><th>Screen</th></tr>{table}</table>{fine}
<p class="note">The imaging checks are selected cases, not the full 84-case DC matrix repeated in transient. VRESET generation, controller, ADC and supply remain idealized; pad/ESD leakage, resistor noise/TC, package coupling, mismatch and brownout recovery remain unverified. Existing extraction approximations remain. The GDS is unchanged: new components are external. A new Xschem view matches the nominal SPICE connections and pin order.</p>
<p>The 3.0–3.6 V functional sweep does not establish reliability signoff; see <a href="https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_14_1.html">GF180 operating limits</a>. <a href="board-bias.md">Reproduction and detailed scope</a>. Next: quantify real bias-pin pad/ESD leakage and capacitance, implement the reset/supply interface, and decide whether a regulated reference is needed for image stability.</p></section>'''
