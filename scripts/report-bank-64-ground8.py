"""Audit the 64-column ground-bus candidate and compare its capture event window.

The original full trace timed out after this window. Its verified prefix is
used only for event diagnosis, never as a complete readout/accuracy result.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout', type=Path, required=True)
    p.add_argument('--geometry', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--refined', type=Path, required=True)
    p.add_argument('--original-probed', type=Path, required=True)
    p.add_argument('--network', type=Path, default=ROOT / 'simulations/compact-bank-ground-network-20260927.json')
    p.add_argument('--original', type=Path, default=ROOT / 'build/compact-bank-c64-full-klu-20260927')
    p.add_argument('--prior', type=Path, default=ROOT / 'simulations/compact-bank-solver-20260927.json')
    a = p.parse_args()
    meta = json.loads((a.layout / 'verification.json').read_text())
    geometry = json.loads((a.geometry / 'result.json').read_text())
    prior = json.loads(a.prior.read_text())
    assert meta['columns'] == 64 and meta['ground_bus_width_um'] == 8
    assert (meta['mos'], meta['mim'], meta['diodes']) == (642, 512, 64)
    assert meta['magic_drc_errors'] == meta['klayout_main_drc_errors'] == 0 and meta['direct_and_resistor_collapsed_lvs']
    assert geometry['columns'] == 64 and geometry['only_ground_bus_rectangle_changed'] and geometry['reference_identical']
    assert sha(a.layout / 'bank.gds') == meta['gds_sha256']
    for file, digest in geometry['evidence_hashes'].items():
        assert sha(ROOT / file) == digest
    old_meta = json.loads((ROOT / geometry['original'] / 'verification.json').read_text())
    original_prefix = str(a.original.resolve().relative_to(ROOT)) + '/'
    original_hashes = {f: h for f, h in prior['evidence_hashes'].items() if f.startswith(original_prefix)}
    assert len(original_hashes) == 9
    for file, digest in original_hashes.items():
        assert sha(ROOT / file) == digest
    reader = module('reader', 'diagnose-capture-transient.py')
    bank = module('bank', 'simulate-compact-bank.py')
    reports = []
    decks = []
    traces = []
    events = [('before_capture_open', .0014 - 1e-9), ('after_capture_open', .001401),
              ('before_row_off', .001402 - 1e-9), ('after_row_off', .0014025),
              ('before_pixel_reset', .001403 - 1e-9), ('after_pixel_reset', .001405)]
    directories = [a.original, a.run, a.refined, a.original_probed]
    for index, directory in enumerate(directories):
        r = json.loads((directory / 'result.json').read_text())
        assert r['columns'] == 64 and r['model'] == 'rc-port' and r['solver'] == 'klu'
        # The older retained runner predates these summary fields. The strict
        # deck options and current-form drivers are independently checked below.
        assert r.get('method', 'trap') == 'trap' and r.get('driver_form', 'current') == 'current' and r['temperature_C'] == 27
        assert r['lights_pA'] == [0, 240] * 32
        if index == 0:
            assert not r['completed'] and r['transient']['timed_out'] and r['phase'] == 'full'
        else:
            assert r['completed'] and r['phase'] == 'capture' and r['diagnostic_only'] and not r['electrical_accuracy_qualified']
            assert not r['references_requested']
            expected_meta = old_meta if index == 3 else meta
            assert r['layout_gds_sha256'] == expected_meta['gds_sha256']
            assert sha(directory / 'tile.spice') == expected_meta['hashes']['rc-port.spice']
        assert sha(directory / 'tile.spice') == r['model_sha256']
        physical = old_meta if index in [0, 3] else meta
        assert r['model_sha256'] == physical['hashes']['rc-port.spice']
        assert r['layout_gds_sha256'] == physical['gds_sha256']
        ex = json.loads((directory / 'transient/execution.json').read_text())
        assert ex == r['transient'] and not ex['errors']
        assert sha(directory / 'transient/test.spice') == ex['deck_sha256']
        deck = (directory / 'transient/test.spice').read_text()
        assert '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2' in deck
        assert 'Bdrive_ROW0 ROW0 0 I=(V(ROW0)-V(CTL_ROW0)*V(VDD))/100' in deck
        assert 'Bcapture SC 0 I=(V(SC)-V(CTL_SC)*V(VDD))/100' in deck
        # Re-extraction renumbers ground terminals. Prove that each source is
        # across its corresponding physical diode before comparing stimuli.
        diodes = [line.split() for line in (directory / 'tile.spice').read_text().splitlines() if line.startswith('D')]
        assert len(diodes) == 64 and len(re.findall(r'(?m)^Ilight\d+ ', deck)) == 64
        for c in range(64):
            role = physical['pixel_roles'][str(c)]
            diode, = [d for d in diodes if d[1:3] == [role['anode'], role['sense']]]
            assert diode[3] == 'diode_nd2ps_03v3'
            def node(name):
                return '0' if name == 'GND' else name if name in physical['ports'] else 'xtile.' + name
            line = f'Ilight{c} {node(role["sense"])} {node(role["anode"])} {r["lights_pA"][c]:g}p\n'
            assert deck.count(line) == 1
            deck = deck.replace(line, f'Ilight{c} PIXEL_SENSE{c} PIXEL_ANODE{c} {r["lights_pA"][c]:g}p\n')
        decks.append(re.sub(r'(?m)^\.tran .*\n|^\.save .*\n', '',
                            re.sub(r'(?m)^\.include .*/tile.spice$', '.include TILE', deck)))
        ix, data = reader.trace(directory / 'transient/stream.raw')
        assert np.isfinite(data).all() and np.all(np.diff(data[:, 0]) > 0)
        assert abs(data[0, 0]) < 1e-15 and data[-1, 0] >= .001405 - 1e-12
        assert len(data) == ex['points'] and np.max(np.diff(data[:, 0])) <= r['step_ns'] * 1.001e-9
        if index > 0:
            assert ex['completed'] and ex['returncode'] == 0 and not ex['timed_out']
            assert abs(data[-1, 0] - .001405) < 1e-12
        traces.append((ix, data, bank.trace_sampler(ix, data)))
        reports.append(r)
    assert all(deck == decks[0] for deck in decks), 'Controls differ beyond timestep/stop, probes, tile path and verified diode terminal names'
    assert [r['step_ns'] for r in reports] == [200, 200, 100, 200]

    def event_delta(first, second):
        differences = []
        for name in traces[first][0].keys() & traces[second][0].keys():
            if name == 'time':
                continue
            assert name.startswith('v(') and name.endswith(')')
            node = name[2:-1]
            for event, t in events:
                differences.append((abs(traces[first][2](node, t) - traces[second][2](node, t)) * 1e6, node, event))
        value, node, event = max(differences)
        return dict(max_uV=value, node=node, event=event, comparison_limit_uV=10, passes=value < 10)

    refinement = event_delta(1, 2)
    reproduction = event_delta(0, 3)
    plates = [line.split()[1:3] for line in (a.run / 'tile.spice').read_text().splitlines()
              if line.startswith('X') and len(line.split()) > 3 and line.split()[3].startswith('cap_mim_')]
    assert len(plates) == 512
    original_plates = [line.split()[1:3] for line in (a.original_probed / 'tile.spice').read_text().splitlines()
                       if line.startswith('X') and len(line.split()) > 3 and line.split()[3].startswith('cap_mim_')]
    assert len(original_plates) == 512
    columns = []
    for c in range(64):
        entries = []
        for index, (ix, data, at) in enumerate(traces[:2]):
            values = {name: at(f'STORE{c}', t) for name, t in events}
            changes = {name: (values[after] - values[before]) * 1e6 for name, before, after in [
                ('capture_open', 'before_capture_open', 'after_capture_open'),
                ('row_off', 'before_row_off', 'after_row_off'),
                ('pixel_reset', 'before_pixel_reset', 'after_pixel_reset')]}
            entries.append(dict(ground_width_um=2 if index == 0 else 8, store_events_V=values, store_changes_uV=changes))
        local = [plate for plate in plates if re.fullmatch(f'STORE{c}(?:[.].*)?', plate[0])]
        assert len(local) == 8 and all(n.startswith('GND.') for _, n in local)
        at = traces[1][2]
        probe = {}
        for name, t in events:
            upper, lower = [sum(at('xtile.' + plate[i], t) for plate in local) / 8 for i in [0, 1]]
            probe[name] = dict(upper_V=upper, ground_V=lower, differential_V=upper - lower)
        columns.append(dict(column=c, light_pA=reports[1]['lights_pA'][c], comparison=entries,
                            revised_mim_events=probe,
                            revised_row_off_mim_change_uV={n: (probe['after_row_off'][n] - probe['before_row_off'][n]) * 1e6
                                                          for n in ['upper_V', 'ground_V', 'differential_V']}))
        original_local = [plate for plate in original_plates if re.fullmatch(f'STORE{c}(?:[.].*)?', plate[0])]
        assert len(original_local) == 8 and all(n.startswith('GND.') for _, n in original_local)
        original_probe = {}
        for name, t in events:
            upper, lower = [sum(traces[3][2]('xtile.' + plate[i], t) for plate in original_local) / 8 for i in [0, 1]]
            original_probe[name] = dict(upper_V=upper, ground_V=lower, differential_V=upper - lower)
        columns[-1]['original_mim_events'] = original_probe
        columns[-1]['original_row_off_mim_change_uV'] = {n: (original_probe['after_row_off'][n] - original_probe['before_row_off'][n]) * 1e6
                                                       for n in ['upper_V', 'ground_V', 'differential_V']}
    x0, y0, x1, y1 = map(float, re.findall(r'-?\d+(?:\.\d+)?', meta['bbox_um']))
    size = [x1 - x0, y1 - y0]
    assert size[0] < 2700 and size[1] < 1100
    last = reports[0]['transient']['last_complete_trace_time_s']
    slots, stop = bank.readout_schedule(64)
    sampled = sum(t + 11.999e-6 <= last for _, _, t in slots)
    readout_start = next(p['observed_wall_seconds'] for p in reports[0]['transient']['progress_observations'] if p['simulated_threshold_s'] == .00141)
    estimate = readout_start + (reports[0]['transient']['seconds'] - readout_start) / sampled * len(slots)
    network = json.loads(a.network.read_text())
    for group in [network] + network['cases']:
        for file, digest in group['evidence_hashes'].items():
            assert sha(ROOT / file) == digest
    evidence = {a.prior.resolve(), a.network.resolve(), Path(__file__).resolve(), (a.geometry / 'result.json').resolve()}
    evidence.update(f.resolve() for directory in [a.layout, a.geometry, a.run, a.refined, a.original_probed] for f in directory.rglob('*') if f.is_file())
    evidence.update(ROOT / name for name in original_hashes)
    evidence.update(ROOT / 'scripts' / name for name in ['simulate-compact-bank.py', 'diagnose-capture-transient.py', 'audit-bank-ground-scaling.py', 'render-bank-64-ground8.py'])
    result = dict(scope=__doc__, layout=str(a.layout), geometry_audit=str(a.geometry), capture_run=str(a.run),
                  physical_checks_pass=True, bbox_um=meta['bbox_um'], size_um=size,
                  budget_um=[2700, 1100], budget_margin_um=[2700 - size[0], 1100 - size[1]],
                  gds_sha256=meta['gds_sha256'], columns=columns, capture_completed=True,
                  capture_transient_seconds=reports[1]['transient']['seconds'], capture_step_ns=reports[1]['step_ns'],
                  capture_refinement=refinement, original_prefix_reproduction=reproduction,
                  diagnostic_runs=[dict(run=str(directory), step_ns=r['step_ns'], seconds=r['transient']['seconds']) for directory, r in zip(directories[1:], reports[1:])],
                  ground_network_diagnostic=str(a.network), ground_network_comparisons=network['comparisons'],
                  full_readout_completed=False, full_bank_accuracy_qualified=False,
                  full_run_budget=dict(original_readout_instants_seen=sampled, required_readout_instants=len(slots),
                                       extrapolated_transient_seconds=estimate, suggested_watchdog_seconds=10800,
                                       scope='Rough original-layout phase extrapolation; new routing and concurrency can change runtime. Independent references need additional time.'),
                  limits=['Unfilled development layout; main DRC excludes density/antenna/cup checks',
                          'Nominal 27 C alternating photocurrents; stops after capture/deselect/reset at 1.405 ms',
                          'Original timed-out trace prefix is used only for capture-event diagnosis',
                          'No 64-column sample accuracy or matched references; event voltage shifts are not ADC errors',
                          'One pixel row; full 64x64 assembly must add 63 rows, then qualify exact-chip manufacturing checks'],
                  evidence_hashes={str(f.relative_to(ROOT)): sha(f) for f in sorted(evidence)})
    (ROOT / 'simulations/compact-bank-64-ground8.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(size_um=size, capture_seconds=result['capture_transient_seconds'],
                          worst_original_row_off_store_uV=max(abs(c['comparison'][0]['store_changes_uV']['row_off']) for c in columns),
                          worst_revised_row_off_store_uV=max(abs(c['comparison'][1]['store_changes_uV']['row_off']) for c in columns),
                          full_run_budget=result['full_run_budget']), indent=2))


if __name__ == '__main__':
    main()
