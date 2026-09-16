"""Step 1 readout results."""
import json,base64

def render(root):
 p=root/'simulations/column-bias.json'
 if not p.exists():return ''
 data=json.loads(p.read_text());rows=''
 for name,r in data['cases'].items():
  currents=r.get('sampled_sink_current_range_uA')
  current='—' if currents is None else f'{currents[0]:.3f}–{currents[1]:.3f}'
  rows+=f'<tr><th>{name}</th><td>{r["row0_signal_mV"][1]:.2f}</td><td>{r["row0_signal_mV"][2]:.2f}</td><td>{current}</td><td>{r["dark_late_window_change_mV"]:.3f}</td><td>{r["average_VDD_power_uW"]:.3f}</td></tr>'
 image=base64.b64encode((root/'docs/assets/column-bias.png').read_bytes()).decode()
 return f'''<section id="column-bias"><h2>Step 1: transistor column bias</h2>
<p>Each column now has a GF180 3.3 V NMOS current sink. A fourth, diode-connected NMOS creates a shared gate bias from an ideal reference current. All four devices use W = 2 µm, L = 2 µm with explicit assumed diffusion geometry. Reference currents of 0.25, 0.5 and 1 µA are compared with the previous 1 MΩ resistor loads.</p>
<p><b>Connections:</b> sink drains connect to COL0, COL1 and COL2; their gates connect to BIAS; their sources and bulks connect to ground. The reference transistor has gate and drain connected to BIAS, and source and bulk connected to ground.</p>
<p>The array retains its extracted resistance and floating-fill capacitance. Each column retains the assumed 1 pF external capacitor. The new bias transistors are schematic models and have not been laid out or passed DRC/LVS.</p>
<img src="data:image/png;base64,{image}" alt="Column current mirror sweep: signal response and dark-column settling">
<table><thead><tr><th>Load</th><th>80 pA signal (mV)</th><th>240 pA signal (mV)</th><th>Sampled sink current (µA)</th><th>Dark change, 25–50 µs (mV)</th><th>Mean VDD power (µW)</th></tr></thead><tbody>{rows}</tbody></table>
<p><b>Provisional next-stage setting: 0.5 µA.</b> It gives about 186 mV medium-light signal with sampled sink currents of 0.495–0.504 µA. The 0.25 µA option also works at this scan rate and remains a lower-power candidate. Multiplexer tests must establish the required current before committing to a choice.</p><p>Power covers the third frame and includes the reference branch; it excludes ideal reset/row driver power. The 25–50 µs change is a late-window diagnostic: continued exposure also changes the signal, so it is not a formal settling-time measurement. Current variation across pixels reveals finite output resistance and loss of compliance at low column voltage.</p>
<p class="note">This is a nominal, 27 °C design experiment. The reference current is still ideal; no current-reference startup, mismatch, noise, process/temperature sweep, bias-layout parasitics or ADC input circuit is included. An unselected column can discharge toward ground because a real NMOS sink loses current near zero drain voltage.</p>
<p>Reproduce with <code>bash scripts/run-tools.sh python3 scripts/column-bias.py</code>, then rebuild this notebook. See <a href="column-bias.md">the circuit and interpretation notes</a>. Next stage: column selection and its switching/settling effects.</p></section>'''
