"""Independently audit the selected column-62 diagnostic; no full-bank claim."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'simulations/compact-bank-64-far-read.json')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('probe', ROOT / 'scripts/probe-bank-readout.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = json.loads((args.run / 'probe-result.json').read_text())
    for name, digest in report['evidence_hashes'].items():
        assert probe.sha(ROOT / name) == digest, name
    layout = ROOT / report['layout']
    meta = json.loads((layout / 'verification.json').read_text())
    result = json.loads((args.run / 'result.json').read_text())
    assert meta['columns'] == report['columns'] == 64 and meta['ground_bus_width_um'] == 8
    assert report['column_read'] == result['column_read'] == 62
    assert result['diagnostic_only'] and not result['full_bank_readout_completed'] and not result['electrical_accuracy_qualified']
    assert not report['full_bank_readout_completed'] and not report['full_bank_accuracy_qualified']
    assert result['completed'] and report['completed'] and result['model'] == 'rc-port'
    assert result['layout_gds_sha256'] == meta['gds_sha256'] == probe.sha(layout / 'bank.gds')
    assert result['model_sha256'] == meta['hashes']['rc-port.spice'] == probe.sha(args.run / 'tile.spice') == probe.sha(layout / 'rc-port.spice')
    assert result['lights_pA'] == [0, 240] * 32
    assert result['temperature_C'] == report['temperature_C'] == 27 and result['step_ns'] == report['step_ns'] == 100
    assert result['method'] == 'trap' and result['driver_form'] == 'current' and result['solver'] == 'klu'
    assert result['stop_s'] == .00270
    assert result['readout_slots'] == [dict(slot='first', column=62, start_s=.00141), dict(slot='last', column=62, start_s=.00267)]
    assert result['transient'] == json.loads((args.run / 'transient/execution.json').read_text())
    ex = result['transient']
    assert ex['completed'] and ex['returncode'] == 0 and not ex['timed_out'] and not ex['errors']
    assert ex['deck_sha256'] == probe.sha(args.run / 'transient/test.spice')
    deck = (args.run / 'transient/test.spice').read_text()
    assert '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2' in deck
    assert '\nset klu\n' in deck and 'uic' not in deck.lower()
    for c in range(64):
        if c != 62:
            assert f'Vctl_SEL{c} CTL_SEL{c} 0 PWL(0 0)\n' in deck
    reader = probe.module('reader', 'diagnose-capture-transient.py')
    bank = probe.module('bank', 'simulate-compact-bank.py')
    dc = probe.module('dc', 'report-compact-bank-16.py')
    ix, data = reader.trace(args.run / 'transient/stream.raw')
    assert np.isfinite(data).all() and np.all(np.diff(data[:, 0]) > 0)
    assert abs(data[0, 0]) < 1e-15 and abs(data[-1, 0] - .0027) < 1e-12
    assert len(data) == ex['points'] and np.max(np.diff(data[:, 0])) <= 100e-9 * 1.001
    at = bank.trace_sampler(ix, data)
    for node, value in result['capture_state'].items():
        assert at(node, .0014 - 1e-9) == value
    assert len(result['samples']) == len(report['samples']) == 2
    references = report['references']
    assert set(references) == {'capture', 'first', 'last'}
    for name, t, stores in [('capture', .0014 - 1e-9, False), ('first', .00141 + 11.999e-6, True), ('last', .00267 + 11.999e-6, True)]:
        directory = args.run / (name + '-probe-reference')
        expected = probe.reference_deck(deck, meta, at, t, 62, stores)
        assert (directory / 'test.spice').read_text() == expected
        execution = references[name]['execution']
        assert execution == json.loads((directory / 'execution.json').read_text())
        assert execution['returncode'] == 0 and not execution['timed_out'] and not execution['errors']
        assert execution['deck_sha256'] == probe.sha(directory / 'test.spice')
        assert dc.dc_values(directory / 'op.raw') == references[name]['values']
        assert abs(references[name]['values']['v(adcin)'] - references[name]['values']['v(hold)']) < 1e-8
    for sample, checked, (scan, t) in zip(result['samples'], report['samples'], [('first', .00141 + 11.999e-6), ('last', .00267 + 11.999e-6)]):
        assert sample['slot'] == checked['scan'] == scan and sample['column'] == checked['column'] == 62
        assert sample['time_s'] == checked['time_s'] == t
        for node, value in sample['values'].items():
            assert at(node, t) == value
        v = sample['values']
        assert v['SC'] < .01 and v['SCB'] > 3 and v['RST0'] > 3 and v['ROW0'] < .01
        assert v['SEL62'] > 3 and v['SELB62'] < .01
        assert all(v[f'SEL{c}'] < .01 and v[f'SELB{c}'] > 3 for c in range(64) if c != 62)
        assert checked['hold_V'] == v['HOLD']
        assert checked['total_error_uV'] == (v['HOLD'] - references['capture']['values']['v(hold)']) * 1e6
        assert checked['tracking_error_uV'] == (v['HOLD'] - references[scan]['values']['v(hold)']) * 1e6
    assert report['selected_capture_readout_pass'] == all(abs(s['total_error_uV']) < 500 for s in report['samples'])
    assert report['selected_tracking_pass'] == all(abs(s['tracking_error_uV']) < 500 for s in report['samples'])
    report['independent_audit_completed'] = True
    report['ground_return_grid'] = bool(meta.get('ground_return_grid'))
    report['evidence_hashes'][str((args.run / 'probe-result.json').resolve().relative_to(ROOT))] = probe.sha(args.run / 'probe-result.json')
    for path in [Path(__file__), ROOT / 'scripts/probe-bank-readout.py', ROOT / 'scripts/test-bank-probe-references.py',
                 layout / 'verification.json', layout / 'bank.gds', layout / 'rc-port.spice']:
        report['evidence_hashes'][str(path.resolve().relative_to(ROOT))] = probe.sha(path)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['samples', 'selected_capture_readout_pass', 'selected_tracking_pass']}, indent=2))


if __name__ == '__main__':
    main()
