"""Render measured post-layout electrical comparisons, without optical claims."""
import base64,json

def render(root):
 path=root/'simulations/parasitic-results.json'
 if not path.exists():return ''
 d=json.loads(path.read_text());rows=''
 for name,r in d['cases'].items():
  rows+=f'<tr><th>{name}</th><td>{r["row0_dark_subtracted_mV"][1]:.3f}</td><td>{r["row0_dark_subtracted_mV"][2]:.3f}</td><td>{r["max_reset_error_mV"]:.4f}</td><td>{r["max_frame2_to3_change_uV"]:.3f}</td></tr>'
 baseline=d['cases']['schematic']['row0_dark_subtracted_mV'][1]
 rc=d['cases']['RC_filled']['row0_dark_subtracted_mV'][1]
 change=100*(1-rc/baseline)
 resistance=d['cases']['C_filled']['row0_dark_subtracted_mV'][1]-rc
 numerical=d.get('numerical_check',{}).get('max_all_samples_difference_mV')
 stability=f'A half-step run with tighter relative tolerance changed sampled outputs by at most {numerical:.6f} mV.' if numerical is not None else 'Numerical refinement check pending.'
 image=base64.b64encode((root/'docs/assets/parasitic-comparison.png').read_bytes()).decode()
 return f'''<section id="parasitics"><h2>Extracted 20 µm array: resistance and capacitance</h2>
<p>The verified 3 × 3 layout now has a post-layout electrical model. Both filled and unfilled extracted device networks match the independent schematic in Netgen after wire resistors are shorted and parasitic capacitors removed. The original filled GDS is unchanged; its previous DRC/LVS results still refer to that same file.</p>
<p>Magic extracted <b>464 wire resistors</b> in each array, retaining 27 NMOS transistors and nine 400 µm² diodes. The filled network contains 453,557 raw capacitors. Eliminating 56,960 purely capacitive floating nodes leaves 464 effective capacitors. Fill remains electrically floating: this reduction preserves terminal charge and linear capacitance energy at zero initial net fill charge.</p>
<figure><img src="data:image/png;base64,{image}" alt="Schematic and extracted array response comparison"><figcaption>Same three-frame row scan, typical corner, 3.3 V supply, 2 V reset, 1 MΩ / 1 pF external column load. Photocurrent is assumed, not optically calibrated.</figcaption></figure>
<table><thead><tr><th>Model</th><th>80 pA signal (mV)</th><th>240 pA signal (mV)</th><th>Worst reset error (mV)</th><th>Frame 2–3 change (µV)</th></tr></thead><tbody>{rows}</tbody></table>
<p><b>Main result:</b> filled-layout RC reduces the medium-light signal by {change:.1f}% versus the schematic. Wire resistance alone changes it by only {resistance:.4f} mV relative to the filled C-only model: capacitance dominates for this geometry and timing. {stability}</p>
<p>Signals are dark-subtracted third-frame column samples from row 0. Reset error covers all nine pixels. Frame changes describe deterministic simulation repeatability, not measured noise. C-only models short the extracted wire resistors; RC models retain them. The unfilled version is an electrical control and does not satisfy the filled layout’s density requirements.</p>
<p class="note">Scope: nominal GF180 Magic interconnect extraction, with transistor and diode junction capacitance supplied by their device models. No optical calibration, noise simulation, package/bond-wire parasitics, ESD pads, output amplifier or ADC is included. This is a small-array result, not a verified 64 × 64 camera. Numerical tolerances are recorded in the generated testbenches.</p>
<h3>Next: realistic column readout</h3><p>Rows need selection and reset drivers. The analog signal travels along columns, so the next circuit is a column bias/load, column multiplexer and shared on-chip output buffer. An external amplifier and ADC can then process the buffered output. Test settling with pad, bond-wire, PCB and ADC input loads before choosing the multiplexing speed.</p>
<p>Reproduce after restoring the existing size-study checkpoint:</p><pre><code>bash scripts/run-tools.sh bash scripts/run-parasitics.sh</code></pre>
<p>See <a href="parasitic-extraction.md">extraction method and limitations</a>. The earlier sections below record earlier milestones; their proposed extraction work is superseded by this comparison.</p></section>'''
