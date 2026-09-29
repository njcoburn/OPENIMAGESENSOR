"""Audit and render compact-bank solver/phase experiments without promoting partial runs."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,action='append',required=True)
    p.add_argument('--layout',type=Path,action='append',default=[])
    p.add_argument('--compare',type=Path,nargs=2,action='append',default=[])
    a=p.parse_args();runs=[];evidence=set();comparisons=[];physical=[]
    for d in a.layout:
        meta=json.loads((d/'verification.json').read_text())
        assert meta['magic_drc_errors']==meta['klayout_main_drc_errors']==0
        assert meta['direct_and_resistor_collapsed_lvs']
        assert meta['gds_sha256']==sha(d/'bank.gds')
        assert len(ET.parse(d/'main-drc.lyrdb').getroot().find('items'))==0
        for name in ['direct','collapsed']:assert 'Circuits match uniquely' in (d/f'{name}-lvs.log').read_text()
        for name,digest in meta['hashes'].items():assert sha(d/name)==digest
        physical.append(dict(directory=str(d),**{k:meta[k] for k in ['columns','bbox_um','mos','mim','diodes','gds_sha256']}))
        evidence.update(f for f in d.iterdir() if f.is_file())
    def read(d):
        r=json.loads((d/'result.json').read_text())
        assert sha(d/'tile.spice')==r['model_sha256']
        assert sha(d/'transient/test.spice')==r['transient']['deck_sha256']
        evidence.update(f for f in d.rglob('*') if f.is_file())
        return r
    for d in a.run:
        r=read(d)
        runs.append(dict(directory=str(d),columns=r['columns'],phase=r.get('phase','full'),
            solver=r.get('solver','sparse'),method=r.get('method','trap'),temperature_C=r['temperature_C'],
            driver_form=r.get('driver_form','current'),
            step_ns=r['step_ns'],lights_pA=r['lights_pA'],model=r['model'],
            layout_gds_sha256=r['layout_gds_sha256'],model_sha256=r['model_sha256'],
            transient=r['transient'],completed=r['completed'],references_requested=r['references_requested'],
            capture_references_completed=len(r.get('capture_references',[])),
            output_references_completed=sum('output_reference' in s for s in r.get('samples',[])),
            max_total_capture_readout_error_V=r.get('max_total_capture_readout_error_V'),
            max_output_tracking_error_V=r.get('max_output_tracking_error_V'),
            capture_readout_pass=r.get('capture_readout_pass'),tracking_pass=r.get('tracking_pass'),
            reference_failure=r.get('reference_failure')))
        last=r['transient'].get('last_complete_trace_time_s')
        runs[-1]['scheduled_readout_sample_times_reached']=sum(last is not None and last>=s['start_s']+11.999e-6 for s in r['readout_slots'])
        runs[-1]['scheduled_readout_samples']=2*r['columns']
    for left,right in a.compare:
        old,new=read(left),read(right)
        assert old['completed'] and new['completed']
        for k in ['columns','lights_pA','temperature_C','layout_gds_sha256','model_sha256']:
            assert old[k]==new[k],k
        assert len(old['samples'])==len(new['samples'])==old['columns']*2
        differences={}
        for x,y in zip(old['samples'],new['samples']):
            assert (x['slot'],x['column'],x['time_s'])==(y['slot'],y['column'],y['time_s'])
            for n in x['values']:
                differences[n]=max(differences.get(n,0),abs(x['values'][n]-y['values'][n]))
        comparisons.append(dict(left=str(left),right=str(right),
            maximum_saved_terminal_difference_V=max(differences.values()),
            maximum_adc_hold_difference_V=differences['HOLD'],
            saved_sample_comparison_pass=max(differences.values())<10e-6,
            scope='Matched saved readout points; not continuous-waveform equivalence.',
            differences_by_node_V=differences))
    report=dict(scope=__doc__,runs=runs,comparisons=comparisons,physical=physical,
        full_bank_accuracy_qualified=False,full_chip_implemented=False,
        runtime_scope='Observed wall times with some concurrent jobs; not controlled speed benchmarks.',
        evidence_hashes={str(f):sha(f) for f in sorted(evidence)})
    (ROOT/'simulations/compact-bank-solver-20260927.json').write_text(json.dumps(report,indent=2)+'\n')
    rows=''
    for r in runs:
        t=r['transient'];last=t.get('last_complete_trace_time_s')
        progress='DC point' if r['phase']=='op' and t['completed'] else ('—' if last is None else f'{last*1e3:.6f} ms')
        outcome='Complete' if r['completed'] else 'Incomplete'
        if t['timed_out']:outcome='Watchdog timeout'
        elif t['errors']:outcome='Solver abort'
        accuracy=r['max_total_capture_readout_error_V']
        error='Not checked' if accuracy is None else f'{accuracy*1e6:.3f} µV; '+('pass' if r['capture_readout_pass'] and r['tracking_pass'] else 'FAIL')
        rows+=f'<tr><th>{r["columns"]} / {r["phase"]}</th><td>{r["solver"].upper()} / {r["method"]} / {r["driver_form"]} drive</td><td>{r["temperature_C"]:g} °C / {r["step_ns"]:g} ns</td><td>{t["seconds"]:.1f} s</td><td>{progress}</td><td>{outcome}</td><td>{error}</td></tr>'
    differences=''.join(f'<li><code>{escape(Path(c["left"]).name)}</code> versus <code>{escape(Path(c["right"]).name)}</code>: maximum saved-terminal difference {c["maximum_saved_terminal_difference_V"]*1e6:.6f} µV; ADC hold difference {c["maximum_adc_hold_difference_V"]*1e6:.6f} µV. {"Passes" if c["saved_sample_comparison_pass"] else "Fails"} the 10 µV comparison screen.</li>' for c in comparisons)
    layouts=''.join(f'<li>{x["columns"]}-column bank: main Magic/KLayout DRC and both LVS paths pass; {x["mos"]} MOS, {x["mim"]} MIM plates, {x["diodes"]} diodes.</li>' for x in physical)
    large=[]
    for r in runs:
        if r['columns']>=16 and r['phase']=='full':
            large.append(f'<li>{r["columns"]} columns, {r["transient"]["seconds"]:.1f} s: '
                         f'{r["scheduled_readout_sample_times_reached"]} of {r["scheduled_readout_samples"]} scheduled sample instants reached. '
                         'Independent readout accuracy references were not requested.</li>')
    html=f'''<section id="compact-bank-solver"><h2>27 September: compact-bank simulation progress</h2>
<p><strong>Full-bank initialization and reset now complete with KLU.</strong> The previous SPARSE 64-column runs timed out with zero samples, including an audited resistor reduction. The KLU reset control reaches 250 µs with all physical devices, resistors and capacitors retained. Reset completion is not a capture/readout accuracy pass.</p>
<p>The new runner separates operating point, reset, capture and full readout. It records when fully written trace data cross each phase boundary; buffered output makes these observation times approximate. Default SPARSE/trapezoidal settings remain available. Solver and integration-method comparisons keep the circuit, extracted parasitics and tolerances unchanged.</p>
<p>The optional voltage-drive control rewrites each finite-resistance control driver as a behavioral voltage source followed by the same resistor. It changes the equation representation, not drive strength or target voltage; its numerical agreement still needs checking. Device and extracted-parasitic records are untouched.</p>
<p>The tested voltage-drive formulation aborts during initialization and is retained as a failed diagnostic. Gear passes the nominal eight-column accuracy comparison but shows no runtime benefit here. Continue with the original current-form drivers and KLU/trapezoidal integration.</p>
<ul>{layouts}</ul>
<div style="overflow-x:auto"><table><thead><tr><th>Columns / phase</th><th>Solver / method</th><th>Temperature / step</th><th>Runtime</th><th>Last saved time</th><th>Completion</th><th>Capture/readout accuracy</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>All new cases use alternating 0/240 pA illumination. Accuracy entries require completed independent capture and output references; the limit is 500 µV. Timed-out or transient-only runs do not qualify accuracy. Some jobs ran concurrently, so runtime differences are observations rather than controlled benchmarks.</p>
<p>The eight-column nominal and hot reference controls reach 195.412 and 430.243 µV worst capture/readout error, respectively. Their matched 200→100 ns saved-terminal changes are 0.170 and 0.401 µV. These cover one alternating pattern at the typical process corner; other patterns, shunt placements and process/wire corners remain open. Thirteen local reducer, schedule and partial-trace tests pass.</p>
<h3>Full-bank runtime is now the immediate bottleneck</h3><ul>{''.join(large)}</ul>
<p>Reuse the completed 16-column transient with a provenance-checked reference pass before paying for another scan. Use the 64-column phase timings to budget a complete run; the 900-second attempt is evidence of partial progress, not a completed bank. All retained attempts are finished; Docker/VNC remains available.</p>
<h3>Numerical comparisons</h3><ul>{differences}</ul>
<p>The earlier <a href="compact-bank-initialization.md">resistor-only reduction audit</a> removes 1824 internal nodes while retaining every non-resistor record, but does not resolve the SPARSE full-bank timeout. Its hot two-column saved-sample comparison differs by at most 0.058281 µV. Four/eight-column layouts pass both main DRC and both LVS paths; four columns completed the original transient.</p>
<p><strong>The 64×64 chip is not yet implemented or tapeout-qualified.</strong> Full-bank nominal/hot accuracy, refinement, shunt placements and supply drops remain required, followed by loaded repeated rows, real drivers, full-chip geometry and manufacturing signoff.</p>
<p><a href="../simulations/compact-bank-solver-20260927.json">Results, phase observations and evidence hashes</a> · <a href="../NEXT_STEPS.md">Next experiments</a>. Generated traces remain local in <code>build/</code>; hashes are not an external backup.</p></section>'''
    (ROOT/'docs/compact-bank-solver-section.html').write_text(html+'\n')
    print(json.dumps(dict(runs=len(runs),comparisons=len(comparisons)),indent=2))


if __name__=='__main__':main()
