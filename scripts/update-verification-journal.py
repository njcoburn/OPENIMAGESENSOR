"""Refresh the living verification record from retained reports, without simulations.

This validates catalogue/report identity and reported metrics, not raw waveforms.
Missing or changed evidence is an error; it must never become a displayed pass.
"""
import argparse
import hashlib
from html import escape
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'verification/compact-bank-suite.json'
JOURNAL = ROOT / 'docs/verification-journal.html'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_cases(catalog, root=ROOT):
    require(catalog['schema_version'] == 1, 'Unsupported catalogue version')
    ids = [case['id'] for case in catalog['cases']]
    require(len(ids) == len(set(ids)), 'Duplicate case IDs')
    result = []
    for case in catalog['cases']:
        path = root / case['report']
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == case['report_sha256'],
                f"Report changed: {case['report']}; record a new reviewed revision")
        report = json.loads(data)
        require(report['pattern'] == case['pattern'] and
                report['temperature_C'] == case['temperature_C'], 'Case identity mismatch')
        require(report.get('model', 'rc-port') == case['model'], 'Model mismatch')
        layout = catalog['layout']['directory']
        require(report['layout'] == layout and
                report['evidence_hashes'][layout + '/bank.gds'] == catalog['layout']['gds_sha256'],
                'Layout identity mismatch')
        require(report['acquisition_us'] == catalog['settings']['acquisition_us'], 'Timing mismatch')
        require([(r['samples'], r['references']) for r in report['runs']] == [(128, 192), (128, 0)],
                'Incomplete sample/reference counts')
        limits = catalog['limits_uV']
        metrics = {
            'capture_readout': (report['max_total_error_uV'], limits['total_error']),
            'output_tracking': (report['max_tracking_error_uV'], limits['output_tracking']),
            'refinement': (report['max_refinement_uV'], limits['saved_sample_refinement']),
            'event_refinement': (report['event_refinement_worst']['difference_uV'], limits['physical_event_refinement']),
        }
        expected = set(metrics)
        if case['pattern'] in ('alternating', 'inverse'):
            expected.add('contrast_order')
        else:
            require(report['contrast_order_applicable'] is False, 'Uniform contrast must be N/A')
        if case['model'] == 'rc-far':
            baseline = next(c for c in catalog['cases'] if c['id'] == case['baseline_case'])
            require(report['baseline_report'] == baseline['report'], 'Wrong placement baseline')
            placement = report['placement']
            require(placement['limit_uV'] == limits['placement_hold_store'], 'Placement limit mismatch')
            metrics['placement'] = (max(placement['hold_max_uV'], placement['store_max_uV']),
                                    limits['placement_hold_store'])
            expected.add('placement')
        require(set(report['checks']) == expected, 'Missing/unexpected check')
        require(all(type(v) is bool for v in report['checks'].values()), 'Non-boolean check')
        for name, (value, limit) in metrics.items():
            require(math.isfinite(value) and value >= 0, 'Invalid metric')
            require(report['checks'][name] == (value < limit), f'{name}: check/metric mismatch')
        require(report['selected_screen_pass'] == all(report['checks'].values()), 'Pass flag mismatch')
        require(report['full_bank_accuracy_qualified'] is False and report['full_chip_qualified'] is False,
                'Unexpected promotion of qualification scope')
        result.append((case, report))
    return result


def render(catalog, cases):
    rows = []
    for case, report in cases:
        placement = report.get('placement')
        delta = f"{max(placement['hold_max_uV'], placement['store_max_uV']):.3f}" if placement else '—'
        state = 'PASS' if report['selected_screen_pass'] else 'FAIL'
        values = [case['pattern'], str(case['temperature_C']), case['model'],
                  f"{report['max_total_error_uV']:.3f}", f"{report['max_tracking_error_uV']:.3f}",
                  f"{report['max_refinement_uV']:.3f}",
                  f"{report['event_refinement_worst']['difference_uV']:.3f}", delta]
        cells = ''.join(f'<td>{escape(v)}</td>' for v in values)
        rows.append(f'<tr>{cells}<td><a href="../{escape(case["report"], quote=True)}">{state}</a></td></tr>')
    transients = sum(len(r['runs']) for _, r in cases)
    references = sum(run['references'] for _, r in cases for run in r['runs'])
    passed = sum(r['selected_screen_pass'] for _, r in cases)
    result = f'<p><strong>{passed}/{len(cases)} selected cases pass; {transients} transients and {references:,} independent references.</strong> Revision: <code>{escape(catalog["revision"])}</code>. Reviewed through {escape(catalog["last_updated"])}.</p>\n'
    result += '<div class="scroll"><table><caption>All errors and differences are in µV. Click a result for its audited report.</caption><thead><tr><th>Pattern</th><th>°C</th><th>Model</th><th>Total error</th><th>Tracking</th><th>Sample refinement</th><th>Event refinement</th><th>Placement change</th><th>Result</th></tr></thead><tbody>'
    result += '\n'.join(rows) + '</tbody></table></div>\n'
    result += '<p>This table checks the identity and consistency of saved reports. Refreshing it does not rerun simulations or independently re-audit raw traces. A PASS applies only to the stated case and limits.</p>'
    history = '<ol class="history">\n'
    for entry in catalog['history']:
        history += f'<li><strong>{escape(entry["date"])} — {escape(entry["title"])}</strong><p>{escape(entry["detail"])} <a href="../{escape(entry["evidence"], quote=True)}">Record</a></p></li>\n'
    return result, history + '</ol>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check report identity and journal freshness without writing')
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text())
    cases = load_cases(catalog)
    results, history = render(catalog, cases)
    original = JOURNAL.read_text()
    updated = original
    for marker, content in [('RESULTS', results), ('HISTORY', history)]:
        pattern = rf'<!-- BEGIN {marker} -->.*?<!-- END {marker} -->'
        updated, count = re.subn(pattern, lambda _: f'<!-- BEGIN {marker} -->\n{content}\n<!-- END {marker} -->', updated, flags=re.S)
        require(count == 1, f'Expected one {marker} section')
    overview = ROOT / 'docs/overview.html'
    overview_original = overview.read_text()
    body = updated.split('<main>', 1)[1].split('</main>', 1)[0]
    # Inline the full journal as expandable content; prefix its anchors to avoid
    # collisions with the overview's historical sections.
    body = re.sub(r'id="([^"]+)"', r'id="journal-\1"', body)
    body = re.sub(r'href="#([^"]+)"', r'href="#journal-\1"', body)
    body = body.replace('<section ', '<div ').replace('</section>', '</div>')
    fragment = ('<!-- BEGIN VERIFICATION_JOURNAL -->\n<section id="verification-journal">'
                '<h2>Verification journal — tests, results and reruns</h2>'
                '<p>The running record explains the physical checks, circuit simulations and audit software, '
                'and the workflow for repeating them after a pixel change. '
                '<a href="verification-journal.html">Open the complete journal</a> · '
                '<a href="#compact-bank-process">Process-variation batch</a></p>'
                '<p>The retained baseline has 12 selected passing bank cases, 24 transients and 2,304 references. '
                'Process-variation results are separate and must be audited before any pass is claimed.</p>'
                '<details><summary>Read the verification journal here</summary>' + body + '</details>'
                '</section>\n<!-- END VERIFICATION_JOURNAL -->')
    overview_updated = re.sub(r'<!-- BEGIN VERIFICATION_JOURNAL -->.*?<!-- END VERIFICATION_JOURNAL -->',
                              '', overview_original, flags=re.S)
    overview_updated = overview_updated.replace('<main>', '<main>' + fragment, 1)
    if 'href="#verification-journal"' not in overview_updated.split('</nav>', 1)[0]:
        overview_updated = overview_updated.replace('<nav>', '<nav><a href="#verification-journal">Verification journal</a>', 1)
    if args.check:
        require(updated == original and overview_updated == overview_original, 'Journal/overview is stale; run without --check')
    else:
        JOURNAL.write_text(updated)
        overview.write_text(overview_updated)
    print(f'{len(cases)} retained reports validated; journal {"current" if args.check else "updated"}. No simulations launched; raw evidence not rehashed.')


if __name__ == '__main__':
    main()
