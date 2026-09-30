"""Publish the reviewed process failures and bounded storage-current diagnostics."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    retention=json.loads((ROOT/'simulations/compact-bank-process-retention-20260930.json').read_text())
    probes=json.loads((ROOT/'simulations/compact-bank-storage-leakage-20260930.json').read_text())
    lengths=json.loads((ROOT/'simulations/compact-bank-hold-length-screen-20260930.json').read_text())
    stacks=json.loads((ROOT/'simulations/compact-bank-hold-stack-screen-20260930.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained')
    for case in retention['cases']:
        rows=[r for r in case['rows'] if r['scan']=='last']
        axes[0,0].plot([r['column'] for r in rows],[r['total_error_uV'] for r in rows],label=case['mos_corner'].upper())
        axes[0,1].plot([r['column'] for r in case['drift']],[-r['store_change_uV'] for r in case['drift']],label=case['mos_corner'].upper())
    axes[0,0].axhline(500,color='red',ls='--');axes[0,0].axhline(-500,color='red',ls='--')
    axes[0,0].set(title='Late-scan total error',xlabel='Column',ylabel='Signed error (µV)')
    axes[0,1].set(title='STORE drop between first and late reads (1.28 ms)',xlabel='Column',ylabel='Voltage drop (µV)')
    dc=[next(c for c in probes['cases'] if c['mos_corner']==corner and c['column']==63 and c['scan']=='last') for corner in ['ss','typical','ff']]
    axes[1,0].bar(['SS','Typical','FF'],[c['device_current_leaving_store_pA']['hold_n'] for c in dc],color=['#287d8e','#666666','#c55233'])
    axes[1,0].set(title='Measured NMOS storage-terminal leakage, column 63',ylabel='Current leaving STORE (pA)')
    labels=['Original','L 0.75','L 1.0','L 1.5','2 in series','3 in series']
    for c in [0,63]:
        base=next(r for r in probes['cases'] if r['mos_corner']=='ff' and r['column']==c and r['scan']=='last')
        data=[base['clamp_supply_measured_pA']]+[r['net_store_leakage_pA'] for r in lengths['cases'] if r['column']==c]+[r['net_store_leakage_pA'] for r in stacks['cases'] if r['column']==c]
        axes[1,1].plot(labels,data,marker='o',label=f'Column {c}')
    axes[1,1].set(title='Model-only candidates: FF frozen states',ylabel='Net storage leakage (pA)')
    axes[1,1].tick_params(axis='x',rotation=20)
    for ax in axes.flat:ax.grid(alpha=.2)
    for ax in [axes[0,0],axes[0,1],axes[1,1]]:ax.legend()
    fig.suptitle('Process failures and storage diagnosis — 125 °C, inverse illumination\nCandidate DC improvements do not establish capture/readout accuracy',fontsize=14)
    fig.savefig(ROOT/'docs/assets/compact-bank-process-diagnosis-20260930.png',dpi=150);plt.close(fig)
    fragment='''<!-- BEGIN BANK_PROCESS_DIAGNOSIS -->
<div id="bank-process-diagnosis"><h3>Process failures reviewed — next correction work</h3>
<p><strong>Both process cases finished, but neither passes total accuracy.</strong> SS reaches 512.924 µV and FF 2000.323 µV against 500 µV. Output tracking, numerical/event refinement and contrast pass. All four transients and 384 references are audited; 1,740 evidence files verify. Runtime was 2.92 hours. Watcher exit 1 intentionally reports the measured failures; all four simulator exits are 0.</p>
<p>SS worst total error separates into −389.105 µV output tracking and −123.819 µV settled-state change. FF worst separates into −3.303 and −1997.019 µV respectively. Settled-state change includes stored voltages and local supply/bias changes. FF STORE drops by as much as 1.522 mV between scans; SS drops by at most 0.016 mV.</p>
<p><strong>Next step already investigated:</strong> five frozen-state DC probes identify the NMOS capture switch as the dominant fast-corner leakage path. At column 63 it drains 37.747 pA in FF, versus 4.252 pA typical and 0.613 pA SS. In FF, the PMOS injects about 0.234 pA, all eight MIM plates together leak about 0.036 pA, and modeled storage-follower gate current is zero. Direct clamp/probe current balance agrees within 0.00254 pA; saved DC voltages change by less than 0.000003 µV.</p>
<p>The initial three-terminal probe used subtraction of nearly equal voltages to infer clamp current and failed its pA-level balance check. Its artifacts remain retained. The second version adds all eight capacitor branches and a direct clamp-current probe; all five balance checks pass. Use these direct measurements for current attribution.</p>
<table><caption>Model-only candidates: net FF storage leakage in two frozen states, pA</caption><thead><tr><th>NMOS capture switch</th><th>Column 0</th><th>Column 63</th></tr></thead><tbody>
<tr><td>Original: one device, L = 0.5 µm</td><td>42.573</td><td>37.551</td></tr>
<tr><td>One device, L = 0.75 µm</td><td>35.836</td><td>29.957</td></tr>
<tr><td>One device, L = 1.0 µm</td><td>30.138</td><td>24.841</td></tr>
<tr><td>One device, L = 1.5 µm</td><td>23.685</td><td>19.237</td></tr>
<tr><td>Two series devices, each L = 0.5 µm</td><td>20.689</td><td>17.154</td></tr>
<tr><td>Three series devices, each L = 0.5 µm</td><td>13.535</td><td>11.030</td></tr>
</tbody></table>
<p>Six length cases and four series-stack cases completed with unchanged PDK corners and tolerances. These changes reduce DC leakage, but <strong>none is an accuracy-qualified correction</strong>. They have not been physically laid out or checked for capture resistance, charge injection, transient retention and process coverage. The original GDS is unchanged.</p>
<figure><a href="assets/compact-bank-process-diagnosis-20260930.png"><img src="assets/compact-bank-process-diagnosis-20260930.png" alt="Process errors, inter-scan storage drop, measured NMOS leakage and model-only length/stack comparisons" style="width:100%;height:auto"></a></figure>
<p><strong>Next engineering task:</strong> compare lower-leakage capture-switch candidates through complete small-bank capture/readout transients, and test a modest acquisition-timing extension for SS with nonoverlapping ADC reset. Only then rebuild a selected physical candidate and rerun the bank matrix. Additional mixed-corner coverage follows correction of these known failures. No new hours-long batch is running.</p>
<p><a href="../simulations/compact-bank-process-review-20260930.json">Completion review</a> · <a href="../simulations/compact-bank-process-retention-20260930.json">Error decomposition</a> · <a href="../simulations/compact-bank-storage-leakage-20260930.json">Direct current probes</a> · <a href="../simulations/compact-bank-hold-length-screen-20260930.json">Length screen</a> · <a href="../simulations/compact-bank-hold-stack-screen-20260930.json">Series-stack screen</a></p>
</div>
<!-- END BANK_PROCESS_DIAGNOSIS -->'''
    (ROOT/'docs/compact-bank-process-diagnosis-fragment.html').write_text(fragment+'\n')
    pattern=r'<!-- BEGIN BANK_PROCESS_DIAGNOSIS -->.*?<!-- END BANK_PROCESS_DIAGNOSIS -->'
    for filename in ['docs/64x64-first-silicon-section.html','docs/verification-journal.html']:
        p=ROOT/filename;s=p.read_text()
        if re.search(pattern,s,re.S):s,count=re.subn(pattern,lambda _:fragment,s,flags=re.S);assert count==1
        else:s=s.replace('<!-- BEGIN BANK_PROCESS -->',fragment+'\n<!-- BEGIN BANK_PROCESS -->',1)
        s=s.replace('the new process-variation batch below is active.','the process batch below has completed with total-error failures.')
        p.write_text(s)
    spec=importlib.util.spec_from_file_location('overview',ROOT/'scripts/update-overview-sections.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.main()
    subprocess.run([sys.executable,str(ROOT/'scripts/update-verification-journal.py')],check=True)

if __name__=='__main__':main()
