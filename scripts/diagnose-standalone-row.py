"""Extract and exercise individual rows; isolation diagnostics, not qualification.

Run in the project Docker toolchain. Shared supplies/columns are ideal DC
boundaries at the recorded initial operating point, except the optional finite
supply control restores the original 3.3 V source and 2 ohm supply resistor
(without the other rows, shared buffer or power clamps). Cross-boundary capacitors
retain their capacitance but their remote plates are held at AC ground.
No saved pixel voltage is imposed: each case computes its own DC state and
starts the original reset/light history at t=0. These boundary substitutions
deliberately remove full-chip feedback and do not reproduce its charge history
exactly. Device records, source deck and substitutions are archived per run.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import os
import re
import runpy
import shutil
import subprocess
import time
import numpy as np

R = Path(__file__).resolve().parents[1]
SOURCE = R/'build/functional-camera-diagnostic/reset-edge-internal-20260920'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pins(fields):
    if fields[0].startswith('D'):
        return fields[1:3]
    if fields[4] == 'ppolyf_u':
        return fields[1:4]
    assert fields[5] in ['nfet_03v3', 'pfet_03v3', 'nfet_06v0', 'pfet_06v0'], fields
    return fields[1:5]


def capacitance(value):
    match = re.fullmatch(r'([0-9.eE+-]+)([fpnum]?)', value)
    assert match, value
    return float(match[1])*{'': 1, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3}[match[2]]


def extract(row, records, pixels):
    devices = {f[0]: f for f in records if f[0][0] in 'XD'}
    selected_pixels = [x for x in pixels if x['row'] == row]
    local = {f'PAD_RST{row}', f'PAD_ROW{row}', f'sensor_3x3_0.RST{row}', f'sensor_3x3_0.ROW{row}'}
    boundary = {'VDD', 'GND', '0', 'sensor_3x3_0.VRESET', *[f'sensor_3x3_0.COL{i}' for i in range(3)]}
    canonical = {f'PAD_RST{row}': 'PAD_RST', f'PAD_ROW{row}': 'PAD_ROW',
                 f'sensor_3x3_0.RST{row}': 'RST', f'sensor_3x3_0.ROW{row}': 'ROW'}
    core = set()
    for px in selected_pixels:
        for key in ['reset', 'source_follower', 'row_select', 'photodiode']:
            core.add(px[key])
        sf = devices[px['source_follower']]
        rst = devices[px['reset']]
        sel = devices[px['row_select']]
        diode = devices[px['photodiode']]
        assert rst[1:5] == ['sensor_3x3_0.VRESET', px['reset_gate'], px['sense'], 'GND']
        assert sf[1:3] == ['VDD', px['sense']] and sf[4] == 'GND'
        assert sel[1:5] == [sf[3], px['row_gate'], px['column_node'], 'GND']
        assert diode[1:3] == ['GND', px['sense']]
        local.update([px['sense'], sf[3]])
        canonical[px['sense']] = f'SENSE{px["column"]}'
        canonical[sf[3]] = f'SF{px["column"]}'
    # Semiconductor/resistor connectivity only. Never traverse coupling caps.
    selected = {}
    while True:
        before = len(local)
        for name, f in devices.items():
            if set(pins(f)) & local:
                selected[name] = f
                local.update(set(pins(f))-boundary)
        if len(local) == before:
            break
    assert len(local) == 10 and len(selected) == 34, (row, local, selected)
    canonical_records = sorted(' '.join(canonical.get(x, x) for x in f[1:]) for f in selected.values())
    resistors = {name for name, f in selected.items() if f[0].startswith('X') and f[4] == 'ppolyf_u'}
    caps = [f for f in records if f[0].startswith('C') and set(f[1:3]) & local]
    cut = [f for f in caps if set(f[1:3])-local-boundary]
    return dict(row=row, pixels=selected_pixels, devices=selected, core=core, resistors=resistors,
                local=local, boundary=boundary, canonical=canonical, canonical_records=canonical_records,
                caps=caps, cut=cut)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--rows', nargs='+', type=int, choices=range(3), default=[0, 1, 2])
    parser.add_argument('--stages', nargs='+', choices=['devices', 'caps', 'pads'], default=['devices', 'caps', 'pads'])
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--max-step-ns', type=float, default=5000)
    parser.add_argument('--supply', choices=['ideal', 'finite'], default='ideal')
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.name)
    assert args.timeout > 0 and args.max_step_ns > 0
    simulator = shutil.which('ngspice')
    assert simulator, 'Use the Docker toolchain'
    dest = R/'build/standalone-row'/args.name
    dest.mkdir(parents=True, exist_ok=False)
    model = (SOURCE/'model.spice').read_text()
    original = (SOURCE/'test.spice').read_text()
    records = [line.split() for line in model.splitlines() if line and line[0] in 'XDC']
    pixels = json.loads((R/'simulations/final-chip-pixel-map.json').read_text())['pixels']
    read_raw = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
    names, source_values = read_raw(SOURCE/'stream.raw')
    rows = [extract(row, records, pixels) for row in range(3)]
    audit = dict(source_model_sha256=digest(SOURCE/'model.spice'), source_deck_sha256=digest(SOURCE/'test.spice'),
                 source_raw_sha256=digest(SOURCE/'stream.raw'),
                 rows_identical_devices=all(x['canonical_records'] == rows[0]['canonical_records'] for x in rows), rows=[])
    for row in rows:
        totals = {row['canonical'].get(node, node): sum(capacitance(f[3]) for f in row['caps'] if node in f[1:3])*1e15 for node in sorted(row['local'])}
        audit['rows'].append(dict(row=row['row'], devices=len(row['devices']), incident_caps=len(row['caps']),
            cut_caps=len(row['cut']), total_incident_capacitance_fF=totals, canonical_devices=row['canonical_records']))
    assert audit['rows_identical_devices']
    (dest/'topology-audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    (dest/'source-model.spice').write_text(model)
    (dest/'source-deck.spice').write_text(original)
    results = dict(scope=__doc__, topology_audit='topology-audit.json', cases=[], accepted_full_chip=False)
    for row_index in args.rows:
        row = rows[row_index]
        stop = .00128+row_index*.001
        for stage in args.stages:
            case = dest/f'r{row_index}-{stage}'
            case.mkdir()
            init = case/'init'
            init.mkdir()
            shutil.copyfile(SOURCE/'init/.spiceinit', init/'.spiceinit')
            selected = row['devices'] if stage == 'pads' else {k:v for k,v in row['devices'].items() if k in row['core'] | row['resistors']}
            lines = ['Standalone row isolation; no full-chip qualification']
            lines += [line for line in original.splitlines() if line.startswith(('.lib ', '.temp ', '.options ')) or line.startswith('.include /')]
            lines += [' '.join(f) for f in selected.values()]
            grounded = []
            if stage in ['caps', 'pads']:
                for f in row['caps']:
                    new = f.copy()
                    for i in [1, 2]:
                        if new[i] not in row['local'] | row['boundary']:
                            grounded.append(dict(cap=f[0], remote_node=f[i], capacitance_F=capacitance(f[3])))
                            new[i] = '0'
                    lines.append(' '.join(new))
            boundary_values = {}
            for i, node in enumerate(sorted(row['boundary']-{'GND', '0'})):
                if node == 'VDD' and args.supply == 'finite':
                    lines += ['Vsource RAW 0 3.3', 'Rsupply RAW VDD 2']
                    continue
                value = float(source_values[0, names.index(f'v({node.lower()})')])
                boundary_values[node] = value
                lines.append(f'Vboundary{i} {node} 0 {value:.17g}')
            keep = {f'Vr{row_index}', f'Vs{row_index}'}
            keep |= {f'{prefix}_{kind}{row_index}' for prefix in ['Bdrive', 'Rdrive', 'Rpull'] for kind in ['RST', 'ROW']}
            keep |= {f'Ilight{row_index}{col}' for col in range(3)}
            stimulus = [line for line in original.splitlines() if line.split() and line.split()[0] in keep]
            assert len(stimulus) == 11
            lines += stimulus
            vectors = [f'v({node})' for node in sorted(row['local'] | (row['boundary']-{'GND', '0'}))]
            vectors += [f'@m.{px[key].lower()}.m0[id]' for px in row['pixels'] for key in ['reset', 'source_follower', 'row_select']]
            vectors += [f'@bdrive_{kind}{row_index}[i]' for kind in ['rst', 'row']]
            lines += ['.save '+' '.join(vectors), f'.tran {args.max_step_ns}n {stop:.12g} 0 {args.max_step_ns}n',
                      '.control', 'set klu', 'set num_threads=1', 'set filetype=binary', 'run stream.raw', 'quit', '.endc', '.end']
            (case/'test.spice').write_text('\n'.join(lines)+'\n')
            meta = dict(row=row_index, stage=stage, supply=args.supply, target_s=stop, max_step_ns=args.max_step_ns, timeout_s=args.timeout,
                        boundary_values_V=boundary_values, ac_grounded_remote_plates=grounded, semiconductor_and_resistor_count=len(selected),
                        deck_sha256=digest(case/'test.spice'), completed=False, accepted_full_chip=False)
            (case/'run.json').write_text(json.dumps(meta, indent=2)+'\n')
            started = time.monotonic()
            with (case/'ngspice.log').open('w') as log:
                proc = subprocess.Popen([simulator, '-b', 'test.spice'], cwd=case, stdout=log, stderr=subprocess.STDOUT,
                    env={**os.environ, 'SPICE_USERINIT_DIR': str(init), 'OMP_NUM_THREADS': '1'})
                try:
                    proc.wait(timeout=args.timeout)
                    meta['timed_out'] = False
                except subprocess.TimeoutExpired:
                    meta['timed_out'] = True
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
            meta.update(seconds=time.monotonic()-started, returncode=proc.returncode)
            log = (case/'ngspice.log').read_text()
            meta['solver_errors'] = [x for x in log.splitlines() if re.search(r'aborted|timestep too small|^Error', x, re.I)]
            try:
                n, v = read_raw(case/'stream.raw')
                assert len(v)>1 and np.isfinite(v).all() and np.all(np.diff(v[:, 0]) >= 0)
                assert all(f'i(@m.{px[key].lower()}.m0[id])' in n for px in row['pixels'] for key in ['reset', 'source_follower', 'row_select'])
                meta.update(points=len(v), end_s=float(v[-1, 0]), completed=bool(not meta['timed_out'] and proc.returncode == 0 and not meta['solver_errors'] and v[-1, 0]>=stop-1e-12 and 'Using KLU as Direct Linear Solver' in log))
                edge=.00127002+row_index*.001
                meta['sense_after_reset_V'] = {px['sense']: float(np.interp(edge+1e-6, v[:,0], v[:,n.index('v('+px['sense']+')')])) for px in row['pixels']} if meta['completed'] else None
            except Exception as exc:
                meta['capture_error'] = repr(exc)
            (case/'result.json').write_text(json.dumps(meta, indent=2)+'\n')
            results['cases'].append({k:v for k,v in meta.items() if k != 'ac_grounded_remote_plates'})
            (dest/'result.json').write_text(json.dumps(results, indent=2)+'\n')
            print(json.dumps(results['cases'][-1]), flush=True)


if __name__ == '__main__':
    main()
