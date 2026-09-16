import json,base64

def render(root):
 p=root/'simulations/column-mux.json';v=root/'simulations/readout-verification.json'
 if not p.exists() or not v.exists():return ''
 d=json.loads(p.read_text());verification=json.loads(v.read_text())
 def img(name,alt):return '<figure><img src="data:image/png;base64,'+base64.b64encode((root/'docs/assets'/name).read_bytes()).decode()+'" alt="'+alt+'"><figcaption>'+alt+'</figcaption></figure>'
 rows=''
 for us in [1,2,5,10,15]:
  error=max(abs(r['tracking_error_mV'][str(us)]) for r in d['samples'])
  rows+=f'<tr><td>{us}</td><td>{error:.4f}</td></tr>'
 disturbance=max(abs(r['column_disturbance_10us_mV']) for r in d['samples'])
 return f'''<section id="column-mux"><h2>Step 2: multiplexed output and readout layout</h2>
<p>Three GF180 NMOS switches select COL0, COL1 or COL2 onto OUT. Each switch is W/L = 1/0.5 µm. A 3.3 V gate signal suits the simulated roughly 0.44–0.99 V column range; this is not a rail-to-rail switch design. The bias reference is 0.5 µA.</p>
<p>Each switch is selected for 16 µs, followed by a 2 µs gap. All three columns are sampled within the existing row selection. Select drivers are ideal external stimuli. OUT has an assumed 1 pF capacitor and 1 GΩ leakage resistor; this is not an ADC input model.</p>
{img('column-mux.png','Multiplexer output follows three columns in sequence; third-frame row 0.')}
<table><tr><th>Delay after selection (µs)</th><th>Worst OUT minus selected COL magnitude (mV), nine samples</th></tr>{rows}</table>
<p>At 10 µs, the maximum change in the selected column relative to the no-mux run is <b>{disturbance:.3f} mV</b>. This is separate from the small output-to-column tracking error: charge sharing can disturb both nodes together. Columns are sampled at different exposure times; equal-time image comparisons need timing correction or sample/hold circuits. Microvolt-scale tracking values are numerical diagnostics, not ADC accuracy claims.</p>
<h3>Physical block: seven transistors</h3>
<p>Left to right: reference NMOS, three column bias sinks, then three mux switches. Horizontal rails connect GND, BIAS, COL0–2, OUT and SEL0–2; vertical routes connect transistor terminals. The ideal reference source and timing drivers remain outside the block.</p>
{img('readout-functional.png','Readout wiring view before density fill: four bias transistors followed by three mux transistors.')}
{img('readout-layout.png','Final standalone readout block with floating density fill.')}
<p><b>Verification:</b> Magic DRC {verification['magic_drc_count']} errors; full GF180 KLayout DRC {verification['klayout_drc_count']} errors; Netgen LVS unique match to the independent seven-transistor netlist. The exact GDS and reports are saved in <code>checkpoints/readout/</code>.</p>
<p class="note">The readout block is verified separately and has not been physically joined to the pixel array. The simulation uses the extracted array with schematic readout devices. Readout wiring/fill parasitics are not yet included. No output buffer, pad/ESD circuitry, package, real ADC load, mismatch or noise analysis is included.</p>
<p>Next: extract the new readout block, reconnect it to the array simulation, then design the shared output buffer against realistic external loads. See <a href="column-mux.md">reproduction and scope</a>.</p></section>'''
