"""Show independently audited joint-placement checks without changing earlier reports."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args(); plan = json.loads(args.plan.read_text())
    rows, plots = [], []
    for case in plan['cases']:
        path = ROOT / 'simulations' / case['report']
        if not path.exists():
            cells = '<td>Pending audit</td><td>—</td><td>—</td><td>—</td>'
        else:
            report = json.loads(path.read_text())
            assert (report['temperature_C'], report['pattern'], report['model']) == (case['temperature'], case['pattern'], 'rc-far')
            assert report['selected_screen_pass'] == all(report['checks'].values())
            assert len(report['placement_nets']) == 67 and not report['full_chip_qualified']
            assert not report['full_bank_accuracy_qualified']
            outcome = 'PASS' if report['selected_screen_pass'] else 'FAIL'
            cells = (f'<td><a href="../simulations/{case["report"]}">{outcome}</a></td>'
                     f'<td>{report["max_total_error_uV"]:.3f}</td>'
                     f'<td>{report["placement"]["hold_max_uV"]:.3f}</td>'
                     f'<td>{report["placement"]["store_max_uV"]:.3f}</td>')
            asset = f'compact-bank-64-placement-{case["name"]}.png'
            module('plot', 'render-bank-full.py').plot(report, ROOT / 'docs/assets' / asset)
            plots.append(f'<figure><img src="assets/{asset}" alt="Joint far-node placement: {case["temperature"]} degrees C, {case["pattern"]}"></figure>')
        rows.append(f'<tr><td>{case["temperature"]} °C / {case["pattern"]}</td>{cells}</tr>')
    fragment = f'''<!-- BEGIN BANK_PLACEMENT -->
<div id="compact-bank-64-placement"><h3>64-column parasitic placement sensitivity</h3>
<p>This bounded batch jointly moves the 67 conserved positive shunt-capacitance totals from their ports to the recorded far nodes. An exact netlist comparison checks that only those endpoints change. It uses nominal alternating and hot inverse illumination, four 100/50 ns transients and 384 references.</p>
<table><thead><tr><th>Case</th><th>Selected result</th><th>Total error, µV</th><th>HOLD placement change, µV</th><th>STORE placement change, µV</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>Accuracy remains limited to 500 µV, timestep and physical-event refinement to 10 µV, and HOLD/STORE placement sensitivity to 10 µV. Placement comparisons use the matching retained port-model baseline. Pending results carry no pass claim. A joint check does not qualify individual placements, other patterns or operating corners.</p>
{''.join(plots)}
<p>Real drivers, repeated rows and final-chip qualification remain open. See <a href="../PICK_UP_HERE.md">current handoff</a> for the automatic continuation status.</p></div>
<!-- END BANK_PLACEMENT -->'''
    (ROOT / 'docs/compact-bank-64-placement-fragment.html').write_text(fragment + '\n')
    path = ROOT / 'docs/64x64-first-silicon-section.html'; text = path.read_text()
    pattern = r'<!-- BEGIN BANK_PLACEMENT -->.*?<!-- END BANK_PLACEMENT -->'
    if re.search(pattern, text, re.S):text = re.sub(pattern, lambda _: fragment, text, flags=re.S)
    else:text = text.replace('</section>', fragment + '\n</section>')
    path.write_text(text); module('overview', 'update-overview-sections.py').main()


if __name__ == '__main__':main()
