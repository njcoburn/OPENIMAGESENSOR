"""Publish the reviewed timeout and remaining electrical failure without qualifying incomplete cases."""
from pathlib import Path
from html import escape
import json
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    path=ROOT/'simulations/stack3-interrupted-review-20260930.json';review=json.loads(path.read_text());cases=review['cases']
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
    for c in cases:
        late=c['late_scan_retention'];axes[0].plot([r['column'] for r in late],[r['total_error_uV'] for r in late],label=c['corner'].upper())
        axes[1].plot([r['column'] for r in late],[-r['store_change_V']*1e6 for r in late],label=c['corner'].upper())
        if c['corner']=='ff':
            fine=[r for r in c['rows'] if r['scan']=='last'];axes[0].scatter([r['column'] for r in fine],[r['fine_error_against_coarse_capture_reference_uV'] for r in fine],s=10,color='black',label='FF available 50 ns samples')
    axes[0].axhline(-500,ls='--',color='red');axes[0].axhline(500,ls='--',color='red')
    axes[0].set(title='Late-scan error: complete coarse runs',xlabel='Column',ylabel='Signed total error (µV)')
    axes[1].set(title='STORE drop between first and late reads',xlabel='Column',ylabel='Voltage drop (µV)')
    for ax in axes:ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('64-column candidate: interrupted refinement review\n125 °C, inverse illumination; no complete paired qualification')
    fig.savefig(ROOT/'docs/assets/stack3-interrupted-review-20260930.png',dpi=150);plt.close(fig)
    rows=''.join(f'<tr><td>{c["corner"].upper()}</td><td>{c["coarse_total_error_uV"]:.3f}</td><td>{c["coarse_tracking_error_uV"]:.3f}</td><td>{c["available_refined_samples"]}/128</td><td>{c["max_available_saved_sample_difference_uV"]:.3f}</td><td>{"Above total-error limit" if not c["coarse_capture_readout_pass"] else "Coarse limits pass; full refinement incomplete"}</td></tr>' for c in cases)
    ff=next(c for c in cases if c['corner']=='ff');bad=ff['available_fine_total_error_failures']
    fragment=f'''<!-- BEGIN STACK3_INTERRUPTED_REVIEW -->
<div id="stack3-interrupted-review"><h3>Latest review: batch stopped; remaining fast-corner error</h3>
<p><strong>No simulation jobs remain active, and the sequence has not advanced.</strong> All three 100 ns runs and their 576 references completed. All three 50 ns runs hit the configured four-hour transient timeout near the end of the 3.98 ms schedule. The independent review validates the completed coarse evidence and available refinement prefixes; it does not count the missing samples as passes.</p>
<table><caption>125 °C inverse candidate results. Total/tracking errors and sampled differences in µV. Limits remain 500 µV total/tracking and 10 µV numerical agreement.</caption><thead><tr><th>MOS corner</th><th>Coarse total</th><th>Coarse tracking</th><th>Available fine samples</th><th>Worst available saved-node difference</th><th>Interpretation</th></tr></thead><tbody>{rows}</tbody></table>
<p>The fast-corner issue is visible before the timeout: {len(bad)} available fine samples exceed 500 µV against the same matched coarse capture references used by the normal paired audit. The largest available fine error is {max(abs(r['fine_error_against_coarse_capture_reference_uV']) for r in bad):.3f} µV. This supports investigating the remaining capture/storage error; raising the runtime limit alone does not establish a passing design.</p>
<p>The slow and typical coarse measurements are within their limits, but their complete refinement checks remain pending. The fine traces end at 3.862–3.932 ms; 373 of 384 sample instants are available. No missing values are extrapolated. Coarse fast-corner worst total error is 602.413 µV at late column 63, with only 3.476 µV maximum output tracking error. The settled-state change includes storage and supply/bias changes; its exact cause requires further diagnosis.</p>
<figure><a href="assets/stack3-interrupted-review-20260930.png"><img src="assets/stack3-interrupted-review-20260930.png" width="1800" height="690" style="max-width:100%;height:auto" alt="Late-scan fast-corner error crosses the negative 500 microvolt limit; available refined samples agree with the coarse trend. Storage droop is largest at the fast corner."></a></figure>
<p><strong>Next:</strong> diagnose and reduce the remaining fast-corner retention/capture error, then rerun the corrected full-bank candidate with a longer transient watchdog and a reviewed concurrency limit. Preserve completed references and interrupted traces; they are useful evidence but cannot turn incomplete pairs into passes. Later process/pattern stages remain blocked by this review.</p>
<p><a href="../simulations/stack3-interrupted-review-20260930.json">Independent evidence review</a> · <a href="../build/stack3-sequence-20260930-away/status.json">Original stopped-controller status</a>. The timeout belongs to the per-transient runner: outer job records correctly show exit code 1 rather than their own timeout flag. All original pinned sources and prior commits remain intact.</p></div>
<!-- END STACK3_INTERRUPTED_REVIEW -->'''
    (ROOT/'docs/stack3-interrupted-review-fragment.html').write_text(fragment+'\n')
    for name in ['64x64-first-silicon-section.html','verification-journal.html']:
        p=ROOT/'docs'/name;text=p.read_text()
        if '<!-- BEGIN STACK3_INTERRUPTED_REVIEW -->' in text:
            text,count=re.subn(r'<!-- BEGIN STACK3_INTERRUPTED_REVIEW -->.*?<!-- END STACK3_INTERRUPTED_REVIEW -->',lambda _:fragment,text,flags=re.S);assert count==1
        else:
            assert text.count('<!-- BEGIN STACK3_SEQUENCE -->')==1
            text=text.replace('<!-- BEGIN STACK3_SEQUENCE -->',fragment+'\n<!-- BEGIN STACK3_SEQUENCE -->',1)
        p.write_text(text)
    for name in ['update-overview-sections.py','update-verification-journal.py']:subprocess.run([sys.executable,str(ROOT/'scripts'/name)],check=True)
if __name__=='__main__':main()
