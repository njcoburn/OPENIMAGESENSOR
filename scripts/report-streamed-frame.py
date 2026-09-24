"""Publish scoped nominal-frame evidence into the local engineering notebook."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse
import html
import json
import re
import shutil

R = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('run')
a = p.parse_args()
d = R/'build/functional-camera-diagnostic'/a.run
r = json.loads((d/'result.json').read_text())
diag = json.loads((d/'analysis.json').read_text())
frame = json.loads((d/'frame-analysis.json').read_text()) if (d/'frame-analysis.json').exists() else None
complete = r['completed'] and r['end_s'] >= .00425-1e-12 and len(diag['retained_samples']) == 9
stamp = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
samples = frame['samples'] if frame else diag['retained_samples']
headline = 'One nominal nine-pixel frame completes' if complete else 'Nominal nine-pixel frame remains incomplete'
status = 'Nominal screens pass; refinement remains open.' if frame and frame['nominal_screens_pass'] else 'Nominal accuracy checks are not all verified.'
summary = dict(updated=stamp, run=a.run, frame_completed=complete, accepted_full_chip=False,
               result={k: v for k, v in r.items() if k != 'ranges'}, diagnostic=diag, frame_analysis=frame)
(R/'simulations/streamed-frame.json').write_text(json.dumps(summary, indent=2)+'\n')
markdown = f'''## Recorded result — {stamp}

**{headline}. {status}**

Run `{a.run}` retained {r['points']:,} accepted points through {r['end_s']*1e3:.12g} ms in {r['seconds']:.2f} seconds. Watchdog stop: {r['timed_out']}. The circuit and model are unchanged from the earlier baseline; only the transient endpoint and watchdog are extended.

'''
body = f'<section id="streamed-frame"><h2>{headline}</h2><p><strong>{stamp}. {status}</strong></p>'
body += f'<p>The unchanged KLU/trapezoidal candidate retained <strong>{r["points"]:,} points through {r["end_s"]*1e3:.6f} ms</strong> in {r["seconds"]/60:.2f} minutes. Watchdog stop: {r["timed_out"]}. The model still freezes 1,680 MOS capacitors at measured bias and includes lumped wiring capacitance.</p>'
errors = [line.strip() for line in (d/'ngspice.log').read_text().splitlines() if 'Timestep too small' in line or 'simulation(s) aborted' in line]
if errors:
    failure = ' '.join(errors)
    markdown += '**Solver failure:** ' + failure + '\n\n'
    body += '<p><strong>Solver failure:</strong> ' + html.escape(failure) + '</p>'
    summary['solver_failure'] = errors
    (R/'simulations/streamed-frame.json').write_text(json.dumps(summary, indent=2)+'\n')
if not complete:
    next_step = 'The third row is missing. The failure coincides with the row-2 reset falling-edge endpoint at 3.27002 ms, although ngspice names bdrive_row1#branch. The reported branch alone does not establish the cause. Next: isolate this transition with internal gate/device capture before another full-frame attempt.'
    markdown += next_step + '\n\n'
    body += '<p>' + next_step + '</p>'
if frame:
    metrics = [
        ('All nine samples', frame['checks']['all_nine_samples']),
        ('Brightness ordering in every row', frame['checks']['brightness_order']),
        ('Maximum hold-minus-ADC tracking error', f'{frame["max_hold_minus_adc_mV"]:.6f} mV (limit 0.5 mV)'),
        ('Maximum held-output error against static reference', f'{frame["max_hold_minus_dc_mV"]:.6f} mV (limit 0.5 mV)'),
        ('Maximum sampled supply/bias difference from static reference', f'{100*frame["max_bias_relative_difference"]:.6f}% (limit 1%)'),
        ('Maximum relative MOS-cap C(V) deviation', f'{frame["max_cap_relative_error"]:.3g} (limit 1e-6)'),
    ]
    markdown += '| Nominal check | Result |\n|---|---|\n'
    body += '<table><thead><tr><th>Nominal check</th><th>Result</th></tr></thead><tbody>'
    for name, value in metrics:
        markdown += f'| {name} | {value} |\n'
        body += f'<tr><td>{html.escape(name)}</td><td>{html.escape(str(value))}</td></tr>'
    body += '</tbody></table>'
    markdown += '\nThe static references hold the captured photodiode sense voltages with explicit testbench sources. They assess readout settling at that charge state, not the integration law or calibrated optical response.\n\n'
    body += '<p>The static reference holds the captured photodiode voltages with explicit testbench sources while retaining the chip, finite-impedance supply, pad-side controls and output load. It checks readout settling at that charge state, not calibrated optical response.</p>'
markdown += '| Row | Column | Assumed light | Held voltage | Held − DC reference |\n|---:|---:|---:|---:|---:|\n'
body += '<h3>Pixel samples (zero-based row and column)</h3><table><thead><tr><th>Row</th><th>Column</th><th>Light current</th><th>Held voltage</th><th>Held − DC</th></tr></thead><tbody>'
for sample in samples:
    error = f'{sample["hold_minus_dc_mV"]:.6f} mV' if 'hold_minus_dc_mV' in sample else 'not checked'
    markdown += f'| {sample["row"]} | {sample["column"]} | {sample["light_pA"]} pA | {sample["hold_V"]:.6f} V | {error} |\n'
    body += f'<tr><td>{sample["row"]}</td><td>{sample["column"]}</td><td>{sample["light_pA"]} pA</td><td>{sample["hold_V"]:.6f} V</td><td>{error}</td></tr>'
body += '</tbody></table>'
for filename, target, label in [('failure-edge.png', 'streamed-frame-failure-edge.png', 'Row-2 reset edge preceding solver abort'),
                                ('nine-pixel-frame.png', 'streamed-frame.png', 'Nominal nine-pixel test pattern and held voltages'),
                                ('response.png', 'streamed-frame-response.png', 'Retained controls, output, supply and adaptive timesteps')]:
    if (d/filename).exists():
        shutil.copyfile(d/filename, R/'docs/assets'/target)
        markdown += f'\n![{label}](assets/{target})\n'
        body += f'<figure><img src="assets/{target}" alt="{label}"><figcaption>{label}; electrical candidate only.</figcaption></figure>'
remaining = 'Timestep/tolerance refinement (10 µV sample-difference screen), three repeated frames, PVT/load, startup/protection, distributed wire resistance, board/ADC timing and optical/manufacturing qualification remain open.'
markdown += f'\n**Not a full-chip qualification pass.** {remaining}\n'
body += f'<p><strong>Not a full-chip qualification pass.</strong> {remaining}</p><p><a href="streamed-frame.md">Method, complete results and reproduction</a> · <a href="../PICK_UP_HERE.md">Updated handoff</a></p></section>\n'
(R/'docs/streamed-frame-section.html').write_text(body)
path = R/'docs/streamed-frame.md'
text = path.read_text()
block = '<!-- FRAME_RESULTS_START -->\n'+markdown+'<!-- FRAME_RESULTS_END -->'
if '<!-- FRAME_RESULTS_START -->' in text:
    text = re.sub(r'<!-- FRAME_RESULTS_START -->.*?<!-- FRAME_RESULTS_END -->', lambda _: block, text, flags=re.S)
else:
    first, rest = text.split('\n', 1)
    text = first+'\n\n'+block+'\n'+rest
path.write_text(text)
path = R/'docs/overview.html'
text = path.read_text()
text = re.sub(r'<section id="streamed-frame">.*?</section>\s*', '', text, flags=re.S)
text = text.replace('<main>', '<main>'+body, 1)
if 'href="#streamed-frame"' not in text.split('</nav>')[0]:
    text = text.replace('<nav>', '<nav><a href="#streamed-frame">Nine-pixel frame</a>', 1)
text = text.replace('>Latest simulation results</a>', '>Row-switching diagnostic</a>')
path.write_text(text)
print(headline+'. '+status)
