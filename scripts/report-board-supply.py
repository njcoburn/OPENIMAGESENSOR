"""Report measured coupled board-supply results without treating failures as passes."""
from pathlib import Path
import hashlib
import html
import json
import tarfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'simulations/board-supply.json').read_text())
cases = data['cases']
fig, axes = plt.subplots(1, 3, figsize=(17, 4.8), constrained_layout=True)
rows = []
comparisons = {}
coarse = cases.get('board_hot_pair_abs1e-12_step0.1us')
fine = cases.get('board_hot_pair_abs1e-12_step0.05us')
if coarse and fine and coarse['status'] == fine['status'] == 'complete':
    for key in ['output_V', 'hold_V']:
        comparisons[key + '_max_difference_uV'] = max(
            abs(a[key]-b[key])*1e6
            for f, g in zip(coarse['frames'], fine['frames'])
            for a, b in zip(f['samples'], g['samples']))
    comparisons['pass_10uV_screen'] = all(v < 10 for v in comparisons.values())
    (ROOT/'simulations/board-supply-convergence.json').write_text(json.dumps(comparisons, indent=2)+'\n')
for name, r in cases.items():
    label = f"{r['temp_C']}°C, {r['supply_V']} V, {r['board']['source_R_ohm']:g} Ω, {r['step_us']*1000:g} ns"
    if r['status'] != 'complete':
        rows.append(f'<tr><td>{html.escape(label)}</td><td colspan="5">Incomplete: {html.escape(r.get("error", "see log"))}</td></tr>')
        continue
    wave = np.loadtxt(next((ROOT/'build/clamp-frames'/name/'scan').glob('*/wave.txt')), skiprows=1)
    # Downsample only the display. Every saved point contributes to metrics.
    stride = max(1, len(wave)//12000)
    axes[0].plot(wave[::stride, 0]*1e3, wave[::stride, 8], label=label)
    active = wave[:, 0] >= .0012
    axes[1].plot(wave[active][::stride, 0]*1e3,
                 (r['supply_V']-wave[active][::stride, 8])*1e3, label=label)
    errors = [abs(s['hold_error_mV']) for f in r['frames'] for s in f['samples']]
    axes[2].plot(range(1, 28), errors, '.-', label=label)
    m = r['board_metrics']
    rows.append(f"<tr><td>{html.escape(label)}</td><td>{m['active_max_rail_error_mV']:.4f}</td>"
                f"<td>{r['all_frames_max_hold_error_mV']:.4f}</td>"
                f"<td>{m['max_sample_change_vs_ideal_uV']:.2f}</td>"
                f"<td>{r['frame2_to_frame3_max_output_change_uV']:.2f}</td>"
                f"<td>{'PASS' if r['board_screen_pass'] else 'FAIL'}</td></tr>")
axes[0].set(title='Supply startup', xlabel='Time (ms)', ylabel='On-chip VDD (V)')
axes[1].set(title='Supply drop during imaging', xlabel='Time (ms)', ylabel='Source target − VDD (mV)')
axes[2].set(title='All three frames', xlabel='Sample number', ylabel='Absolute sampling error (mV)')
axes[2].axhline(.5, color='red', linestyle='--', label='0.5 mV limit')
for ax in axes:
    ax.grid(alpha=.25)
    ax.legend(fontsize=8)
fig.suptitle('Extracted camera + supply clamps + assumed board RLC network')
fig.savefig(ROOT/'docs/assets/board-supply.png', dpi=150)
plt.close(fig)
section = '''<section id="board-supply"><h2>Board supply impedance and decoupling</h2>
<p>The extracted camera and direct foundry supply-clamp pair now run with an explicit passive board supply network. An ideal upstream source ramps in 1 ms; a 200 µs reset hold follows. Three complete frames give 27 pixel samples per run.</p>
<p><strong>Assumed network:</strong> 0.5 Ω source resistance (5 Ω hot sensitivity case), 2 nH series lead inductance, and 100 nF local decoupling with 0.1 Ω ESR and 1 nH ESL. Ground and the upstream regulator remain ideal. These values are test assumptions, not measured board or package parasitics.</p>
<img src="assets/board-supply.png" alt="Board supply startup, imaging rail droop, and all 27 sampling errors" style="width:100%;height:auto">
<table><thead><tr><th>Condition</th><th>Max rail error during imaging (mV)</th><th>Max sampling error (mV)</th><th>Max output change vs ideal supply (µV)</th><th>Frame 2→3 change (µV)</th><th>Screen</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table>
<p>Sampling and tracking errors use a DC transfer sweep with the same board network. The ideal-supply comparison separately measures the total output shift; this includes changed pixel reset and bias voltages. Acceptance screens are 0.5 mV sampling/tracking error, 1% rail and startup bias error, correct brightness ordering, and 50 µV frame repeatability. The 1% rail budget is an engineering screen.</p>
<p>Simulation uses the previously checked 1 pA current tolerance, Gear integration, and 100 ns step. All saved points contribute to rail extrema; the plotted waveforms are downsampled for display. Finite-supply runs are new circuit cases and do not inherit ideal-rail convergence proof.</p>
<p><strong>Scope:</strong> typical MOS at nominal and hot conditions, extracted sensor and local protection, schematic foundry supply clamps, and the existing generic off-chip ADC load. No full pad-ring extraction, ground bounce, regulator feedback-loop model, ESD qualification or complete process-corner signoff is implied. The bias/startup power metric inherited from the prior runner combines die voltage with source current; use the explicit board metrics here for supply evaluation.</p>
<p>Reproduction: <code>bash scripts/run-tools.sh python3 scripts/simulate-board-supply.py</code>, then <code>scripts/report-board-supply.py</code> and <code>scripts/build-overview.py</code> through the same runner. Details: <a href="board-supply.md">board-supply notes</a>. Next: qualify a selected regulator/package and extract the actual pad-ring interconnect.</p></section>'''
if comparisons:
    section = section.replace('</section>', '<p><strong>Finer-step hot check:</strong> 50 ns with relative tolerance 1e-5 versus 100 ns with 5e-5. Maximum output difference: ' + f"{comparisons['output_V_max_difference_uV']:.3f} µV; maximum held-voltage difference: {comparisons['hold_V_max_difference_uV']:.3f} µV. " + ('Pass' if comparisons['pass_10uV_screen'] else 'Fail') + ' against the declared 10 µV numerical agreement screen.</p></section>')
(ROOT/'docs/board-supply.html').write_text(section+'\n')
checkpoint = ROOT/'checkpoints/board-supply'
checkpoint.mkdir(exist_ok=True)
files = [ROOT/'scripts/simulate-board-supply.py', ROOT/'scripts/report-board-supply.py',
         ROOT/'scripts/simulate-clamp-frames.py', ROOT/'simulations/board-supply.json',
         ROOT/'docs/board-supply.html', ROOT/'docs/board-supply.md', ROOT/'docs/assets/board-supply.png']
if comparisons:
    files.append(ROOT/'simulations/board-supply-convergence.json')
for name in cases:
    files.extend(p for p in (ROOT/'build/clamp-frames'/name).rglob('*') if p.is_file())
manifest = {'scope': data['scope'], 'parent_checkpoint': 'checkpoints/clamp-convergence/evidence.tar.gz',
            'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
archive = checkpoint/'evidence.tar.gz'
with tarfile.open(archive, 'w:gz', compresslevel=3) as tar:
    for name in manifest['files']:
        tar.add(ROOT/name, arcname=name)
with tarfile.open(archive) as tar:
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(tar.extractfile(name).read()).hexdigest() == digest
manifest['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
(checkpoint/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('Reported', len(cases), 'cases;', sum(r.get('board_screen_pass', False) for r in cases.values()), 'passed; archived', len(manifest['files']), 'verified files.')
