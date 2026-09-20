"""Rebuild the standalone team report from simulation data and a VNC capture."""
from pathlib import Path
import base64, csv, json
from datetime import datetime, timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
assets=root/'docs/assets'; assets.mkdir(exist_ok=True)
data={key:np.loadtxt(root/f'simulations/cycles_{key}',skiprows=1) for key in ['0','1p','5p']}
colors=['#2563eb','#c55c13','#218355']; labels=['Dark · 0 pA','Dim · 1 pA','Bright · 5 pA']
samples={}
for key,d in data.items():
 assert d.shape[1]==5 and np.isfinite(d).all(), 'Invalid waveform data'
 assert (np.diff(d[:,0])>=0).all(), 'Time must be ordered'
 samples[key]=[float(np.interp(i*.001+.00097,d[:,0],d[:,4])) for i in range(4)]
 assert np.sum(np.diff((d[:,2]>1.65).astype(int))==1)==4, 'Expected four row selections'
 for i in range(4):
  assert np.interp(i*.001+10e-6,d[:,0],d[:,1])>3, 'Reset not asserted'
  assert np.interp(i*.001+500e-6,d[:,0],d[:,2])<.1, 'Row must be off during integration'
for i in range(4): assert samples['0'][i]>samples['1p'][i]>samples['5p'][i], 'Light ordering failed'
(root/'simulations/cycle-samples.json').write_text(json.dumps({'sample_offset_us':970,'column_V':samples},indent=2)+'\n')
for zoom,name in [(False,'cycles'),(True,'last-cycle')]:
 fig,axs=plt.subplots(3,1,figsize=(11,8),sharex=True,layout='constrained',height_ratios=[.8,1,1])
 d=data['0'];axs[0].plot(d[:,0]*1e3,d[:,1],label='Reset',color='#7944aa');axs[0].plot(d[:,0]*1e3,d[:,2],label='Row select',color='#475569')
 for (key,d),color,label in zip(data.items(),colors,labels):
  axs[1].plot(d[:,0]*1e3,d[:,3],label=label,color=color)
  axs[2].plot(d[:,0]*1e3,d[:,4],label=label,color=color)
  axs[2].scatter(np.arange(4)+.97,samples[key],s=18,color=color,zorder=4)
 for ax,title in zip(axs,['Timing controls','Sensing node: charge integrates here','Column: valid readout only while row is selected']):
  ax.set(ylabel='Voltage (V)',title=title);ax.grid(alpha=.2);ax.legend(loc='upper right',ncol=3,fontsize=8)
  for i in range(4):ax.axvspan(i+.92,i+.98,color='#ccead9',alpha=.5)
 axs[-1].set(xlabel='Time (ms)',xlim=(3,4) if zoom else (0,4))
 fig.savefig(assets/f'{name}.png',dpi=150);plt.close(fig)
def img(name):
 return 'data:image/png;base64,'+base64.b64encode((assets/name).read_bytes()).decode()
rows=''.join('<tr><th>'+str(i+1)+'</th>'+''.join(f'<td>{samples[k][i]:.6f}</td>' for k in data)+'</tr>' for i in range(4))
darkchange=(samples['0'][3]-samples['0'][2])*1000
stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Open Image Sensor · Engineering notebook</title>
<style>:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f2f5f6;color:#182c3b;font:17px/1.65 system-ui,sans-serif}header{background:#102e3b;color:white;padding:64px max(24px,calc((100vw - 1100px)/2))}header p{max-width:760px;color:#d2e4e9}h1{font-size:clamp(32px,5vw,55px);line-height:1.1;margin:12px 0}h2{font-size:29px;line-height:1.2}h3{font-size:20px}main{max-width:1150px;margin:auto;padding:24px}section{background:white;border:1px solid #dce5e9;border-radius:14px;padding:30px;margin:22px 0}nav{display:flex;flex-wrap:wrap;gap:20px}a{color:#146379}header a{color:#b6e8eb}.tag{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:#a6dbd0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}.card{background:#edf5f5;padding:20px;border-radius:10px}.card strong{display:block;font-size:24px}img{display:block;width:100%;height:auto;border-radius:8px}figure{margin:24px 0}figcaption,.small{font-size:14px;color:#526574}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}th,td{text-align:left;padding:11px;border-bottom:1px solid #dce5e9}code{background:#eef2f3;padding:2px 5px;font-size:14px}pre{overflow:auto;background:#102e3b;color:#e6f1f1;padding:20px;border-radius:8px}pre code{background:none;color:inherit}.note{border-left:4px solid #d88a32;background:#fff6e9;padding:16px}summary{cursor:pointer;font-weight:650}button{padding:10px 18px;border:1px solid #146379;border-radius:6px;background:#fff;color:#146379;cursor:pointer;margin-right:8px}button[aria-pressed=true]{background:#146379;color:white}.hidden{display:none}@media print{body{background:white}section{break-inside:avoid;border:0;padding:10px}header{padding:25px}button,nav{display:none}.hidden{display:block}}</style></head><body>
<header><div class="tag">Open Image Sensor / living engineering notebook</div><h1>A monochrome camera,<br>starting with one pixel.</h1><p>GF180MCU · Xschem · ngspice · future gdsfactory layout. This notebook records what we built, what the simulations show, and which assumptions still need physical validation.</p><nav><a href="#status">Status</a><a href="#circuit">Circuit</a><a href="#timing">Timing</a><a href="#results">Results</a><a href="#history">History</a><a href="#reproduce">Reproduce</a></nav></header><main>
<section id="status"><h2>Current milestone</h2><p>One three-transistor pixel now runs through four finite reset–integration–readout cycles, starting with discharged sensing and column nodes. Higher photocurrent produces a lower sampled output in every cycle.</p><div class="grid"><div class="card"><strong>4 cycles</strong>1 ms period; a single-pixel experiment, not a demonstrated camera frame rate.</div><div class="card"><strong>3 light levels</strong>0, 1 and 5 pA of assumed photocurrent.</div><div class="card"><strong>3.3 V supply</strong>GF180 3.3 V NMOS electrical models at the typical corner.</div></div><p class="note">The dark output continues to change between cycles. The circuit is not yet a repeatable, calibrated sensor. We have no fabricated-device measurements or layout signoff.</p></section>
<section id="circuit"><h2>Inside the pixel</h2><p>The sensing node stores charge. Reset charges it; light removes charge during exposure. The source follower buffers its voltage, and the row transistor connects it to a shared column.</p><div class="grid"><div><h3>In the pixel</h3><ul><li><b>Xrst:</b> reset switch.</li><li><b>Dphoto + Csense + Iphoto:</b> simplified photodiode model.</li><li><b>Xsf:</b> source-follower buffer.</li><li><b>Xsel:</b> row-select switch.</li></ul></div><div><h3>Outside the pixel</h3><ul><li><b>Rload:</b> 1 MΩ passive column load.</li><li><b>Ccol:</b> assumed 1 pF column capacitance.</li><li>Ideal supply and timing sources.</li><li>Numerical readout samples; no ADC circuit yet.</li></ul></div></div><figure><img src="SCHEMATIC" alt="Xschem desktop showing the GF180 repeated-cycle pixel schematic"><figcaption>Actual Xschem VNC capture. The model and timing block appear beside the circuit. The capture is a snapshot, not a live stream.</figcaption></figure><p>The first experiment used a continuously selected row and an ideal 1 µA current sink. For disconnected-row operation, this test uses a resistor: an always-on ideal sink could drive an isolated column below ground. This change affects bias and gain, so absolute voltages should not be compared directly between the two experiments.</p></section>
<section id="timing"><h2>What happens each millisecond?</h2><table><thead><tr><th>Time within cycle</th><th>Operation</th><th>Meaning</th></tr></thead><tbody><tr><td>0–20 µs</td><td>Reset on, row off</td><td>Charge the sensing node through Xrst.</td></tr><tr><td>20–920 µs</td><td>Reset off, row off</td><td>Photocurrent changes the stored sensing voltage.</td></tr><tr><td>920–980 µs</td><td>Row on</td><td>Drive the column through the source follower.</td></tr><tr><td>970 µs</td><td>Sample column</td><td>Record a voltage 50 µs after row selection.</td></tr><tr><td>980–1000 µs</td><td>Row off</td><td>The passive load discharges the column before the next cycle.</td></tr></tbody></table><p><b>Exposure continues during readout.</b> This 3T pixel has no transfer gate or storage shutter. The sample occurs about 950 µs after reset releases. Row selection is an electrical read switch, not an optical shutter.</p><p>Approximately, voltage drop = photocurrent × elapsed exposure / total sensing capacitance. Switching and MOS capacitances also affect the waveforms. A lower sampled voltage corresponds to brighter illumination under comparable reset conditions.</p></section>
<section id="results"><h2>Measured simulation response</h2><p>Green shaded bands show row selection. Dots mark the samples at 970 µs within each cycle. Column voltages outside those bands are not valid pixel readings.</p><div><button aria-pressed="true" onclick="showPlot(false,this)">All four cycles</button><button aria-pressed="false" onclick="showPlot(true,this)">Last cycle</button></div><figure id="all"><img src="CYCLES" alt="Reset, row, sensing-node and column waveforms across four cycles"></figure><figure id="last" class="hidden"><img src="LAST" alt="Detailed waveforms of the fourth cycle"></figure><h3>Column voltage at the readout instant</h3><table><thead><tr><th>Cycle</th><th>Dark / V</th><th>1 pA / V</th><th>5 pA / V</th></tr></thead><tbody>ROWS</tbody></table><p>These are interpolated simulator samples, not measured ADC precision. The dim and bright cases approach repeatable outputs quickly, while the dark sample rises by <b>DARKCHANGE mV between cycles 3 and 4</b>. Incomplete settling of the weak NMOS reset is a working explanation to test with longer resets and more cycles.</p><p>Startup uses explicit zero initial node voltages and skips the initial DC operating-point solution. This models a chosen cold-start condition, not a power-supply ramp. The four-cycle experiment does not establish steady state, noise performance, or ADC acquisition compatibility.</p></section>
<section id="history"><h2>How we got here</h2><ol><li><b>Architecture:</b> selected a monochrome 3T active pixel and retained GF180 to match the existing gdsfactory prototype.</li><li><b>Toolchain:</b> verified Xschem 3.4.8RC, ngspice 46, Magic, Netgen and the installed gf180mcuD PDK in IIC-OSIC-TOOLS.</li><li><b>First integration test:</b> brighter input discharged the sensing node faster, but the dark trace dropped by about 373 mV over 0.98 ms.</li><li><b>Numerical diagnosis:</b> reducing SPICE's minimum junction conductance, with tighter current tolerance, reduced that original dark drop to about 0.74 mV. Sweeping gmin from 1e-17 to 1e-18 S left the reported drop unchanged at that precision.</li><li><b>Current step:</b> graphical repeated-cycle schematic, switched row selection, passive column load, sampled outputs, and this shareable notebook.</li></ol><p>The original dark-drift numbers belong to the continuously selected test. They are not physical photodiode leakage measurements and should not be applied directly to the new readout circuit.</p></section>
<section><h2>What remains before silicon</h2><div class="grid"><div><h3>Next electrical work</h3><ul><li>Sweep reset duration and run more cycles to investigate dark reset memory.</li><li>Add source/drain geometry and a justified GF180 diode electrical model.</li><li>Design a transistor column bias and output buffer.</li><li>Characterize readout settling, corners, noise and mismatch.</li></ul></div><div><h3>Camera integration</h3><ul><li>Expand to a small array with row/column addressing.</li><li>Choose an external ADC and controller from the required resolution and frame rate.</li><li>Plan optical access, lens mount, die bonding and packaging.</li><li>Generate gdsfactory layout, run DRC/LVS, extract parasitics and resimulate.</li></ul></div></div><p>wafer.space is our proposed GF180 manufacturing route. Run-specific process options, acceptable photodiode structures and optical packaging still need confirmation. A board ADC is the initial system direction; no component has been finalized.</p><details><summary>Model assumptions and practical limits</summary><ul><li>Photodiode: assumed 10 fF explicit capacitance; ideal current source; diode Is=1e-18 A, Cjo=0. No measured quantum efficiency or wavelength response.</li><li>All transistor diffusion areas/perimeters are zero in this baseline. Real junction leakage and capacitance are incomplete.</li><li>Column load: 1 MΩ resistor and 1 pF capacitor. The resistor is a testbench choice, not a final column circuit.</li><li>No thermal or shot noise, random mismatch, parasitic extraction, optical crosstalk, or ADC quantization is evaluated in these deterministic traces.</li><li>No color-filter array is planned. Monochrome operation still needs a characterized optical response and calibration.</li></ul></details></section>
<section id="reproduce"><h2>Reproduce and extend</h2><p>The schematic is the source for the new simulation: <code>xschem/pixel_cycles.sch</code>. Run these commands from the repository root with Docker available:</p><pre><code>bash scripts/simulate-cycles.sh
bash scripts/run-tools.sh python3 scripts/build-overview.py</code></pre><p>The report builder checks finite waveforms, four row selections, reset assertions, row isolation during integration, and light ordering at every readout. It writes plots, sample data and this HTML. The Xschem screenshot is captured separately into <code>docs/assets/xschem-cycles.png</code>; refresh it when the schematic changes.</p><details><summary>Simulation settings and provenance</summary><p>Typical GF180 corner; default 27 °C simulation temperature. Transient output step 0.2 µs, duration 4 ms, adaptive internal steps, explicit initial conditions. gmin=1e-17 S; abstol=1e-16 A; reltol=1e-5. The current run has not yet been checked across smaller maximum timesteps.</p><p>Local image ID: <code>sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a</code>. The runner permits IIC_OSIC_IMAGE override. gf180mcuD identifies the installed tool PDK; exact manufacturing options are still to be aligned with the shuttle.</p></details><p><b>Share:</b> send <code>docs/overview.html</code>. All report images and styling are embedded; it opens offline without a server. Source files and the reference PDF remain in the repository. Rebuilding refreshes this document; it is not automatically connected to a running simulation.</p><p>Background reading: Yuhao Zhu, <a href="https://www.cs.rochester.edu/courses/572/fall2022/decks/lect10-sensor-basics.pdf">Image Sensor Basics, Rochester CSC 292/572 (Fall 2022)</a>. Saved in the repository as <code>docs/lect10-sensor-basics.pdf</code>. See PDF pages 44–49 for charge readout, noting that the transfer-gate example differs from our 3T pixel.</p><p class="small">Generated STAMP from local simulation artifacts. This notebook records design evidence and open questions; it is not a fabrication readiness claim.</p></section></main><script>function showPlot(last,button){document.getElementById('all').classList.toggle('hidden',last);document.getElementById('last').classList.toggle('hidden',!last);button.parentElement.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',b===button?'true':'false'));}</script></body></html>'''
for key,val in {'SCHEMATIC':img('xschem-cycles.png'),'CYCLES':img('cycles.png'),'LAST':img('last-cycle.png'),'ROWS':rows,'DARKCHANGE':f'{darkchange:.2f}','STAMP':stamp}.items():html=html.replace(key,val)
import runpy
progress=runpy.run_path(str(root/'scripts/overview-progress.py'))['render'](root)
html=html.replace('<section id="status"><h2>Current milestone</h2>', '<section id="status"><h2>First four-cycle milestone (historical baseline)</h2>')
array_progress=runpy.run_path(str(root/'scripts/overview-array.py'))['render'](root)
size_progress=runpy.run_path(str(root/'scripts/overview-size-study.py'))['render'](root)
camera_plan=runpy.run_path(str(root/'scripts/overview-camera-plan.py'))['render'](root)
parasitics=runpy.run_path(str(root/'scripts/overview-parasitics.py'))['render'](root)
column_bias=runpy.run_path(str(root/'scripts/overview-column-bias.py'))['render'](root)
mux=runpy.run_path(str(root/'scripts/overview-column-mux.py'))['render'](root)
readout_pex=runpy.run_path(str(root/'scripts/overview-readout-pex.py'))['render'](root)
buffer=runpy.run_path(str(root/'scripts/overview-output-buffer.py'))['render'](root)
corners=runpy.run_path(str(root/'scripts/overview-buffer-corners.py'))['render'](root)
hardening=runpy.run_path(str(root/'scripts/overview-buffer-hardening.py'))['render'](root)
buffer_pex=runpy.run_path(str(root/'scripts/overview-buffer-pex.py'))['render'](root)
integrated=runpy.run_path(str(root/'scripts/overview-integrated.py'))['render'](root)
integrated_corners=runpy.run_path(str(root/'scripts/overview-integrated-corners.py'))['render'](root)
bias_reference=runpy.run_path(str(root/'scripts/overview-bias-reference.py'))['render'](root)
pad_proposal=(root/'docs/pad-proposal.html').read_text() if (root/'docs/pad-proposal.html').exists() else ''
path_to_camera=(root/'docs/path-to-camera.html').read_text() if (root/'docs/path-to-camera.html').exists() else ''
clamp_model_review=(root/'docs/clamp-model-review.html').read_text() if (root/'docs/clamp-model-review.html').exists() else ''
filled_demonstrator=(root/'docs/filled-demonstrator.html').read_text() if (root/'docs/filled-demonstrator.html').exists() else ''
routed_demonstrator=(root/'docs/routed-demonstrator.html').read_text() if (root/'docs/routed-demonstrator.html').exists() else ''
completion_dashboard=(root/'docs/completion-dashboard.html').read_text() if (root/'docs/completion-dashboard.html').exists() else ''
moscap_branch=(root/'docs/moscap-branch.html').read_text() if (root/'docs/moscap-branch.html').exists() else ''
corner_interface=(root/'docs/corner-interface.html').read_text() if (root/'docs/corner-interface.html').exists() else ''
charge_reduction=(root/'docs/charge-reduction.html').read_text() if (root/'docs/charge-reduction.html').exists() else ''
charge_reference=(root/'docs/charge-reference.html').read_text() if (root/'docs/charge-reference.html').exists() else ''
capacitance_candidate=(root/'docs/capacitance-candidate.html').read_text() if (root/'docs/capacitance-candidate.html').exists() else ''
ring_candidate=(root/'docs/ring-candidate.html').read_text() if (root/'docs/ring-candidate.html').exists() else ''
combined_patch=(root/'docs/combined-patch.html').read_text() if (root/'docs/combined-patch.html').exists() else ''
network_investigation=(root/'docs/network-investigation.html').read_text() if (root/'docs/network-investigation.html').exists() else ''
extraction_diagnostics=(root/'docs/extraction-diagnostics.html').read_text() if (root/'docs/extraction-diagnostics.html').exists() else ''
rail_faces=(root/'docs/rail-faces.html').read_text() if (root/'docs/rail-faces.html').exists() else ''
rail_isolation=(root/'docs/rail-isolation.html').read_text() if (root/'docs/rail-isolation.html').exists() else ''
geometry_controls=(root/'docs/geometry-controls.html').read_text() if (root/'docs/geometry-controls.html').exists() else ''
terminal_calibration=(root/'docs/terminal-calibration.html').read_text() if (root/'docs/terminal-calibration.html').exists() else ''
filler_stitch=(root/'docs/filler-stitch.html').read_text() if (root/'docs/filler-stitch.html').exists() else ''
ring_sections=(root/'docs/ring-sections.html').read_text() if (root/'docs/ring-sections.html').exists() else ''
power_ring=(root/'docs/power-ring.html').read_text() if (root/'docs/power-ring.html').exists() else ''
board_supply=(root/'docs/board-supply.html').read_text() if (root/'docs/board-supply.html').exists() else ''
clamp_convergence=(root/'docs/clamp-convergence.html').read_text() if (root/'docs/clamp-convergence.html').exists() else ''
pad_closure=(root/'docs/pad-closure.html').read_text() if (root/'docs/pad-closure.html').exists() else ''
pad_layout=(root/'docs/pad-layout.html').read_text() if (root/'docs/pad-layout.html').exists() else ''
pad_references=(root/'docs/pad-references.html').read_text()
pad_evaluation=(root/'docs/pad-evaluation.html').read_text() if (root/'docs/pad-evaluation.html').exists() else ''
if clamp_convergence:
 pad_closure=pad_closure.replace('<h2>Pad DRC configuration and supply-clamp evaluation</h2>', '<h2>Earlier checkpoint: pad DRC and supply clamps</h2><p>The later <a href="#clamp-convergence">full-frame verification</a> above supersedes the transient limitation recorded here.</p>',1)
if rail_isolation:
 for name in ['terminal_calibration','geometry_controls']:
  fragment=globals()[name]
  end=fragment.find('</h2>')+5
  notice='<p><strong>Correction, 18 September:</strong> the earlier negative-threshold command was rejected by Magic. See <a href="#rail-isolation">the accepted canonical-selection procedure and corrected interpretation</a> above. Earlier measurements are retained as historical evidence.</p>'
  globals()[name]=fragment[:end]+notice+fragment[end:]
html=html.replace('<main>', '<main>'+completion_dashboard+path_to_camera+clamp_model_review+filled_demonstrator+routed_demonstrator+pad_proposal+camera_plan+moscap_branch+corner_interface+charge_reduction+charge_reference+capacitance_candidate+ring_candidate+combined_patch+network_investigation+extraction_diagnostics+rail_faces+rail_isolation+geometry_controls+terminal_calibration+filler_stitch+ring_sections+power_ring+board_supply+clamp_convergence+pad_closure+pad_layout+pad_evaluation+pad_references+bias_reference+integrated_corners+integrated+buffer_pex+hardening+corners+buffer+readout_pex+mux+column_bias+parasitics+size_progress+array_progress+progress, 1)
html=html.replace('<nav>', '<nav><a href="#pad-references">Pad references</a>',1)
if network_investigation:html=html.replace('<nav>', '<nav><a href="#network-investigation">Reduction and device regressions</a>',1)
if extraction_diagnostics:html=html.replace('<nav>', '<nav><a href="#extraction-diagnostics">Export and via diagnostics</a>',1)
if rail_faces:html=html.replace('<nav>', '<nav><a href="#rail-faces">Full-width rail faces</a>',1)
if rail_isolation:html=html.replace('<nav>', '<nav><a href="#rail-isolation">Real rail isolation</a>',1)
if geometry_controls:html=html.replace('<nav>', '<nav><a href="#geometry-controls">Matched terminals</a>',1)
if terminal_calibration:html=html.replace('<nav>', '<nav><a href="#terminal-calibration">Terminal calibration</a>',1)
if filler_stitch:html=html.replace('<nav>', '<nav><a href="#filler-stitch">Boundary stitching</a>',1)
if ring_sections:html=html.replace('<nav>', '<nav><a href="#ring-sections">Small ring extraction</a>',1)
if power_ring:html=html.replace('<nav>', '<nav><a href="#power-ring">Physical supply ring</a>',1)
if board_supply:html=html.replace('<nav>', '<nav><a href="#board-supply">Board supply</a>',1)
if clamp_convergence:html=html.replace('<nav>', '<nav><a href="#clamp-convergence">Full clamp transient</a>',1)
if pad_closure:html=html.replace('<nav>', '<nav><a href="#pad-closure">Supply clamps and pad checks</a>',1)
if pad_layout:html=html.replace('<nav>', '<nav><a href="#pad-layout">Physical pad interface</a>',1)
if pad_evaluation:html=html.replace('<nav>', '<nav><a href="#pad-evaluation">Pad evaluation</a>',1)
if bias_reference:html=html.replace('<nav>', '<nav><a href="#bias-reference">Physical bias and startup</a>',1)
if integrated_corners:html=html.replace('<nav>', '<nav><a href="#integrated-corners">Connected corner matrix</a>',1)
if integrated:html=html.replace('<nav>', '<nav><a href="#integrated">Connected layout</a>',1)
if buffer_pex:html=html.replace('<nav>', '<nav><a href="#buffer-pex">Buffer extraction</a>',1)
if hardening:html=html.replace('<nav>', '<nav><a href="#buffer-hardening">Revised buffer</a>',1)
if corners:html=html.replace('<nav>', '<nav><a href="#buffer-corners">Process / temperature</a>',1)
if buffer:html=html.replace('<nav>', '<nav><a href="#output-buffer">Output buffer</a>',1)
if readout_pex:html=html.replace('<nav>', '<nav><a href="#readout-pex">Readout extraction</a>',1)
if mux:html=html.replace('<nav>', '<nav><a href="#column-mux">Mux and layout</a>',1)
if column_bias:html=html.replace('<nav>', '<nav><a href="#column-bias">Column bias</a>',1)
if parasitics:html=html.replace('<nav>', '<nav><a href="#parasitics">Extracted RC</a>',1)
if camera_plan:html=html.replace('<a href="#repeatability">', '<a href="#camera-plan">Camera plan</a><a href="#resolution-demo">Resolution demo</a><a href="#repeatability">',1)
if size_progress:html=html.replace('<a href="#repeatability">', '<a href="#size-study">Diode sizes</a><a href="#repeatability">', 1)
if array_progress:
 html=html.replace('<a href="#repeatability">', '<a href="#verified-array">Verified array</a><a href="#array-operation">Array scan</a><a href="#repeatability">', 1)
 html=html.replace('No 3×3 layout exists yet.', 'This was the plan before the verified array milestone above.')
 html=html.replace('Latest investigation · repeatability', 'Earlier investigation · repeatability')
 html=html.replace('Next physical target', 'Earlier physical target')
html=html.replace('<a href="#status">Status</a>', '<a href="#repeatability">Repeatability</a><a href="#array">3×3 target</a><a href="#status">First experiment</a>')
html=html.replace('</main>', '''<section id="checkpoint"><h2>Restore this checkpoint and tool environment</h2><p>The repository includes a checksummed archive of verified GDS, netlists, DRC/LVS reports and simulation waveforms. The localhost desktop uses the checkout mounted at <code>/foss/designs</code>; saved project files are already on the host.</p><p>From a clean checkout:</p><pre><code>docker pull hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a
python3 scripts/restore-checkpoint.py
bash scripts/start-vnc.sh</code></pre><p>Open <code>http://localhost:8080/vnc.html?autoconnect=true&amp;resize=scale</code> for the desktop. See <a href="https://github.com/njcoburn/OPENIMAGESENSOR/blob/main/docs/docker-setup.md">Docker setup and full reproduction instructions</a>. The restore refuses to overwrite existing artifacts. Browser sessions and the Docker image itself are not in the archive.</p></section></main>''',1)
html=html.replace('</main>', (root/'docs/carrier-fixture-section.html').read_text()+'</main>', 1)
html=html.replace('</main>', (root/'docs/scaled-electrical-progress-section.html').read_text()+'</main>', 1)
html=html.replace('</main>', (root/'docs/wafer-space-version-audit-section.html').read_text()+'</main>', 1)
html=html.replace('</main>', (root/'docs/ngspice-version-comparison-section.html').read_text()+'</main>', 1)
html=html.replace('</main>', (root/'docs/gf180-shuttle-references-section.html').read_text()+'</main>', 1)
if (root/'docs/functional-camera-section.html').exists():
 html=html.replace('</main>', (root/'docs/functional-camera-section.html').read_text()+'</main>', 1)
html=html.replace('<main>', '<main><p><strong>Returning to the project?</strong> <a href="../PICK_UP_HERE.md">Read the dated handoff, current blockers and next steps</a>.</p>', 1)
(root/'docs/overview.html').write_text(html)
print('Checks passed. Wrote docs/overview.html and simulations/cycle-samples.json')
