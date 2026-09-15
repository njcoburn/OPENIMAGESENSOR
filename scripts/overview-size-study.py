"""Notebook section generated from verified size-study results."""
import json,base64,hashlib

def render(root):
 path=root/'simulations/diode-size-comparison.json'
 if not path.exists():return ''
 data=json.loads(path.read_text());rows=data['variants']
 def picture(name,alt):
  b=base64.b64encode((root/'docs/assets'/name).read_bytes()).decode()
  mime='image/svg+xml' if name.endswith('.svg') else 'image/png'
  return f'<figure><img src="data:{mime};base64,{b}" alt="{alt}"><figcaption>{alt}</figcaption></figure>'
 table='';layouts=''
 for r in rows:
  n=r['size_um'];gds=root/f'build/size-study/{n}um/build/array_3x3.gds'
  assert hashlib.sha256(gds.read_bytes()).hexdigest()==r['verification']['gds_sha256']
  sig=r['dark_subtracted_signal_mV']
  table+=f"<tr><th>{n} × {n} µm</th><td>{r['fill_factor_percent']:g}%</td><td>{r['photocurrents_pA'][2]:g} pA</td><td>{sig[1]:.1f} mV</td><td>{sig[2]:.1f} mV</td><td>{r['effective_sense_capacitance_fF']:.1f} fF</td><td>{r['max_reset_error_mV']:.3f} mV</td><td>{r['frame2_to3_max_change_uV']:.2f} µV</td><td>0 / 0; match</td></tr>"
  layouts+=f'<h4>{n} × {n} µm junctions</h4>'+picture(f'diode-{n}um-array-layout.png',f'Actual KLayout render of the verified {n} µm variant, including fill.')
 return f'''<section id="size-study"><div class="tag">Latest experiment · detector size comparison</div><h2>Three junction sizes: layout checks and electrical response</h2><p>The 5, 10 and 20 µm square-junction variants each contain nine pixels at an 80 × 50 µm pitch. Each delivered GDS passes Magic and full installed GF180MCUD KLayout DRC, and Netgen matches both the independent reference and generated Xschem schematic (27 NMOS + 9 diodes).</p><p>The 10 and 20 µm variants relocate diode contacts and access routes and enlarge optical fill clearances. The 20 µm diode center moves down 5 µm to clear horizontal buses; its fill boundary extends down 8 µm. Nonphysical layer-0 primitive boundary markers are removed in the larger final GDS files so they do not distort density calculations. All physical layers remain checked.</p>
<h3>The larger layout currently in VNC</h3>
{picture('large-pixel-labeled.svg','Labeled original VNC screenshot: reset, source follower, row select, photodiode, horizontal buses, column output and dummy fill. Callouts identify one representative pixel; the structure repeats nine times.')}
<details><summary>Original VNC screenshot</summary>{picture('large-pixel-vnc.png','Actual VNC desktop capture of the 20 × 20 µm junction variant in KLayout. Nine junctions at 80 × 50 µm pixel pitch; drawn junction fraction 10%.')}</details>
<p>This is our preferred candidate for the next extraction experiment. The larger square junctions are clearly visible within their fill clearances. The source layout and verified checkpoint remain unchanged by this screenshot.</p>
{picture('diode-size-comparison.png','Simulated size comparison: column signal versus assumed photocurrent density, and medium-light sense-node discharge.')}
<p>Comparison conditions: typical GF180 electrical models; VDD=3.3 V, reset supply=2.0 V; 20 µs reset; sample about 950 µs after reset release; external 1 MΩ ∥ 1 pF on each column. Three frames scan the same permuted dark/medium/bright pattern. Medium and bright correspond to assumed photocurrent densities of 0.2 and 0.6 pA/µm². Absolute photon flux and optical efficiency are not calibrated.</p>
<div style="overflow-x:auto"><table><tr><th>Junction</th><th>Geometric fraction</th><th>Bright current</th><th>Medium signal</th><th>Bright signal</th><th>Effective C</th><th>Reset error, max</th><th>Frame 2→3 change, max</th><th>Magic/KLayout; LVS</th></tr>{table}</table></div>
<p>Signal means dark column voltage minus illuminated column voltage, sampled in row 0 of frame 3. Effective C is a secant estimate I·Δt/ΔV from the medium-light sense-node discharge between 80 and 880 µs after reset release, with the row disconnected. It includes the electrical model’s voltage-dependent device capacitance; it is not extracted wiring capacitance. Reset error is |2.0 V − sense voltage| one microsecond before reset release, maximized over the nine pixels in frame 3. Frame repeatability is deterministic, not a noise measurement.</p>
<p>The modeled effective capacitance rises from about 18.7 to 65.6 to 249.0 fF. All nine sense nodes reset to within 0.01 mV of 2.0 V under the 20 µs pulse in frame 3. The sense-node steps near readout in the plot come from switching the row-selection circuit in this schematic model.</p><p><b>How to interpret this:</b> increasing diode area increases both photocurrent and sense-node capacitance. The voltage signal therefore does not scale by 4× or 16× with area. These results test integration and reset behavior under a controlled electrical assumption; they do not select an optical winner. A larger collected-electron signal may benefit photon-limited imaging, but noise, quantum efficiency and dark-current behavior need separate characterization.</p>
<p class="note">The comparison uses each LVS-matched schematic with updated diode area/perimeter. Wiring resistance, wire/fill capacitance, process corners, mismatch and noise are not included. Parasitic extraction is the next comparison stage. These are local core checks, not manufacturing submission signoff.</p>
<details><summary>Inspect all three verified layouts</summary>{layouts}</details>
<h3 id="next-steps-large-pixel">Next steps for the larger pixel</h3>
<ol><li><b>Extract parasitics from the verified 20 µm GDS.</b> Begin with wiring capacitance, then resistance where supported. Check what the installed extraction deck actually models, including coupling to floating fill. Keep the 5 µm baseline as a comparison. Record any omitted effects rather than treating an LVS netlist as a complete parasitic model.</li>
<li><b>Repeat the same three-frame scan.</b> Compare schematic and extracted results for column signal, reset behavior, row-switching disturbances and settling before the sample. Check that device capacitance is not counted twice and that the extracted netlist retains the nine diodes and 27 transistors.</li>
<li><b>Find the useful operating range.</b> Sweep exposure, assumed light-current density, column load, supply and available process/temperature corners. Establish readout timing and saturation limits. Investigate noise and mismatch separately from deterministic repeatability.</li>
<li><b>Design the external readout interface.</b> Choose practical column bias and output buffering, then define ADC input range, acquisition time and sample rate. Use those requirements to select the ADC and controller for a test board.</li>
<li><b>Resolve optical access and fabrication integration.</b> Confirm the intended run’s detector structure, allowed optical openings, surface layers, packaging and illumination path. Add pads/protection and chip-level routing; repeat full-chip DRC/LVS and extraction before submission.</li></ol>
<p><b>Immediate next task:</b> a documented schematic-versus-extracted comparison for the 20 µm array. Keeping the current geometry fixed will make any change in response attributable to the extraction model.</p>
<h3>Reproduce and inspect</h3><pre><code>bash scripts/run-size-study.sh</code></pre><p>Variant GDS, Xschem schematics, netlists and verification logs are in <code>build/size-study/5um/</code>, <code>10um/</code> and <code>20um/</code>. Machine-readable comparison and GDS fingerprints: <code>simulations/diode-size-comparison.json</code>. The original baseline remains in its original paths.</p></section>'''
