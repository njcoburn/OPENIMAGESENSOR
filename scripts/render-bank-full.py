"""Render the audited nominal complete-bank screen and its explicit limits."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def plot(r,output):
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for scan,color in [('first','#236a91'),('last','#b75423')]:
        rows=[s for s in r['rows'] if s['scan']==scan]
        axes[0,0].plot([s['column'] for s in rows],[s['total_error_uV'] for s in rows],'.-',ms=3,label=scan,color=color)
        axes[0,1].plot([s['column'] for s in rows],[s['tracking_error_uV'] for s in rows],'.-',ms=3,label=scan,color=color)
        fine=[s for s in r['refinement'] if s['scan']==scan]
        axes[1,0].plot([s['column'] for s in fine],[s['max_uV'] for s in fine],'.-',ms=3,label=scan,color=color)
    for ax in axes[0]:
        ax.axhline(500,color='#a12424',ls='--');ax.axhline(-500,color='#a12424',ls='--')
        ax.set(ylabel='Signed error (µV)');ax.legend()
    axes[0,0].set_title('Capture/readout: 64 capture references')
    axes[0,1].set_title('Output tracking: 128 output references')
    axes[1,0].axhline(10,color='#a12424',ls='--')
    axes[1,0].set(title='100 → 50 ns: all saved sample terminals',ylabel='Largest absolute change (µV)')
    events=r['runs'][0]['events']
    for e,color in [(next(x for x in events if x['event']=='before_row_off'),'#236a91'),(next(x for x in events if x['event']=='after_row_off'),'#b75423')]:
        axes[1,1].plot([x['column'] for x in e['columns']],[x['ground_V']*1000 for x in e['columns']],label=e['event'].replace('_',' '),color=color)
    axes[1,1].set(title='Physical MIM ground, average of 8 plates/column',ylabel='Ground relative to external GND (mV)')
    axes[1,1].legend()
    for ax in axes.flat:ax.set_xlabel('Physical column');ax.grid(alpha=.2)
    fig.suptitle(f'Complete 64-column screen · 12 µs acquisition in 20 µs slots\n{r["temperature_C"]} °C · {r["pattern"]} pattern · one capture, two scans')
    fig.savefig(output,dpi=160);plt.close(fig)


def main():
    r=json.loads((ROOT/'simulations/compact-bank-64-full.json').read_text())
    assert r['full_bank_readout_completed'] and not r['full_bank_accuracy_qualified'] and not r['full_chip_qualified']
    plot(r,ROOT/'docs/assets/compact-bank-64-full.png')
    events=r['runs'][0]['events']
    worst=max(r['rows'],key=lambda x:abs(x['total_error_uV']));fine=max(r['refinement'],key=lambda x:x['max_uV'])
    outcome='passes' if r['selected_screen_pass'] else 'fails'
    table=''.join(f'<tr><td>{x["scan"]}</td><td>{x["column"]}</td><td>{x["hold_V"]:.9f}</td><td>{x["total_error_uV"]:.3f}</td><td>{x["tracking_error_uV"]:.3f}</td><td>{x["hold_refinement_uV"]:.6f}</td></tr>' for x in r['rows'])
    checks=''.join(f'<tr><td>{name.replace("_"," ")}</td><td>{"PASS" if passed else "FAIL"}</td></tr>' for name,passed in r['checks'].items())
    before=next(x for x in events if x['event']=='before_row_off');after=next(x for x in events if x['event']=='after_row_off')
    shifts=[dict(column=a['column'],store_uV=(b['store_V']-a['store_V'])*1e6,ground_uV=(b['ground_V']-a['ground_V'])*1e6,differential_uV=(b['differential_V']-a['differential_V'])*1e6) for a,b in zip(before['columns'],after['columns'])]
    shift=max(shifts,key=lambda x:abs(x['store_uV']))
    maxground=max(e['max_mim_ground_V'] for e in events)*1000
    html=f'''<section id="compact-bank-64-full"><h2>Complete 64-column readout: nominal accuracy and refinement</h2>
<p><strong>The distributed-return bank {outcome} this nominal complete-bank screen.</strong> Both 3.98 ms transients finish all 128 scheduled reads. The 100 ns run has <strong>64 capture and 128 output references</strong>, independently checked. Worst total capture/readout error is <strong>{r['max_total_error_uV']:.3f} µV</strong> and output tracking is <strong>{r['max_tracking_error_uV']:.3f} µV</strong>, each against 500 µV. Worst total error occurs in the {worst['scan']} scan at column {worst['column']}.</p>
<p>The matching 50 ns transient changes saved sample terminals by at most <strong>{r['max_refinement_uV']:.3f} µV</strong> against 10 µV; its worst comparison is {fine['node']} in the {fine['scan']} scan, column {fine['column']}. It has no separate DC references. The four physical MIM event comparisons differ by at most {r['event_refinement_worst']['difference_uV']:.3f} µV.</p>
<figure><img src="assets/compact-bank-64-full.png" alt="Full-bank first and late scan errors, timestep differences and physical storage-capacitor ground profiles"><figcaption>27 °C, typical process, nominal supply/wire, alternating 0/240 pA. Dashed lines show the accuracy and refinement limits. The ground profile is a physical diagnostic, not an ADC error metric.</figcaption></figure>
<table><thead><tr><th>Selected check</th><th>Result</th></tr></thead><tbody>{checks}</tbody></table>
<h3>Physical ground measurements and timing</h3>
<p>The maximum saved physical MIM ground rise across the four capture/row/reset event probes is {maxground:.3f} mV. The largest row-off STORE shift is {shift['store_uV']:.3f} µV at column {shift['column']}; its average ground and across-capacitor shifts are {shift['ground_uV']:.3f}/{shift['differential_uV']:.3f} µV. These event shifts are separate from the matched readout errors above.</p>
<p>The 12 µs acquisition ends at +14 µs; the sample is at +13.999 µs, reset begins at +15 µs and selection ends at +16 µs. The 20 µs slot is unchanged. A separately versioned runner preserves the original evidence dependencies. Four regression tests verify default deck equality at 2/16/64 columns, exact reproduction of the archived selected 12 µs control, the intended full-deck change and disjoint sample/control windows.</p>
<p>The 100/50 ns transients took {r['runs'][0]['transient_seconds']/60:.1f}/{r['runs'][1]['transient_seconds']/60:.1f} minutes; these figures exclude reference-solving time and depend on concurrent work. Strict simulator tolerances, physical devices and parasitic loads are retained. Binary waveforms, all frozen-state reference decks and errors are independently rechecked. Six auditor regression/adversarial tests pass.</p>
<details><summary>All 128 nominal readout results</summary><div style="overflow-x:auto"><table><thead><tr><th>Scan</th><th>Column</th><th>HOLD, V</th><th>Total error, µV</th><th>Tracking, µV</th><th>HOLD refinement, µV</th></tr></thead><tbody>{table}</tbody></table></div></details>
<p class="note"><strong>Scope remains limited:</strong> remaining temperature/illumination combinations, process/wire/supply corners, shunt placements and local supply/bias qualification remain open. This uses behavioral drivers, external bias resistors and an ADC fixture, one capture and two scans. Real decoding/drivers, repeated rows, the exact 64×64 layout and provider optical/manufacturing checks are still required. Complete readout is demonstrated; full bank/corner and tapeout qualification flags remain false.</p>
<p><a href="../simulations/compact-bank-64-full.json">Independent audit and evidence hashes</a> · <a href="compact-bank-64-full.md">Reproduction and next steps</a> · <a href="#compact-bank-64-read-probes">Earlier selected readout controls</a> · <a href="#wafer-space-run3">Run dates, costs and die fit</a></p></section>'''
    hotfile=ROOT/'simulations/compact-bank-64-full-hot.json'
    if hotfile.exists():
        hot=json.loads(hotfile.read_text())
        assert hot['full_bank_readout_completed'] and hot['temperature_C']==125 and hot['pattern']=='inverse'
        assert not hot['full_bank_accuracy_qualified'] and not hot['full_chip_qualified']
        plot(hot,ROOT/'docs/assets/compact-bank-64-full-hot.png')
        hotoutcome='passes' if hot['selected_screen_pass'] else 'fails'
        hotworst=max(hot['rows'],key=lambda x:abs(x['total_error_uV']))
        hotrows=''.join(f'<tr><td>{x["scan"]}</td><td>{x["column"]}</td><td>{x["total_error_uV"]:.3f}</td><td>{x["tracking_error_uV"]:.3f}</td><td>{x["hold_refinement_uV"]:.6f}</td></tr>' for x in hot['rows'])
        hothtml=f'''<h3>Full-width hot inverse-pattern control</h3>
<p><strong>The 125 °C inverse-pattern pair {hotoutcome} its selected screen.</strong> Both full scans complete with another 192 matched references. Worst total error is {hot['max_total_error_uV']:.3f} µV ({hotworst['scan']} scan, column {hotworst['column']}); output tracking is {hot['max_tracking_error_uV']:.3f} µV. Largest 100/50 ns saved-terminal and physical-event differences are {hot['max_refinement_uV']:.3f}/{hot['event_refinement_worst']['difference_uV']:.3f} µV. Accuracy limits stay 500 µV and refinement limits stay 10 µV.</p>
<figure><img src="assets/compact-bank-64-full-hot.png" alt="Full-width hot inverse-pattern accuracy, numerical refinement and physical capacitor ground profiles"><figcaption>The two temperature/pattern pairs cover four complete transients and 384 references. They do not establish every temperature/pattern combination or process/wire/supply corner.</figcaption></figure>
<p>Hot 100/50 ns transients took {hot['runs'][0]['transient_seconds']/60:.1f}/{hot['runs'][1]['transient_seconds']/60:.1f} minutes, excluding references. This is the prior 16-column screen's highest-error condition, now tested at full width; it is not a substitute for the remaining pattern and corner matrix.</p>
<details><summary>All 128 hot inverse-pattern readouts</summary><table><thead><tr><th>Scan</th><th>Column</th><th>Total error, µV</th><th>Tracking, µV</th><th>HOLD refinement, µV</th></tr></thead><tbody>{hotrows}</tbody></table></details>
<p><a href="../simulations/compact-bank-64-full-hot.json">Hot inverse audit and evidence hashes</a></p>'''
        html=html.replace('</section>',hothtml+'</section>')
    (ROOT/'docs/compact-bank-64-full-section.html').write_text(html+'\n')
    print(json.dumps(dict(outcome=outcome,worst=worst,ground_shift=shift),indent=2))


if __name__=='__main__':main()
