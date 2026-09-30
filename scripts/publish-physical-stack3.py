"""Update the repository overview/journal with the verified physical candidate."""
from pathlib import Path
import json
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    port=json.loads((ROOT/'simulations/compact-bank-physical-cycles-20260930.json').read_text())
    far=json.loads((ROOT/'simulations/compact-bank-physical-far-cycles-20260930.json').read_text())
    for name in ['compact-bank-combined-review','compact-bank-physical-cycles-review','compact-bank-physical-far-review']:
        review=json.loads((ROOT/f'simulations/{name}-20260930.json').read_text());assert all(c['selected_screen_pass'] for c in review['cases'])
    rows=''.join(f'<tr><td>{a["corner"].upper()}</td><td>{a["max_total_error_uV"]:.3f}</td><td>{b["max_total_error_uV"]:.3f}</td><td>{max(a["max_tracking_error_uV"],b["max_tracking_error_uV"]):.3f}</td><td>PASS</td></tr>' for a,b in zip(port['cases'],far['cases']))
    fragment='''<!-- BEGIN PHYSICAL_STACK3 -->
<div id="physical-stack3"><h3>Physical three-device capture switch — small-bank verification complete</h3>
<p><strong>The candidate is now implemented in a separate physical column and two-column bank.</strong> Three W = 1 µm, L = 0.5 µm NMOS capture devices in series, combined with 12.5 µs acquisition, pass the selected extracted-circuit tests at typical, SS and FF. The original 64-column GDS remains the existing checkpoint; its known process failures are not relabeled by these results.</p>
<p>Both the new column and small bank pass Magic/KLayout main DRC and direct/resistor-collapsed LVS. Two neighboring columns pass the 40 µm abutment check. The column outline is unchanged, and M4, M5, capacitor-marker and via4 geometry is exactly unchanged. The column contains nine MOS devices; the bank contains 26 MOS devices, 16 capacitor plates and two photodiodes. Density, antenna, CUP and full-chip checks remain outside this evidence.</p>
<table><caption>Extracted two-column candidate: 125 °C inverse illumination, 12.5 µs acquisition. Worst errors across 100/50 ns, in µV; total/tracking limit 500 µV.</caption><thead><tr><th>MOS corner</th><th>Port-placement total</th><th>Far-placement total</th><th>Worst tracking</th><th>Selected checks</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<p>Six combined model-only transients and 36 references passed before physical qualification. The extracted candidate adds 12 transients and 72 references across two wiring-capacitance placements. All 18 transients and 108 references are reviewed. Each timestep has fresh capture and output references. Numerical, physical-capacitor-event and contrast checks pass. Moving all four approximated shunt groups together changes sampled HOLD/STORE by at most 0.044 µV, below 10 µV. All extracted resistors and collapsed capacitance totals are retained.</p>
<p>The first physical attempt extended routes into a capacitor region and failed two Magic rules; it is retained as a failed attempt. The corrected placement puts the two added NMOS devices at y = 144 and 156 µm and preserves the original capacitor routes. The isolated-column extraction includes small negative shunt corrections on one new private net; these are consolidated with its positive total, with raw extraction retained. The assembled-bank extraction does not need that private-net consolidation.</p>
<details><summary>View the new two-column physical layout detail</summary><figure><a href="assets/compact-bank-physical-stack3-detail-20260930.png"><img src="assets/compact-bank-physical-stack3-detail-20260930.png" width="795" height="1525" style="max-width:100%;height:auto" alt="Physical two-column candidate showing two pixel photodiodes at the bottom, shared buses, analog devices and the two added NMOS devices at the top of each column."></a><figcaption>Exact new GDS detail: two pixels at the bottom; shared references at left; added NMOS pair at the top of each repeated column. Capacitor plates continue above this crop. This is a separate candidate, not the displayed 64-column checkpoint.</figcaption></figure></details>
<p><strong>Next:</strong> build the candidate as a separate 64-column bank with the established ground grid, verify DRC/LVS and topology, then run matched typical/SS/FF corner tests with 12.5 µs acquisition. Full-bank testing is the next potentially hours-long stage; no such batch has been started here. Other temperatures, illumination patterns, mixed corners, supply/wire and full-chip coverage remain open.</p>
<p><a href="../simulations/compact-bank-physical-stack3-20260930.json">Physical audit</a> · <a href="../simulations/compact-bank-physical-cycles-review-20260930.json">Port raw-data review</a> · <a href="../simulations/compact-bank-physical-far-review-20260930.json">Far raw-data review</a> · <a href="../simulations/compact-bank-physical-stack3-placement-20260930.json">Placement comparison</a> · <a href="../verification/compact-bank-physical-stack3.json">Reproduction profile</a></p>
<p>New scripts and evidence are versioned separately from earlier hash-pinned runners. The reproduction profile records the commands and fixed physical source for this candidate; a changed pixel requires rebuilding and requalifying that source before rerunning electrical coverage.</p>
</div>
<!-- END PHYSICAL_STACK3 -->'''
    (ROOT/'docs/compact-bank-physical-stack3-fragment.html').write_text(fragment+'\n')
    for name in ['64x64-first-silicon-section.html','verification-journal.html']:
        p=ROOT/'docs'/name;text=p.read_text()
        if '<!-- BEGIN PHYSICAL_STACK3 -->' in text:
            text,count=re.subn(r'<!-- BEGIN PHYSICAL_STACK3 -->.*?<!-- END PHYSICAL_STACK3 -->',lambda _:fragment,text,flags=re.S);assert count==1
        else:
            assert text.count('<!-- BEGIN BANK_CAPTURE_CYCLES -->')==1
            text=text.replace('<!-- BEGIN BANK_CAPTURE_CYCLES -->',fragment+'\n<!-- BEGIN BANK_CAPTURE_CYCLES -->',1)
        text=text.replace('<h3>Capture-switch candidates — complete small-bank cycles reviewed</h3>','<h3>Earlier model-only capture-switch candidate screen</h3>')
        text=text.replace('<strong>Next:</strong> implement the three-device capture switch','<strong>Earlier plan (physical small-bank work now completed above):</strong> implement the three-device capture switch')
        p.write_text(text)
    for name in ['update-overview-sections.py','update-verification-journal.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/name)],check=True)
if __name__=='__main__':main()
