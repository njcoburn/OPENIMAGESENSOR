"""Measure completed strip recovery experiments, retaining failures separately.

Run inside the tools container; writes a report beside each completed case.
No numerical, storage, or power result here implies camera signoff.
"""
from pathlib import Path
import argparse, hashlib, json, runpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
read_raw = runpy.run_path(str(ROOT / 'scripts/diagnose-functional-camera.py'))['read_raw']


def analyze(directory, source):
    result = json.loads((directory / 'result.json').read_text())
    assert result['completed'], directory
    meta = json.loads((source / result['case'] / 'extraction.json').read_text())
    model = source / result['case'] / (result['mode'] + '.spice')
    assert hashlib.sha256(model.read_bytes()).hexdigest() == result['model_sha256']
    names, data = read_raw(directory / 'transient/stream.raw')
    assert np.isfinite(data).all()
    ix = {name: i for i, name in enumerate(names)}
    times = data[:, 0]

    def wave(n):
        if n in ['GND', '0']:
            return np.zeros(len(times))
        if n not in meta['ports']:
            n = 'xarray.' + n
        return data[:, ix['v(' + n.lower() + ')']]

    def at(n, t):
        return float(np.interp(t, times, data[:, ix['v(' + n.lower() + ')']]))

    mask = times >= .0012
    vdd = data[:, ix['v(vdd)']]
    metrics = dict(run_directory=str(directory.relative_to(ROOT)),
                   max_local_vdd_loss_V=0., max_sampled_local_vdd_loss_V=0.,
                   max_abs_local_ground_V=0., min_local_supply_V=10.)
    for key, role in meta['roles']['rc'].items():
        local, ground = wave(role['vdd']), wave(role['gnd'])
        loss = vdd-local
        peak = float(loss[mask].max())
        if peak > metrics['max_local_vdd_loss_V']:
            index = np.flatnonzero(mask)[np.argmax(loss[mask])]
            metrics.update(max_local_vdd_loss_V=peak,
                           peak_vdd_loss_time_s=float(times[index]),
                           peak_vdd_loss_pixel=key)
        metrics['max_abs_local_ground_V'] = max(metrics['max_abs_local_ground_V'], float(np.abs(ground[mask]).max()))
        metrics['min_local_supply_V'] = min(metrics['min_local_supply_V'], float((local-ground)[mask].min()))
    for sample in result['samples']:
        role = meta['roles']['rc'][f"{sample['row']}_{sample['column']}"]
        drop = float(np.interp(sample['time_s'], times, vdd-wave(role['vdd'])))
        metrics['max_sampled_local_vdd_loss_V'] = max(metrics['max_sampled_local_vdd_loss_V'], drop)
    metrics['max_source_current_A'] = float((-data[mask, ix['i(vsource)']]).max())
    metrics['mean_source_current_A'] = float(np.trapezoid(-data[mask, ix['i(vsource)']], times[mask]) / np.ptp(times[mask]))
    metrics['same_light_hold_spread_V'] = {
        str(light): float(np.ptp([s['capture']['HOLD'] for i, s in enumerate(result['samples']) if i % 3 == j]))
        for j, light in enumerate([0, 80, 240])}
    metrics['sample_min_sense_V'] = min(s['sense_differential_V'] for s in result['samples'])
    if result.get('column_storage_pF'):
        capture = result['capture_time_s']
        metrics['capture_max_local_vdd_loss_V'] = max(
            float(np.interp(capture-1e-9, times, vdd-wave(role['vdd'])))
            for role in meta['roles']['rc'].values())
        metrics['capture_min_local_supply_V'] = min(
            float(np.interp(capture-1e-9, times, wave(role['vdd'])-wave(role['gnd'])))
            for role in meta['roles']['rc'].values())
        items = []
        for sample in result['samples']:
            c, t = sample['column'], sample['time_s']
            role = meta['roles']['rc'][f'0_{c}']
            before = at(f'STORE{c}', capture - 1e-9)
            after = at(f'STORE{c}', capture + 1e-6)
            read = at(f'STORE{c}', t)
            items.append(dict(column=c, photocurrent_pA=[0,80,240][c%3],
                              capture_sense_V=float(np.interp(capture-1e-9, times, wave(role['sense'])-wave(role['anode']))),
                              capture_column_V=at(f'COL{c}', capture-1e-9),
                              store_before_V=before, store_after_V=after, store_read_V=read,
                              capture_tracking_error_V=before-at(f'COL{c}', capture-1e-9),
                              capture_pedestal_V=after-before,
                              retention_change_V=read-after,
                              hold_V=sample['capture']['HOLD']))
        metrics['storage'] = items
        control_checks = []
        for sample in result['samples']:
            t, c = sample['time_s'], sample['column']
            supply = at('VDD', t)
            checks = {
                'capture_open': at('SC', t) < .1 and at('SCB', t) > supply-.1,
                'selected_column': at(f'SEL{c}', t) > supply-.1,
                'other_columns_off': all(at(f'SEL{other}', t) < .1
                                         for other in range(result['columns']) if other != c),
                'adc_acquiring': at('ACQ', t) > 3.2 and at('RSTADC', t) < .1,
            }
            if result['reset_after_capture']:
                checks['row_off_and_reset'] = at('ROW0', t) < .1 and at('RST0', t) > supply-.1
            control_checks.append(dict(column=c, passed=all(checks.values()), checks=checks))
        metrics['capture_readout_control_checks'] = control_checks
        metrics['all_capture_readout_controls_pass'] = all(x['passed'] for x in control_checks)
        for key in ['capture_tracking_error_V', 'capture_pedestal_V', 'retention_change_V']:
            metrics['max_abs_' + key] = max(abs(s[key]) for s in items)
        metrics['capture_min_sense_V'] = min(s['capture_sense_V'] for s in items)
    (directory / 'recovery-analysis.json').write_text(json.dumps(metrics, indent=2)+'\n')
    print(json.dumps({k:v for k,v in metrics.items() if k not in ['storage', 'capture_readout_control_checks']}), flush=True)
    return metrics


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    p.add_argument('runs', nargs='+')
    args = p.parse_args()
    for run in args.runs:
        for result in sorted(Path(run).glob('r*c*/result.json')):
            if json.loads(result.read_text())['completed']:
                analyze(result.parent.resolve(), Path(args.source).resolve())
