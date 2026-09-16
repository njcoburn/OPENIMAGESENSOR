import json,base64

def render(root):
 p=root/'simulations/output-buffer.json'
 if not p.exists():return ''
 d=json.loads(p.read_text());rows=''
 for name,r in d['cases'].items():
  samples=r['samples'];lo=min(x['output_V'] for x in samples);hi=max(x['output_V'] for x in samples)
  rows+=f'<tr><th>{name}</th><td>{lo:.3f}–{hi:.3f}</td><td>{r["max_tracking_error_mV"]:.3f}</td><td>{r["mean_total_VDD_power_uW"]:.1f}</td></tr>'
 extra=''
 if 'numerical_check' in d:
  check=d['numerical_check'];name=check['case'];r=d['cases'][name]
  picture=base64.b64encode((root/'docs/assets/buffer-acquisition.png').read_bytes()).decode()
  hold=max(abs(x['hold_error_mV']) for x in r['samples'])
  extra=f'<h3>Longer ADC acquisition</h3><p>With 5 µs acquisition, worst ADC-input tracking error is {r["max_tracking_error_mV"]:.3f} mV and the sampling-capacitor error at the acquisition endpoint is {hold:.3f} mV. The provisional choice is 20 µA with 100 pF and this 5 µs acquisition window; the screening limit is 1 mV, not an ADC accuracy specification. Halving the timestep and tightening relative tolerance changes sampled outputs by at most {check["half_step_max_sample_change_mV"]:.4f} mV.</p><img src="data:image/png;base64,{picture}" alt="Longer ADC acquisition transient">'
 image=base64.b64encode((root/'docs/assets/output-buffer.png').read_bytes()).decode()
 return f'''<section id="output-buffer"><h2>Shared output buffer: first transistor candidate</h2>
<p>A PMOS source follower buffers the roughly 0.44–0.99 V mux output. Its drain connects to ground, gate to OUT, source to BUF and bulk to VDD. A PMOS mirror supplies the source current; an ideal external reference sets 5 or 20 µA. The follower is W/L = 20/0.5 µm; reference and load devices are 20/2 µm.</p>
<p>This is a voltage-shifting follower, not a unity-gain amplifier. Its static transfer curve must be included in calibration. All three new PMOS devices are schematic models with assumed diffusion geometry; no buffer layout or DRC/LVS is claimed.</p>
<img src="data:image/png;base64,{image}" alt="Output buffer transient load tests and static transfer curves">
<table><tr><th>Reference / load</th><th>Sampled output range (V)</th><th>Worst tracking error at 10 µs (mV)</th><th>Mean total VDD power (µW)</th></tr>{rows}</table>
<p>Tracking error compares the dynamic output to the loaded DC transfer value at the instantaneous mux input. It therefore separates the follower’s intended voltage shift from lag. Optical integration continues throughout each mux selection. Power includes the buffer and ideal reference branch plus the earlier array/readout VDD load, but excludes ideal digital/reset driver power.</p>
{extra}<h3>External-load assumptions</h3><p>BUF → 1 Ω / 5 nH bond path → 5 pF pad → 100 Ω isolation → ADC input. The input has 100 pF or 1 nF capacitance and a 1 MΩ DC load. The sampled case adds a 20 pF capacitor through a 100 Ω ideal switch for 1 µs in the first test and 5 µs in the follow-up, with its charge reset before each acquisition to stress the driver. These are explicit generic assumptions; a chosen ADC’s actual input circuit, acquisition timing and allowed source impedance must replace them.</p>
<p class="note">The qualified extracted readout still uses the documented lumped BIAS shunt approximation. Inter-block wires, buffer wiring, real pad/ESD devices, reference startup, process/temperature variation, mismatch, noise and optical calibration remain absent. These nominal tests do not establish ADC bit accuracy or fabrication readiness.</p>
<p>See <a href="output-buffer.md">circuit and reproduction notes</a>. Reproduce with <code>bash scripts/run-tools.sh python3 scripts/output-buffer.py</code>, then rebuild this notebook.</p></section>'''
