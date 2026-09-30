"""Publish uniform-pattern progress from independent audits, preserving the bank views."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def read_reports(plan):
    active = {(c['temperature'], c['pattern']) for c in plan['cases']}
    assert len(active) == 2 and {t for t, _ in active} == {27, 125}
    assert len({p for _, p in active}) == 1
    assert all(p in ('dark', 'middle', 'bright') for _, p in active)
    cases, reports = [], {}
    for pattern in ('dark', 'middle', 'bright'):
        for temperature in (27, 125):
            name = f'{pattern}{temperature}'
            filename = f'compact-bank-64-uniform-{name}.json'
            cases.append(dict(name=name, pattern=pattern, temperature=temperature,
                              report=filename, active=(temperature, pattern) in active))
            path = ROOT / 'simulations' / filename
            if not path.exists():
                continue
            report = json.loads(path.read_text())
            assert (report['temperature_C'], report['pattern']) == (temperature, pattern)
            assert report['full_bank_readout_completed']
            assert not report['full_bank_accuracy_qualified'] and not report['full_chip_qualified']
            assert report['contrast_order_applicable'] is False
            assert set(report['checks']) == {'capture_readout', 'output_tracking', 'refinement', 'event_refinement'}
            assert report['selected_screen_pass'] == all(report['checks'].values())
            assert [r['samples'] for r in report['runs']] == [128, 128]
            assert [r['references'] for r in report['runs']] == [192, 0]
            assert report['acquisition_us'] == 12
            assert report['layout'] == 'build/compact-bank-c64-ground-grid-20260927'
            reports[name] = report
    return cases, reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    cases, reports = read_reports(plan)
    rows, plots = [], []
    for case in cases:
        report = reports.get(case['name'])
        if report is None:
            state = 'Pending audit' if case['active'] else 'Not started'
            values = f'<td>{state}</td><td>—</td><td>—</td><td>—</td>'
        else:
            state = 'PASS' if report['selected_screen_pass'] else 'FAIL'
            values = (f'<td><a href="../simulations/{case["report"]}">{state}</a></td>'
                      f'<td>{report["max_total_error_uV"]:.3f}</td>'
                      f'<td>{report["max_tracking_error_uV"]:.3f}</td>'
                      f'<td>{report["max_refinement_uV"]:.3f}</td>')
            asset = f'compact-bank-64-uniform-{case["name"]}.png'
            module('plots', 'render-bank-full.py').plot(report, ROOT / 'docs/assets' / asset)
            plots.append(f'<figure><img src="assets/{asset}" alt="Uniform {case["pattern"]}, {case["temperature"]} degrees C: independently audited accuracy and refinement"></figure>')
        current = {'dark': 0, 'middle': 80, 'bright': 240}[case['pattern']]
        rows.append(f'<tr><td>{case["pattern"]}: {current} pA/pixel</td><td>{case["temperature"]} °C</td>{values}</tr>')
    completed = sum(c['name'] in reports for c in plan['cases'])
    fragment = f'''<!-- BEGIN BANK_UNIFORM -->
<div id="compact-bank-64-uniform"><h3>Uniform illumination: dark, middle and bright</h3>
<p><strong>{completed}/2 cases in the current batch independently audited.</strong> Each bounded batch tests one uniform pattern at 27/125 °C: four fresh 100/50 ns transients and 384 matched references. Pending audit does not imply success; consult the watcher status for live progress or failures.</p>
<table><thead><tr><th>Uniform illumination</th><th>Temperature</th><th>Result</th><th>Total error, µV</th><th>Tracking, µV</th><th>Sample refinement, µV</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>The 500 µV accuracy and 10 µV refinement limits are unchanged. Uniform scenes have no dark/bright neighbor contrast check; it is explicitly not applicable. Physical MIM event refinement remains independently checked. The completed alternating/inverse reports and exact GDS remain unchanged.</p>
{''.join(plots)}
<p>All six uniform cases would require 12 transients and 1,152 references. Each pair will be reviewed before launching the next pattern. Remaining corners, parasitic placements, real drivers, repeated rows and final-chip checks remain open.</p>
<p><a href="compact-bank-64-uniform.md">Reproduction and limits</a> · <a href="../PICK_UP_HERE.md">Current handoff</a></p></div>
<!-- END BANK_UNIFORM -->'''
    (ROOT / 'docs/compact-bank-64-uniform-fragment.html').write_text(fragment + '\n')
    section = ROOT / 'docs/64x64-first-silicon-section.html'
    content = section.read_text()
    pattern = r'<!-- BEGIN BANK_UNIFORM -->.*?<!-- END BANK_UNIFORM -->'
    if re.search(pattern, content, re.S):
        content, count = re.subn(pattern, lambda _: fragment, content, flags=re.S)
        assert count == 1
    else:
        content = content.replace('</section>', fragment + '\n</section>')
    section.write_text(content)
    module('overview', 'update-overview-sections.py').main()
    print(json.dumps(dict(current_cases_audited=completed, all_uniform_cases_audited=len(reports))))


if __name__ == '__main__':
    main()
