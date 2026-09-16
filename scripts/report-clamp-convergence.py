"""Publish full-frame convergence evidence and preserve unsuccessful diagnostics."""
from pathlib import Path
import base64, hashlib, json, tarfile, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DIRECT=['nominal_pair_abs1e-12_step0.1us','hot_pair_abs1e-12_step0.1us']
STRICT=['adapter_nominal_pair_abs1e-14_step0.1us','adapter_hot_pair_abs1e-14_step0.1us']
FINE='hot_pair_abs1e-12_step0.05us_rel5e-05'
STRICT_FINE='adapter_hot_pair_abs1e-14_step0.05us_monitor'

def read(label):
    return json.loads((ROOT/'build/clamp-frames'/label/'result.json').read_text())
def samples(result, field):
    return np.array([s[field] for frame in result['frames'] for s in frame['samples']])

labels=DIRECT+STRICT+[STRICT_FINE]
rows={label:read(label) for label in labels}
assert all(r['status']=='complete' and r['all_frames_pass'] for r in rows.values()), 'Required full-frame verification failed'
comparison={}
for a,b,name in [(DIRECT[0],STRICT[0],'nominal_direct_vs_strict'),(DIRECT[1],STRICT[1],'hot_direct_vs_strict'),(DIRECT[1],STRICT_FINE,'hot_vs_finer_strict'),(STRICT[1],STRICT_FINE,'strict_hot_timestep_and_relative_tolerance')]:
    difference=float(np.max(abs(samples(rows[a],'output_V')-samples(rows[b],'output_V')))*1e6)
    hold_difference=float(np.max(abs(samples(rows[a],'hold_V')-samples(rows[b],'hold_V')))*1e6)
    comparison[name]={'max_output_difference_uV':difference,'max_hold_difference_uV':hold_difference}
    assert max(difference,hold_difference)<10, (name,difference,hold_difference)
# The ideal supply fixes VDD regardless of clamp current. The earlier strict
# no-clamp waveform is therefore also a useful independent output reference.
reference={}
for label in DIRECT:
    r=rows[label];tag=f"*{r['temp_C']}C*"
    source=next((ROOT/'build/clamp-imaging/matched-control/scan').glob(tag))
    wave=np.loadtxt(source/'wave.txt',skiprows=1)
    times=samples(r,'time_s')
    delta=float(np.max(abs(samples(r,'output_V')-np.interp(times,wave[:,0],wave[:,3])))*1e6)
    hold_delta=float(np.max(abs(samples(r,'hold_V')-np.interp(times,wave[:,0],wave[:,5])))*1e6)
    reference[label]={'max_output_difference_uV':delta,'max_hold_difference_uV':hold_delta,'source':str(source.relative_to(ROOT))}
    assert max(delta,hold_delta)<10

summary={'status':'resolved_for_tested_nominal_and_hot_three_frame_cases',
         'production_configuration':{'connection':'direct original supply-pad pair','abstol_A':1e-12,'reltol':5e-5,'gmin_S':1e-17,'chgtol_C':1e-16,'method':'gear','step_us':.1,'timeout_s':1200,'ramp_us':1000,'post_ramp_reset_us':200},
         'primary_cases':DIRECT, 'independent_strict_cases':STRICT+[STRICT_FINE],
         'total_verified_scans':len(rows),'samples_per_scan':27,
         'max_sampling_error_mV':max(r['all_frames_max_hold_error_mV'] for r in rows.values()),
         'max_frame2_to_frame3_change_uV':max(r['frame2_to_frame3_max_output_change_uV'] for r in rows.values()),
         'comparisons':comparison,'strict_reference_comparisons':reference,
         'interface_monitor':rows[STRICT_FINE]['interface_checks'],
         'scope':'Typical MOS, nominal 27C/3.3V and hot 125C/3.0V diode_ff; extracted core/local protection, foundry supply clamps, ideal rails and generic finite-transition ADC model. Not ESD, full power-network, or full PVT qualification.'}
for path,expected in [('checkpoints/integrated/sensor_3x3.gds','8a2183fd85d5a6b81bcaceb10eeb00f906018574902c4bdfe2199a5c41b222b7'),('checkpoints/pad-layout/analog_pad_interface.gds','3517bdda5385d7037ce8158520db6ab9d38e220ffc478867a3a5a6addcff3ecf')]:
    digest=hashlib.sha256((ROOT/path).read_bytes()).hexdigest();assert digest==expected
    summary.setdefault('unchanged_gds_sha256',{})[path]=digest

diagnostics={p.parent.name:json.loads(p.read_text()) for p in (ROOT/'build/clamp-diagnostic').glob('*/result.json')}
summary['diagnostic_status']={k:{'status':v['status'],'wall_s':v['wall_s']} for k,v in diagnostics.items()}
summary['unfinished_extra_refinement']=json.loads((ROOT/'build/clamp-frames'/FINE/'result.json').read_text())
port=json.loads((ROOT/'simulations/clamp-interface-check.json').read_text())
summary['finite_source_port_diagnostic']=port

fig,axes=plt.subplots(1,3,figsize=(15,4.7),layout='constrained')
for label,color in zip(DIRECT,['#1779ad','#c35b19']):
    r=rows[label];name=f"{r['temp_C']}°C / {r['supply_V']} V"
    axes[0].plot(np.arange(1,28),samples(r,'output_V'),'.-',label=name,color=color)
    axes[1].plot(np.arange(1,28),abs(samples(r,'hold_error_mV')),'.-',label=name,color=color)
axes[0].set(title='All 27 samples: three complete frames',xlabel='Sample number',ylabel='ADC input (V)');axes[0].legend()
axes[1].axhline(.5,color='red',ls='--',label='0.5 mV limit');axes[1].set(title='Sampling error',xlabel='Sample number',ylabel='Absolute error (mV)');axes[1].legend()
for ax in axes[:2]:
    for x in [9.5,18.5]:ax.axvline(x,color='gray',lw=.8,ls=':')
    ax.set_xticks([1,9,18,27])
axes[2].plot(np.arange(1,28),1e6*abs(samples(rows[DIRECT[1]],'output_V')-samples(rows[STRICT_FINE],'output_V')),'.-',label='Direct 100 ns vs strict 50 ns')
axes[2].plot(np.arange(1,28),1e6*abs(samples(rows[DIRECT[1]],'output_V')-samples(rows[STRICT[1]],'output_V')),'.-',label='Direct vs strict interface')
axes[2].set(title='Hot-case numerical agreement',xlabel='Sample number',ylabel='Output difference (µV)');axes[2].legend()
for ax in axes:ax.grid(alpha=.2)
fig.suptitle('Extracted camera with supply clamps — full multi-frame verification')
asset=ROOT/'docs/assets/clamp-convergence.png';fig.savefig(asset,dpi=140);plt.close(fig)

body=''
for label,r in rows.items():
    connection='Strict interface' if label.startswith('adapter_') else 'Direct'
    body+=f"<tr><td>{connection}</td><td>{r['temp_C']}°C / {r['supply_V']} V</td><td>{r['step_us']*1000:g} ns</td><td>{r['all_frames_max_hold_error_mV']:.4f} mV</td><td>{r['frame2_to_frame3_max_output_change_uV']:.2f} µV</td><td>27/27; pass</td></tr>"
diag=''.join(f"<tr><td>{name}</td><td>{r['status']}</td><td>{r['wall_s']:.1f} s</td></tr>" for name,r in sorted(diagnostics.items()))
max_diff=max(max(v.values()) for v in comparison.values())
image='data:image/png;base64,'+base64.b64encode(asset.read_bytes()).decode()
section=f'''<section id="clamp-convergence"><h2>Resolved: full camera-plus-clamp simulation</h2>
<p><strong>The original direct connection now completes all three frames at nominal and hot conditions.</strong> The working setup uses <code>abstol=1e-12</code> (1 pA) and a 1200 s watchdog, retaining <code>reltol=5e-5</code>, <code>gmin=1e-17</code>, <code>chgtol=1e-16</code>, Gear integration, and the original circuit. A 50 ns run of the independent formulation supplies a stricter cross-check, retaining 10 fA absolute tolerance and tightening relative tolerance to 1e-5. Runtime limits prevent runaway jobs; they do not count incomplete runs as passes.</p>
<p>Prior runs at 10 fA slowed sharply around switching events, and the 600 s cutoff stopped them before completion. The validated configuration changes both current tolerance and runtime allowance; these experiments do not establish that either change alone is necessary. This is a diagnosis supported by the controlled comparisons, not a proof of a particular ngspice source-code defect. The <a href="https://ngspice.sourceforge.io/docs/ngspice-manual.pdf">ngspice manual</a> defines ABSTOL as the absolute current-error tolerance and documents 1 pA as its default. Accuracy is established here by the measured comparisons, not by that default alone.</p>
<h3>Verification results</h3>
<ul><li>{len(rows)} full scans, 27 samples each; all sampling, brightness-order and startup screens pass.</li><li>Worst sampling error: <strong>{summary['max_sampling_error_mV']:.4f} mV</strong>, below the unchanged 0.5 mV limit.</li><li>Largest change between frames two and three: <strong>{summary['max_frame2_to_frame3_change_uV']:.2f} µV</strong>, below the stated 50 µV repeatability screen.</li><li>Maximum output/held-voltage difference across timestep and strict-interface comparisons: <strong>{max_diff:.2f} µV</strong>, below a 10 µV convergence screen.</li><li>Sensor and pad-interface GDS hashes match the prior checkpoint.</li></ul>
<img src="{image}" alt="Three-frame sample outputs, sampling error, and numerical convergence comparisons" style="width:100%">
<table><thead><tr><th>Connection</th><th>Condition</th><th>Time step</th><th>Worst sampling error</th><th>Frame 2 → 3</th><th>Result</th></tr></thead><tbody>{body}</tbody></table>
<h3>Independent check at the original strict tolerance</h3>
<p>A second formulation keeps the 10 fA tolerance and introduces an algebraic voltage/current interface in the testbench. Its equations enforce <code>V(CLAMPRAIL)=V(VDD)</code> and return the measured clamp current to VDD. It retains the full nonlinear clamp devices. It is a numerical check; production simulations use the direct connection.</p>
<pre><code>Eclamp CLAMPDRIVE 0 VDD 0 1
Vclamp CLAMPDRIVE CLAMPRAIL 0
Fclamp VDD 0 Vclamp 1
Xsupply CLAMPRAIL 0 sensor_supply_pads</code></pre>
<p>The strict hot refinement also tightens relative tolerance to 1e-5 and monitors voltage, current balance and exchanged power. Transient comparison bounds account for saved waveform precision. Separate finite-source DC/AC diagnostics reveal picoampere-scale numerical differences: the 1 Ω cases meet a 1 pA + 10 ppm current comparison; the 1 kΩ cases exceed that strict screen. Those failures remain recorded. This interface is not used to replace the direct clamp model or to qualify ESD leakage/stress performance.</p>
<details><summary>Other diagnostic attempts and their results</summary><table><thead><tr><th>Attempt</th><th>Status</th><th>Runtime</th></tr></thead><tbody>{diag}</tbody></table><p>Timeouts and failed alternatives remain evidence. An additional direct 50 ns run was stopped unfinished after the stricter independent refinement passed; no result is inferred for that extra run. Memory usage was moderate; reducing saved outputs alone did not fix the original strict run. Matrix solver, initialization, iteration count and integration-method changes alone did not establish a reliable solution in their allotted runs.</p></details>
<h3>Scope and next step</h3><p>These are nominal and hot typical-MOS checks with the extracted sensor/local protection, foundry supply clamps, 1 ms startup ramp, 200 µs reset hold and generic ADC load. The camera rail remains ideal in this verification. A coupled board supply/regulator and complete pad-ring extraction are next. ESD qualification and a full process-corner campaign remain separate work.</p>
<p>Reproduce: <code>bash scripts/run-tools.sh python3 scripts/simulate-clamp-frames.py</code>. The detailed notes include the finer-step and independent-check commands. Reports, decks, logs, waveforms and failed diagnostics are archived with SHA-256 hashes.</p></section>'''
(ROOT/'docs/clamp-convergence.html').write_text(section)
(ROOT/'simulations/clamp-convergence-verification.json').write_text(json.dumps(summary,indent=2)+'\n')

checkpoint=ROOT/'checkpoints/clamp-convergence';checkpoint.mkdir(exist_ok=True)
paths=set()
for folder in ['build/clamp-diagnostic','build/clamp-frames','build/clamp-interface-check','build/clamp-interface-initial']:
    paths.update(p for p in (ROOT/folder).rglob('*') if p.is_file())
for pattern in ['scripts/diagnose-clamp-transient.py','scripts/simulate-clamp-frames.py','scripts/check-clamp-interface.py','scripts/report-clamp-convergence.py','docs/clamp-convergence.*','docs/assets/clamp-convergence.png','simulations/clamp-diagnostic*.json','simulations/clamp-frames.json','simulations/clamp-interface-check.json','simulations/clamp-convergence-verification.json']:
    paths.update(ROOT.glob(pattern))
for name in ['scripts/run-tools.sh','scripts/bias-reference.py','scripts/evaluate-pads.py','scripts/simulate-pad-layout.py','circuits/board-bias.spice','circuits/sensor-supply-pads.spice','circuits/bias-scan-template.spice','circuits/bias-dc-template.spice','checkpoints/integrated/pex/sensor_reduced.spice','build/integrated-pex/sensor_reduced.spice','build/pad-layout/secondary_pex.spice','checkpoints/pad-evaluation/analog-pad.spice','checkpoints/pad-closure/supply-pad-models.spice','checkpoints/pad-closure/ngspice-init/.spiceinit','simulations/integrated-verification.json']:
    paths.add(ROOT/name)
paths.update(ROOT/path for path in summary['unchanged_gds_sha256'])
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
with tarfile.open(checkpoint/'evidence.tar.gz','w:gz',compresslevel=3) as tar:
    for p in sorted(paths):tar.add(p,arcname=str(p.relative_to(ROOT)))
with tarfile.open(checkpoint/'evidence.tar.gz','r:gz') as tar:
    for name,digest in manifest.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
(checkpoint/'manifest.json').write_text(json.dumps({'files':manifest,'archive_sha256':hashlib.sha256((checkpoint/'evidence.tar.gz').read_bytes()).hexdigest(),'dependencies':summary['unchanged_gds_sha256'],'prior_model_checkpoint':'checkpoints/pad-closure/evidence.tar.gz'},indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['finite_source_port_diagnostic','diagnostic_status']},indent=2))
print('Archive verified:',len(manifest),'files')
