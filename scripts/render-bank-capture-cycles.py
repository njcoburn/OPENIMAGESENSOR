"""Publish the reviewed small-bank candidate screen in the overview and journal."""
from pathlib import Path
import json
import re
import subprocess
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def main():
    report=json.loads((ROOT/'simulations/compact-bank-capture-cycles-20260930.json').read_text())
    review=json.loads((ROOT/'simulations/compact-bank-capture-cycles-review-20260930.json').read_text())
    assert len(report['cases'])==len(review['cases'])==10
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    for corner,color in [('typical','#547c39'),('ss','#307caa'),('ff','#bf5537')]:
        cases=[c for c in report['cases'] if c['corner']==corner and c['acquisition_us']==12]
        axes[0].plot([c['series_devices'] for c in cases],[c['max_total_error_uV'] for c in cases],marker='o',label=corner.upper(),color=color)
    axes[0].axhline(500,color='black',ls='--',label='500 µV limit')
    axes[0].set(title='Full capture/readout cycle: two-column model',xlabel='Series NMOS devices in capture switch',ylabel='Worst absolute total error (µV)',xticks=[1,2,3])
    axes[0].legend();axes[0].grid(alpha=.2)
    timing=[c for c in report['cases'] if c['series_devices']==1 and c['corner']=='ss']
    for key,label in [('max_total_error_uV','Total error'),('max_tracking_error_uV','Output tracking')]:
        axes[1].plot([c['acquisition_us'] for c in timing],[c[key] for c in timing],marker='o',label=label)
    axes[1].set(title='SS acquisition extension: original switch',xlabel='Acquisition (µs)',ylabel='Worst absolute error (µV)',xticks=[12,12.5])
    axes[1].legend();axes[1].grid(alpha=.2)
    fig.suptitle('125 °C, inverse illumination — model-only candidate screen\nBoth timesteps independently referenced; physical layout and 64-column correction still pending')
    fig.savefig(ROOT/'docs/assets/compact-bank-capture-cycles-20260930.png',dpi=150);plt.close(fig)
    rows=''.join(f'<tr><td>{c["series_devices"]}</td><td>{c["corner"].upper()}</td><td>{c["acquisition_us"]:g}</td><td>{c["max_total_error_uV"]:.3f}</td><td>{c["max_tracking_error_uV"]:.3f}</td><td>{"PASS" if c["selected_screen_pass"] else "FAIL"}</td></tr>' for c in report['cases'])
    fragment='''<!-- BEGIN BANK_CAPTURE_CYCLES -->
<div id="bank-capture-cycles"><h3>Capture-switch candidates — complete small-bank cycles reviewed</h3>
<p><strong>The three-device series NMOS candidate passes the selected two-column screen at typical, SS and FF.</strong> At FF, total error falls from 1240.756 µV with the original switch to 596.505 µV with two series devices and 410.653 µV with three. The limit remains 500 µV. This identifies a candidate to implement physically; it does not fix or qualify the existing 64-column GDS.</p>
<p>Twenty fresh transients and 120 matched-state references cover the complete capture and two readout scans at 125 °C, inverse illumination, 100/50 ns timesteps. Both timesteps have their own capture/output references. All sample, event, error-refinement and contrast checks pass, including the added stack nodes. Worst saved-sample difference is 1.346 µV; worst event difference is 1.590 µV, below 10 µV. Fresh original-switch SS/FF controls reproduce the retained waveforms within 0.001 µV at HOLD.</p>
<table><caption>Two-column diagnostic results, worst across both timesteps; errors in µV</caption><thead><tr><th>Series devices</th><th>MOS</th><th>Acquisition µs</th><th>Total error</th><th>Tracking</th><th>Screen</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<p><strong>Timing result:</strong> extending acquisition from 12 to 12.5 µs reduces SS tracking error from 281.789 to 206.737 µV and total error from 187.313 to 137.243 µV on the original small bank. Acquisition finishes falling at 14.51 µs within the 20 µs slot; ADC reset begins rising at 15 µs, leaving 0.49 µs separation. This is a fresh simulation, not a later sample of the old waveform. The full-bank SS failure still requires verification, as does combining the extension with the series-switch candidate.</p>
<figure><a href="assets/compact-bank-capture-cycles-20260930.png"><img src="assets/compact-bank-capture-cycles-20260930.png" width="1800" height="720" style="max-width:100%;height:auto" alt="Three series NMOS devices reduce fast-corner error below 500 microvolts in the two-column model; a half-microsecond acquisition extension improves slow-corner settling."></a></figure>
<p><strong>Next:</strong> implement the three-device capture switch in a separate physical column revision, check DRC/LVS and extracted small-bank behavior, then verify the complete 64-column schedule. First check the combined candidate and timing change. The model-only stack retains each original device's geometry parameters and omits new routing parasitics; physical extraction may change the result. Mixed MOS, diode/MIM, supply/wire and full-chip checks remain open. No new hours-long batch is active.</p>
<p><a href="../simulations/compact-bank-capture-cycles-20260930.json">Screen evidence</a> · <a href="../simulations/compact-bank-capture-cycles-review-20260930.json">Independent raw/deck review</a> · <a href="../verification/compact-bank-capture-candidates.json">Rerun profile</a></p>
<p>Reproduce this screen with a fresh output directory, then audit it:</p>
<pre>bash scripts/run-tools.sh python3 scripts/screen-bank-capture-cycles.py --out build/candidate-cycles-NEW
bash scripts/run-tools.sh python3 scripts/review-bank-capture-cycles.py --source build/candidate-cycles-NEW --out build/candidate-review-NEW</pre>
<p>The screen is tied to the retained two-column physical parent. After a pixel/layout change, rebuild and validate the parent, version these scripts for the new source, and rerun the physical baseline and full-bank matrix; this command is not yet a general pixel-rebuild controller.</p></div>
<!-- END BANK_CAPTURE_CYCLES -->'''
    (ROOT/'docs/compact-bank-capture-cycles-fragment.html').write_text(fragment+'\n')
    for filename in ['64x64-first-silicon-section.html','verification-journal.html']:
        p=ROOT/'docs'/filename;text=p.read_text()
        if '<!-- BEGIN BANK_CAPTURE_CYCLES -->' in text:
            text,count=re.subn(r'<!-- BEGIN BANK_CAPTURE_CYCLES -->.*?<!-- END BANK_CAPTURE_CYCLES -->',lambda _:fragment,text,flags=re.S);assert count==1
        else:
            assert text.count('<!-- BEGIN BANK_PROCESS_DIAGNOSIS -->')==1
            text=text.replace('<!-- BEGIN BANK_PROCESS_DIAGNOSIS -->',fragment+'\n<!-- BEGIN BANK_PROCESS_DIAGNOSIS -->',1)
        # Preserve diagnostic measurements, label their superseded next-step text.
        text=text.replace('<strong>Next engineering task:</strong> compare lower-leakage','<strong>Earlier plan (completed in the candidate screen above):</strong> compare lower-leakage')
        p.write_text(text)
    for filename in ['update-overview-sections.py','update-verification-journal.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/filename)],check=True)

if __name__=='__main__':main()
