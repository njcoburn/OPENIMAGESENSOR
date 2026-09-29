"""Audit complete pattern refinement and selected schematic/placement controls.

The previous screen remains an immutable input. This report does not convert
the selected hot inverse placement screen into an all-pattern/corner pass.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {'alternating': [0, 240] * 8, 'inverse': [240, 0] * 8,
            'dark': [0] * 16, 'middle': [80] * 16, 'bright': [240] * 16}
OPTIONS = '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def delta(a, b, nodes=None):
    differences = []
    assert len(a['samples']) == len(b['samples']) == 32
    for x, y in zip(a['samples'], b['samples']):
        assert (x['slot'], x['column'], x['time_s']) == (y['slot'], y['column'], y['time_s'])
        for node in nodes if nodes is not None else x['values'].keys() & y['values'].keys():
            differences.append((abs(y['values'][node] - x['values'][node]) * 1e6, node, x['slot'], x['column']))
    value, node, scan, column = max(differences)
    return dict(max_uV=value, node=node, scan=scan, column=column)


def check_variant(layout, meta, model):
    """Prove only the intended shunt endpoints change, keeping every RC/device."""
    original = (layout / 'rc-port.spice').read_text().splitlines()
    expected = original.copy()
    selected = meta['shunt_approximations'] if model == 'rc-far' else [
        shunt for shunt in meta['shunt_approximations'] if model == 'rc-' + shunt['net'].lower() + '-far']
    assert len(selected) == (19 if model == 'rc-far' else 1)
    for shunt in selected:
        index = meta['shunt_approximations'].index(shunt)
        before = f'CFIX{index} {shunt["net"]} GND {shunt["total_F"]:.17g}'
        after = f'CFIX{index} {shunt["far_node"]} GND {shunt["total_F"]:.17g}'
        assert expected.count(before) == 1 and shunt['total_F'] > 0
        expected[expected.index(before)] = after
    assert expected == (layout / (model + '.spice')).read_text().splitlines(), model
    return [shunt['net'] for shunt in selected]


def audit_run(directory, layout, meta, reader, bank, dc_reader):
    r = json.loads((directory / 'result.json').read_text())
    assert r['completed'] and r['phase'] == 'full' and r['columns'] == 16
    assert r['solver'] == 'klu' and r['method'] == 'trap' and r['driver_form'] == 'current'
    assert r['layout_gds_sha256'] == meta['gds_sha256']
    assert r['temperature_C'] in [27, 125] and r['step_ns'] in [50, 100]
    source = layout / (r['model'] + '.spice')
    assert sha(source) == meta['hashes'][source.name]
    expected_model = source.read_text().replace('.subckt reference ', '.subckt tile ').replace('.ends reference', '.ends tile')
    assert (directory / 'tile.spice').read_text() == expected_model
    assert sha(directory / 'tile.spice') == r['model_sha256']
    ex = r['transient']
    assert ex == json.loads((directory / 'transient/execution.json').read_text())
    assert ex['completed'] and ex['returncode'] == 0 and not ex['timed_out'] and not ex['errors']
    deck = (directory / 'transient/test.spice').read_text()
    assert sha(directory / 'transient/test.spice') == ex['deck_sha256']
    assert OPTIONS in deck and '\nset klu\n' in deck and 'uic' not in deck.lower()
    assert f'.tran {r["step_ns"]:g}n 0.003 0 {r["step_ns"]:g}n' in deck
    assert f'.temp {r["temperature_C"]:g}\n' in deck
    assert 'Vsource RAW 0 3.3\nRsupply RAW VDD 2\n' in deck
    for corner in ['typical', 'diode_typical', 'mimcap_typical']:
        assert f'/sm141064.ngspice {corner}\n' in deck
    ix, data = reader.trace(directory / 'transient/stream.raw')
    assert np.isfinite(data).all() and np.all(np.diff(data[:, 0]) > 0)
    assert abs(data[0, 0]) < 1e-15 and abs(data[-1, 0] - .003) < 1e-12
    assert len(data) == ex['points'] and np.max(np.diff(data[:, 0])) <= r['step_ns'] * 1.001e-9
    at = bank.trace_sampler(ix, data)
    for node, value in r['capture_state'].items():
        assert at(node, .0014 - 1e-9) == value
    slots, stop = bank.readout_schedule(16)
    assert stop == r['stop_s'] and len(slots) == len(r['samples']) == 32
    for sample, (slot, column, start) in zip(r['samples'], slots):
        assert (sample['slot'], sample['column'], sample['time_s']) == (slot, column, start + 11.999e-6)
        for node, value in sample['values'].items():
            assert at(node, sample['time_s']) == value
        values = sample['values']
        assert values['SC'] < .01 and values['SCB'] > 3 and values['ROW0'] < .01 and values['RST0'] > 3
        assert values[f'SEL{column}'] > 3 and values[f'SELB{column}'] < .01
        assert all(values[f'SEL{c}'] < .01 and values[f'SELB{c}'] > 3 for c in range(16) if c != column)
    for c, value in enumerate(r['storage_reset_window_change_V']):
        assert at(f'STORE{c}', .001405) - at(f'STORE{c}', .0014025) == value
    roles = meta['pixel_roles'] if r['model'] != 'reference' else {
        str(c): dict(sense=f'SENSE{c}', anode='GND') for c in range(16)}

    def node(name):
        return '0' if name == 'GND' else name if name in meta['ports'] else 'xtile.' + name

    pixels = [(node(roles[str(c)]['sense']), node(roles[str(c)]['anode'])) for c in range(16)]
    for c, (sense, anode) in enumerate(pixels):
        assert f'Ilight{c} {sense} {anode} {r["lights_pA"][c]:g}p\n' in deck

    def check_reference(path, ref, t, column, stores):
        execution = ref['execution']
        assert execution == json.loads((path / 'execution.json').read_text())
        assert execution['completed'] and not execution['errors'] and not execution['timed_out'] and execution['returncode'] == 0
        assert sha(path / 'test.spice') == execution['deck_sha256']
        dc = (path / 'test.spice').read_text()
        assert 'PWL(' not in dc and 'Ilight' not in dc and OPTIONS in dc and '\nset klu\n' in dc
        assert 'optran 1 1 1 100n 400u 0\nop\nwrite op.raw' in dc
        for c, (sense, anode) in enumerate(pixels):
            voltage = at(sense, t) - at(anode, t)
            assert f'Bsense{c} {sense} {anode} I=(V({sense},{anode})-({voltage:.17g}))/1\n' in dc
            assert f'Vctl_SEL{c} CTL_SEL{c} 0 {int(c == column)}\n' in dc
            if stores:
                assert f'Bstore{c} STORE{c} 0 I=(V(STORE{c})-({at(f"STORE{c}", t):.17g}))/1\n' in dc
        for control, value in dict(RST0=int(stores), ROW0=int(not stores), SC=int(not stores)).items():
            assert f'Vctl_{control} CTL_{control} 0 {value}\n' in dc
        values = dc_reader.dc_values(path / 'op.raw')
        for name, value in ref['values'].items():
            assert values[f'v({name.lower()})'] == value
        assert abs(ref['values']['ADCIN'] - ref['values']['HOLD']) < 1e-8

    if r['references_requested']:
        assert r['reference_progress'] == dict(completed=48, expected=48)
        assert len(r['capture_references']) == 16
        for c, ref in enumerate(r['capture_references']):
            check_reference(directory / f'capture{c}-reference', ref, .0014 - 1e-9, c, False)
        for sample in r['samples']:
            c = sample['column']
            check_reference(directory / f'{sample["slot"]}{c}-output-reference', sample['output_reference'], sample['time_s'], c, True)
            capture = r['capture_references'][c]['values']
            assert sample['total_capture_readout_error_V'] == sample['values']['HOLD'] - capture['HOLD']
            assert sample['output_tracking_error_V'] == sample['values']['HOLD'] - sample['output_reference']['values']['HOLD']
            assert sample['storage_capture_error_V'] == sample['values'][f'STORE{c}'] - capture[f'STORE{c}']
        for kind in ['total_capture_readout', 'output_tracking']:
            assert r['max_' + kind + '_error_V'] == max(abs(s[kind + '_error_V']) for s in r['samples'])
        assert r['capture_readout_pass'] == (r['max_total_capture_readout_error_V'] < 500e-6)
        assert r['tracking_pass'] == (r['max_output_tracking_error_V'] < 500e-6)
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior', type=Path, default=ROOT / 'simulations/compact-bank-16-screen.json')
    parser.add_argument('--batch', type=Path, required=True)
    args = parser.parse_args()
    prior = json.loads(args.prior.read_text())
    batch = json.loads((args.batch / 'batch.json').read_text())
    assert batch['expected'] == len(batch['runs']) == 32 and all(r['completed'] for r in batch['runs'])
    print('Verifying prior evidence hashes...', flush=True)
    for name, digest in prior['evidence_hashes'].items():
        assert sha(ROOT / name) == digest, name
    layout = ROOT / prior['layout']
    meta = json.loads((layout / 'verification.json').read_text())
    assert meta['columns'] == 16 and meta['ground_bus_width_um'] == 8
    assert meta['direct_and_resistor_collapsed_lvs'] and meta['magic_drc_errors'] == meta['klayout_main_drc_errors'] == 0
    assert sha(layout / 'bank.gds') == meta['gds_sha256'] == prior['layout_gds_sha256']
    planned = module('extension', 'extend-bank-16-screen.py').jobs(meta)
    assert batch['planned_cases'] == planned
    assert {c['name'] for c in batch['runs']} == {c['name'] for c in planned}
    reader = module('reader', 'diagnose-capture-transient.py')
    bank = module('bank', 'simulate-compact-bank.py')
    dc_reader = module('dc_reader', 'report-compact-bank-16.py')
    records = {}
    evidence = {args.prior.resolve(), (layout / 'verification.json'), layout / 'bank.gds', Path(__file__).resolve()}
    evidence.update(ROOT / 'scripts' / name for name in ['extend-bank-16-screen.py', 'simulate-compact-bank.py',
                    'diagnose-capture-transient.py', 'report-compact-bank-16.py', 'run-tools.sh',
                    'test-bank-16-extension-audit.py', 'render-bank-16-extension.py'])
    evidence.update(f.resolve() for f in args.batch.rglob('*') if f.is_file())
    rows = []
    for row in prior['rows'] + batch['runs']:
        directory = ROOT / row['run']
        r = audit_run(directory, layout, meta, reader, bank, dc_reader)
        pattern, = [name for name, lights in PATTERNS.items() if lights == r['lights_pA']]
        key = (r['temperature_C'], pattern, r['step_ns'], r['model'])
        assert key not in records
        assert (row['temperature_C'], row['pattern'], row['step_ns'], row['model']) == key
        assert bool(row['references']) == r['references_requested']
        records[key] = r
        evidence.add(layout / (r['model'] + '.spice'))
        records_row = dict(run=row['run'], temperature_C=key[0], pattern=pattern, step_ns=key[2], model=key[3],
                           references=48 if r['references_requested'] else 0, transient_seconds=r['transient']['seconds'])
        if r['references_requested']:
            records_row.update(total_error_uV=r['max_total_capture_readout_error_V'] * 1e6,
                               tracking_error_uV=r['max_output_tracking_error_V'] * 1e6)
        rows.append(records_row)
        print('Audited ' + row['run'], flush=True)
    expected = {(t, p, s, 'rc-port') for t in [27, 125] for p in PATTERNS for s in [100, 50]}
    expected |= {(t, 'alternating', 100, 'rc-far') for t in [27, 125]}
    expected |= {(t, 'inverse', s, 'reference') for t in [27, 125] for s in [100, 50]}
    variants = ['rc-far'] + ['rc-' + v['net'].lower() + '-far' for v in meta['shunt_approximations']]
    expected |= {(125, 'inverse', 100, model) for model in variants}
    assert set(records) == expected and len(records) == 46
    assert sum(row['references'] for row in rows) == 1152
    refinement = []
    for t in [27, 125]:
        for pattern in PATTERNS:
            a, b = [records[t, pattern, step, 'rc-port'] for step in [100, 50]]
            refinement.append(dict(temperature_C=t, pattern=pattern, terminals=delta(a, b), hold=delta(a, b, ['HOLD'])))
    placement = []
    for model in variants:
        nets = check_variant(layout, meta, model)
        base, placed = records[125, 'inverse', 100, 'rc-port'], records[125, 'inverse', 100, model]
        placement.append(dict(model=model, nets=nets, temperature_C=125, pattern='inverse',
                              hold=delta(base, placed, ['HOLD']), stores=delta(base, placed, [f'STORE{c}' for c in range(16)]),
                              terminals=delta(base, placed)))
    schematic = []
    for t in [27, 125]:
        a, b = [records[t, 'inverse', step, 'reference'] for step in [100, 50]]
        physical = records[t, 'inverse', 50, 'rc-port']
        schematic.append(dict(temperature_C=t, pattern='inverse', terminals=delta(a, b), hold=delta(a, b, ['HOLD']),
                              physical_schematic_output_difference=delta(b, physical, ['HOLD']),
                              physical_schematic_store_difference=delta(b, physical, [f'STORE{c}' for c in range(16)])))
    accuracy = [r for r in records.values() if r['references_requested']]
    checks = dict(accuracy=all(r['capture_readout_pass'] and r['tracking_pass'] for r in accuracy),
                  five_pattern_physical_refinement=all(r['terminals']['max_uV'] < 10 for r in refinement),
                  inverse_schematic_refinement=all(r['terminals']['max_uV'] < 10 for r in schematic),
                  hot_inverse_placement=all(max(r['hold']['max_uV'], r['stores']['max_uV']) < 10 for r in placement))
    physical = {k: r for k, r in records.items() if k[3] == 'rc-port'}
    checks['contrast_order'] = all(s['values']['HOLD'] > r['samples'][(s['column'] ^ 1) + (16 if s['slot'] == 'last' else 0)]['values']['HOLD']
                                  for (t, p, step, model), r in physical.items() if p in ['alternating', 'inverse']
                                  for s in r['samples'] if r['lights_pA'][s['column']] == 0)
    checks['brightness_order'] = all(all(x > y for x, y in zip(values, values[1:])) for values in
                                   [[physical[t, p, step, 'rc-port']['samples'][i]['values']['HOLD'] for p in ['dark', 'middle', 'bright']]
                                    for t in [27, 125] for step in [100, 50] for i in range(32)])
    report = dict(scope=__doc__, layout=prior['layout'], layout_gds_sha256=meta['gds_sha256'], prior_report=str(args.prior.resolve().relative_to(ROOT)),
                  prior_evidence_files_verified=len(prior['evidence_hashes']), rows=rows, refinement=refinement,
                  placement=placement, schematic=schematic, checks=checks, selected_screen_pass=all(checks.values()),
                  new_transients=32, total_transients=46, new_references=576, total_references=1152,
                  max_total_error_uV=max(r['max_total_capture_readout_error_V'] for r in accuracy) * 1e6,
                  max_tracking_error_uV=max(r['max_output_tracking_error_V'] for r in accuracy) * 1e6,
                  full_16_column_qualification=False, full_64_column_qualification=False,
                  limits=['Typical process and nominal wire RC only; 27/125 C and nominal supply',
                          'Individual and joint placement extension covers inverse 240/0 pA at 125 C only',
                          'Schematic comparisons cover inverse 240/0 pA at 27/125 C only',
                          'Physical/schematic response difference is a separate metric without an assigned threshold',
                          'Other placement/schematic patterns, process/wire/supply corners and local supply/reference checks remain open',
                          'One capture, two scans, behavioral drivers, external bias resistors/ADC; no full 64-column or 64x64 pass'],
                  evidence_hashes={str(f.resolve().relative_to(ROOT)): sha(f) for f in sorted(evidence)})
    (ROOT / 'simulations/compact-bank-16-extension.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['checks', 'max_total_error_uV', 'max_tracking_error_uV', 'total_references']}, indent=2))
    if not report['selected_screen_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
