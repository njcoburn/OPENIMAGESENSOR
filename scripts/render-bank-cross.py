"""Render the alternating/inverse temperature matrix from independently audited reports."""
import argparse
import html
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def read_reports(plan):
    cases=[dict(name='nominal',temperature=27,pattern='alternating',report='compact-bank-64-full.json'),
           dict(name='hot-inverse',temperature=125,pattern='inverse',report='compact-bank-64-full-hot.json')]+plan['cases']
    assert {(c['temperature'],c['pattern']) for c in cases}=={(t,p) for t in [27,125] for p in ['alternating','inverse']}
    assert len(cases)==4
    reports={}
    for case in cases:
        path=ROOT/'simulations'/case['report']
        if not path.exists():continue
        r=json.loads(path.read_text())
        assert (r['temperature_C'],r['pattern'])==(case['temperature'],case['pattern'])
        assert r['full_bank_readout_completed'] and not r['full_bank_accuracy_qualified'] and not r['full_chip_qualified']
        assert r['selected_screen_pass']==all(r['checks'].values())
        assert [x['samples'] for x in r['runs']]==[128,128] and [x['references'] for x in r['runs']]==[192,0]
        assert r['layout']=='build/compact-bank-c64-ground-grid-20260927' and r['acquisition_us']==12
        reports[case['name']]=r
    return cases,reports

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    plan=json.loads(a.plan.read_text());cases,reports=read_reports(plan)
    rows=[]
    for case in sorted(cases,key=lambda c:(c['temperature'],c['pattern'])):
        r=reports.get(case['name'])
        values=('<td>Pending</td><td>—</td><td>—</td><td>—</td>' if r is None else
                f'<td>{"PASS" if r["selected_screen_pass"] else "FAIL"}</td><td>{r["max_total_error_uV"]:.3f}</td><td>{r["max_tracking_error_uV"]:.3f}</td><td>{r["max_refinement_uV"]:.3f}</td>')
        link=f'<a href="../simulations/{html.escape(case["report"])}">{case["pattern"]}</a>' if r else case['pattern']
        rows.append(f'<tr><td>{case["temperature"]} °C</td><td>{link}</td>{values}</tr>')
    completed=sum(case['name'] in reports for case in plan['cases'])
    outcome=('Both new cases pass their selected checks.' if all(reports[c['name']]['selected_screen_pass'] for c in plan['cases'])
             else 'Both new cases are audited; at least one selected check fails.') if completed==2 else f'{completed}/2 new cases audited; remaining results are pending.'
    plots=[]
    if completed:
        renderer=module('plots','render-bank-full.py')
        for case in plan['cases']:
            if case['name'] not in reports:continue
            asset=f'compact-bank-64-{case["name"]}.png'
            renderer.plot(reports[case['name']],ROOT/'docs/assets'/asset)
            plots.append(f'<figure><img src="assets/{asset}" alt="{case["temperature"]} degrees C {case["pattern"]} complete-bank accuracy and refinement"><figcaption>{case["temperature"]} °C, {case["pattern"]}: 128 reads per transient and 192 matched references.</figcaption></figure>')
    section=f'''<section id="compact-bank-64-cross"><h2>64-column bank: crossed temperature and illumination checks</h2>
<p><strong>{outcome}</strong> This batch adds 27 °C inverse and 125 °C alternating to the previously completed 27 °C alternating and 125 °C inverse cases. Four fresh transients and 384 new references are planned. Each pair uses 100/50 ns steps, 12 µs acquisition in 20 µs slots, the same distributed ground-return geometry and strict tolerances.</p>
<table><thead><tr><th>Temperature</th><th>Pattern</th><th>Selected result</th><th>Worst total error, µV</th><th>Worst tracking, µV</th><th>Sample refinement, µV</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>Accuracy limits are 500 µV; saved-sample and physical-event refinement limits are 10 µV. Pending results carry no pass claim. Each completed pair is independently audited from binary samples, frozen-state references and retained evidence. The earlier reports and plots are preserved.</p>
{''.join(plots)}
<p><strong>Remaining scope:</strong> uniform dark/middle/bright illumination, other operating and parasitic-placement conditions, local supply/reference checks, repeated rows with real drivers, and full-chip manufacturing qualification. Passing this matrix does not qualify those conditions.</p>
<p><a href="compact-bank-64-cross.md">Reproduction and limits</a> · <a href="../PICK_UP_HERE.md">Current handoff</a> · <a href="#compact-bank-64-full">Earlier two cases</a></p></section>'''
    (ROOT/'docs/compact-bank-64-cross-section.html').write_text(section+'\n')
    updater=module('overview','update-overview-sections.py');updater.main()
    print(json.dumps(dict(new_cases_audited=completed,previous_cases_preserved=True)))

if __name__=='__main__':main()
