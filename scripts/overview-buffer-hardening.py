import base64,json

def render(root):
 path=root/'simulations/buffer-hardened-corners.json';layout=root/'simulations/buffer-layout-verification.json'
 if not path.exists():return ''
 d=json.loads(path.read_text());rows=d['cases'];completed=[r for r in rows.values() if r['status']=='complete'];passed=sum(r['screen_pass'] for r in rows.values());worst=max(completed,key=lambda r:r['max_hold_error_mV'])
 def image(name,alt):return '<figure><img src="data:image/png;base64,'+base64.b64encode((root/'docs/assets'/name).read_bytes()).decode()+'" alt="'+alt+'"><figcaption>'+alt+'</figcaption></figure>'
 table=''
 for name,r in rows.items():
  if r['status']!='complete':table+=f'<tr><th>{name}</th><td colspan="3">Incomplete</td></tr>';continue
  table+=f'<tr><th>{r["corner"]} / {r["diode"]}</th><td>{r["temp_C"]}</td><td>{r["max_hold_error_mV"]:.3f}</td><td>{r["mean_total_VDD_power_uW"]:.1f}</td></tr>'
 physical=''
 if layout.exists():
  v=json.loads(layout.read_text());physical=f'<h3>Standalone buffer layout</h3><p>Three PMOS devices: reference mirror, current-source load and source follower, from left to right. Magic DRC: {v["magic_drc_count"]}; full KLayout DRC: {v["klayout_drc_count"]}; Netgen LVS unique match: {v["lvs_unique_match"]}. Exact GDS and reports are saved in <code>checkpoints/output-buffer/</code>.</p>'+image('buffer-functional.png','Buffer connections before density fill; verified final GDS includes fill.')
 refine=''
 if 'refinements' in d:refine='<p>The cold slow-process case and the largest-error revised case also pass at 0.05 µs and tighter relative tolerance. Largest sampled-output change: '+f'{max(r["max_output_change_mV"] for r in d["refinements"].values()):.4f} mV.</p>'
 return f'''<section id="buffer-hardening"><h2>Revised buffer: startup reset and stronger drive</h2>
<p><b>{passed}/{len(rows)} cases meet the revised 0.5 mV screen.</b> The buffer reference is now 40 µA. All rows reset for 20 µs at startup before the original rolling-reset sequence continues. There is no added mux precharge circuit.</p>
<h3>Cold failure diagnosis</h3><p>The isolated buffer passed a slow sweep through the problematic idle-input range, with and without the board model. Removing bond-wire inductance, readout parasitics or array parasitics individually did not solve the connected-chain failure. Holding the mux output at 0.8 V with an NMOS precharge switch did not solve it either.</p>
<p>Before the original failure, unreset row-1/row-2 sensing nodes had reached approximately −0.40 V: the testbench applied photocurrent from time zero but delayed those rows’ first resets. A global startup reset makes the original extracted chain complete at −40 °C at both 20 and 40 µA. This supports the startup sequence as the remedy; it is not proof of the simulator’s internal failure mechanism. The reset pulse must ultimately be implemented by the row-control hardware.</p>
<h3>Hot-corner drive</h3><p>At fs / 125 °C, the original 20 µA gives about 0.967 mV error; 30, 40 and 60 µA give about 0.194, 0.179 and 0.145 mV respectively. We carry 40 µA forward for added drive margin; ideal reference-current generation still needs implementation.</p>
{image('buffer-hardening.png','Hot-current comparison and revised process/temperature screen.')}
<p>Largest revised sampling error: <b>{worst['max_hold_error_mV']:.3f} mV</b> at {worst['corner']}, {worst['temp_C']} °C, {worst['diode']}. Each result uses its own loaded DC transfer curve, so calibration drift is not hidden inside the tracking-error number.</p>
{refine}<table><tr><th>MOS / diode corner</th><th>°C</th><th>Worst sample error (mV)</th><th>Mean VDD power (µW)</th></tr>{table}</table>
{physical}<p class="note">The simulation includes the separately extracted array and qualified readout model; the buffer and row-control waveforms are schematic-only. Buffer-layout parasitics and inter-block routing are not yet simulated. References, supply and load estimates remain ideal/fixed; no mismatch, noise, optical calibration, pad/ESD or actual ADC model is included. The buffer is a voltage-shifting source follower, not a unity-gain amplifier.</p>
<p>Next: extract the buffer layout and repeat the combined electrical checks, then integrate routing and pad/ESD design. See <a href="buffer-hardening.md">reproduction and evidence</a>. Earlier sections below retain the failed experiments and superseded candidate results.</p></section>'''
