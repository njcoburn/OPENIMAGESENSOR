import json,base64

def render(root):
 path=root/'simulations/readout-pex.json'
 if not path.exists():return ''
 d=json.loads(path.read_text());red=d['reduction'];rows=''
 for name,case in d['cases'].items():
  samples=case['samples'];rows+=f'<tr><th>{name}</th><td>{case["max_tracking_error_10us_mV"]:.4f}</td><td>'+', '.join(f'{s["output_V"]:.4f}' for s in samples[:3])+'</td></tr>'
 image=base64.b64encode((root/'docs/assets/readout-pex.png').read_bytes()).decode()
 return f'''<section id="readout-pex"><h2>Extracted readout connected to the extracted array</h2>
<p>The standalone bias/mux block contributes <b>{red['resistors']} resistors</b> and {red['raw_capacitors']:,} raw capacitors. Eliminating {red['eliminated_capacitive_nodes']:,} floating capacitance-only nodes leaves {red['output_capacitors']} effective capacitors. Extracted devices pass Netgen LVS against the independent seven-transistor circuit.</p>
<p class="note"><b>Extraction qualification:</b> Magic emitted a −3.52353 fF BIAS-to-ground shunt, making the raw parasitic capacitance matrix non-passive. We did not discard that value: the signed sum of BIAS-to-ground shunts is preserved as one capacitor at BIAS. All wire resistors and coupling capacitances remain. This approximates capacitance distribution along BIAS; it is not an unmodified distributed-RC result. A placement sensitivity run moves that same shunt to the reference transistor gate.</p>
<img src="data:image/png;base64,{image}" alt="Readout capacitance and resistance comparison">
<table><tr><th>Readout model</th><th>Worst tracking difference at 10 µs (mV)</th><th>Row 0 output samples (V)</th></tr>{rows}</table>
<p>Maximum sampled output change from schematic readout to qualified RC: <b>{d['RC_vs_schematic_max_output_difference_mV']:.3f} mV</b>. The observed output change is comparable to the numerical-refinement difference, so it does not establish a precise microvolt-scale physical effect. This compares identical sampling times, unlike a comparison between columns sampled at different exposure times. C denotes the extracted capacitances with ideal readout wires; devices is the extracted-device-only control.</p>
<p>Control checks: extracted devices versus schematic differ by at most {d['devices_control_max_difference_mV']:.6f} mV. Halving the transient step and tightening relative tolerance changes samples by at most {d['refinement_max_difference_mV']:.6f} mV. Moving the lumped BIAS shunt changes samples by at most {d.get('bias_placement_max_difference_mV',0):.6f} mV. These checks support this nominal comparison, not a sensor noise or ADC resolution claim.</p>
<p>The two separately extracted blocks connect through ideal wires. Inter-block routing, shared supply impedance, output buffer, pads/ESD, package and ADC loads are still absent. The reference current and control waveforms remain ideal. This simulation does not verify a physically integrated camera.</p>
<p>Reproduce: <code>bash scripts/run-tools.sh bash scripts/run-readout-pex.sh</code>. Compact netlists and the LVS/reduction audit are saved in <code>checkpoints/readout/pex/</code>. Next: output-buffer design and realistic external loads, followed by integrated routing and extraction.</p></section>'''
