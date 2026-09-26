"""Bounded row-enable diagnostics derived from the accepted capture fixture.

Run in the tools container. Preserve time-zero integration and every stimulus;
only stop time, disconnected timestep fixture, and explicitly selected extracted
power resistors/model change. This does not qualify capture/readout accuracy.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/array-strip-capture40-klu-27-100-20260924/r1c64-rc-port'
EXTRACT = ROOT / 'build/array-strip-power2um-20260924/r1c64'
EDGE = .0012

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def raw(path, allow_partial=False):
    with path.open('rb') as f:
        lines = []
        while True:
            line = f.readline()
            if line == b'Binary:\n':
                break
            assert line, 'Missing binary header'
            lines.append(line)
        offset = f.tell()
    header = b''.join(lines).decode()
    assert 'Flags: real' in header
    names = [line.split()[1] for line in header.split('Variables:\n', 1)[1].splitlines() if line.strip()]
    size = path.stat().st_size - offset
    assert allow_partial or size % (8 * len(names)) == 0, 'Incomplete binary record'
    data = np.memmap(path, dtype=np.float64, mode='r', offset=offset,
                     shape=(size // (8 * len(names)), len(names)))
    return {name.lower(): i for i, name in enumerate(names)}, data

def analyze(path, meta, stop, edge_step_ns):
    ix, data = raw(path)
    t = data[:, 0]
    assert t[-1] >= stop - 1e-12 and np.all(np.diff(t) > 0)
    for start in range(0, len(t), 10000):
        assert np.isfinite(data[start:start + 10000]).all()
    def wave(n):
        if n == 'GND':
            return np.zeros(len(t))
        n = n if n in meta['ports'] else 'xarray.' + n
        return data[:, ix[f'v({n.lower()})']]
    vdd = wave('VDD')
    window = (t >= EDGE) & (t <= EDGE + 20e-6)
    indices = np.flatnonzero(window)
    pixels = {}
    for key, roles in meta['roles']['rc'].items():
        loss = vdd - wave(roles['vdd'])
        rail = wave(roles['vdd']) - wave(roles['gnd'])
        peak = indices[np.argmax(loss[window])]
        crossings = {}
        for threshold in [.1, .2, .3]:
            falling = np.flatnonzero((loss[:-1] >= threshold) & (loss[1:] < threshold)
                                    & (t[:-1] >= t[peak]) & (t[1:] <= EDGE + 20e-6))
            j = int(falling[0]) if len(falling) else None
            crossings[str(threshold)] = (float((t[j] + (threshold-loss[j]) *
                (t[j+1]-t[j])/(loss[j+1]-loss[j]) - EDGE)*1e6) if j is not None else None)
        pixels[key] = {'peak_vdd_loss_V': float(loss[peak]),
            'peak_offset_us': float((t[peak]-EDGE)*1e6),
            'minimum_local_rail_V': float(np.min(rail[window])),
            'loss_at_offset_us_V': {str(us): float(np.interp(EDGE+us*1e-6,t,loss))
                                   for us in [0, .01, .05, .1, .5, 1, 5, 10, 20]},
            'falling_threshold_crossing_us': crossings}
    fine = (t[:-1] >= EDGE-10e-9) & (t[1:] <= EDGE+2e-6)
    maxstep = float(np.max(np.diff(t)[fine]))
    if edge_step_ns:
        assert maxstep <= edge_step_ns*1e-9*1.001, (maxstep, edge_step_ns)
    worst = max(pixels, key=lambda k: pixels[k]['peak_vdd_loss_V'])
    return {'points': len(t), 'stop_s': float(t[-1]), 'edge_window_max_step_s': maxstep,
            'worst_pixel': worst, 'worst': pixels[worst], 'pixels': pixels,
            'scope': 'Row-enable transient only; no capture/readout accuracy qualification.'}

def scaled_model(source, factor):
    lines = source.read_text().splitlines(keepends=True)
    parent = {}
    def find(n):
        parent.setdefault(n, n)
        if parent[n] != n:
            parent[n] = find(parent[n])
        return parent[n]
    resistors = [line.split() for line in lines if line.startswith('R')]
    for fields in resistors:
        parent[find(fields[1])] = find(fields[2])
    power = {find('VDD'): 'VDD', find('GND'): 'GND'}
    assert len(power) == 2
    changed = []
    result = []
    for line in lines:
        fields = line.split()
        if line.startswith('R') and find(fields[1]) in power and factor != 1:
            assert len(fields) == 4
            before = float(fields[3])
            fields[3] = format(before*factor, '.17g')
            changed.append({'name': fields[0], 'net': power[find(fields[1])],
                            'old_ohm': before, 'new_ohm': before*factor})
            line = ' '.join(fields) + '\n'
        result.append(line)
    assert sum(a != b for a, b in zip(lines, result)) == len(changed)
    return ''.join(result), changed

def run_case(out, name, factor, step_ns, extraction, timeout, stop, method, temperature, model_name, solver):
    d = out / name
    d.mkdir()
    meta = json.loads((extraction/'extraction.json').read_text())
    assert meta['rows'] == 1 and meta['columns'] == 64
    shutil.copyfile(extraction/'extraction.json', d/'extraction.json')
    model_path = extraction/(model_name+'.spice')
    model, changes = scaled_model(model_path, factor)
    (d/'array.spice').write_text(model)
    shutil.copyfile(BASE/'buffer.spice', d/'buffer.spice')
    deck = (BASE/'transient/test.spice').read_text().replace(str(BASE), str(d))
    # Regenerate the only hierarchical stimuli and observations using new roles.
    def node(n):
        return '0' if n == 'GND' else n if n in meta['ports'] else 'xarray.'+n
    rows = []
    for line in deck.splitlines():
        if line.startswith('Ilight_'):
            key = line.split()[0].removeprefix('Ilight_')
            role = meta['roles']['rc'][key]
            line = f'Ilight_{key} {node(role["sense"])} {node(role["anode"])} {line.split()[-1]}'
        elif line.startswith('.save '):
            saves = [n for n in line.split()[1:] if 'xarray.' not in n]
            saves += [f'v({node(n)})'.lower() for role in meta['roles']['rc'].values()
                      for n in role.values() if node(n) != '0']
            line = '.save ' + ' '.join(dict.fromkeys(saves))
        elif line.startswith('.tran '):
            line = f'.tran 100n {stop:.12g} 0 100n'
        elif line.startswith('.options '):
            assert 'method=trap' in line
            line = line.replace('method=trap', 'method='+method)
        elif line.startswith('.temp '):
            line = f'.temp {temperature:g}'
        elif line == 'set klu':
            line = 'set klu' if solver == 'klu' else 'unset klu'
        else:
            assert 'xarray.' not in line.lower(), line
        rows.append(line)
    if step_ns:
        # Disconnected source supplies breakpoints; no chip terminal sees it.
        # Verify actual accepted spacing from the output, not just the request.
        count = round(2010/step_ns)
        pts = [(0., 0.)] + [(EDGE-10e-9+i*step_ns*1e-9, float(i%2))
                            for i in range(count+1)]
        timing = ['Vdiagnostic_steps DIAGNOSTIC_STEPS 0 PWL(']
        timing += [f'+ {t:.15g} {v:g}' for t,v in pts]
        timing[-1] += ')'
        rows[1:1] = timing
    deck = '\n'.join(rows)+'\n'
    (d/'test.spice').write_text(deck)
    manifest = {'name': name, 'resistance_factor': factor, 'edge_step_ns': step_ns,
                'method': method, 'temperature_C': temperature, 'solver': solver, 'model_name': model_name,
                'source_extraction': str(extraction), 'source_model_sha256': sha(model_path),
                'baseline_deck_sha256': sha(BASE/'transient/test.spice'),
                'deck_sha256': sha(d/'test.spice'), 'model_sha256': sha(d/'array.spice'),
                'changed_resistors': changes, 'completed': False,
                'simulator_sha256': sha(Path(shutil.which('ngspice'))),
                'stop_requested_s': stop}
    (d/'result.json').write_text(json.dumps(manifest, indent=2)+'\n')
    start = time.monotonic()
    with (d/'ngspice.log').open('w') as log:
        p = subprocess.Popen(['ngspice','-b','test.spice'], cwd=d, stdout=log,
                             stderr=subprocess.STDOUT, env={**os.environ,
                             'SPICE_USERINIT_DIR':str(out/'init'),'OMP_NUM_THREADS':'1'})
        try:
            p.wait(timeout=timeout)
            timedout = False
        except subprocess.TimeoutExpired:
            p.terminate()
            p.wait(timeout=10)
            timedout = True
    log = (d/'ngspice.log').read_text()
    errors = [line for line in log.splitlines() if re.search('timestep too small|aborted|^Error',line,re.I)]
    manifest.update(seconds=time.monotonic()-start, returncode=p.returncode,
                    timed_out=timedout, errors=errors)
    if p.returncode == 0 and not timedout and not errors:
        try:
            manifest['analysis'] = analyze(d/'stream.raw', meta, stop, step_ns)
            manifest['completed'] = True
        except Exception as e:
            manifest['analysis_error'] = repr(e)
    (d/'result.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['name','completed','seconds']}),flush=True)
    return manifest

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    p.add_argument('--extraction', type=Path, default=EXTRACT)
    p.add_argument('--timeout', type=float, default=1200)
    p.add_argument('--stop-ms', type=float, default=1.22)
    p.add_argument('--cases', nargs='+', default=['baseline:1:1','refined:1:0.5','low-power-r:0.1:1'])
    p.add_argument('--workers', type=int, default=3)
    p.add_argument('--method', choices=['trap','gear'], default='trap')
    p.add_argument('--temperature', type=float, default=27)
    p.add_argument('--model-name', default='rc-port')
    p.add_argument('--solver', choices=['klu','sparse'], default='klu')
    a = p.parse_args()
    out = Path(a.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/'runner.py')
    (out/'init').mkdir()
    (out/'init/.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    cases = [c.split(':') for c in a.cases]
    assert len({c[0] for c in cases}) == len(cases)
    assert all(float(c[1]) > 0 and float(c[2]) >= 0 for c in cases)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = [pool.submit(run_case,out,n,float(f),float(s),a.extraction.resolve(),
                               a.timeout,a.stop_ms*1e-3,a.method,a.temperature,a.model_name,a.solver) for n,f,s in cases]
        results = [f.result() for f in futures]
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    assert all(r['completed'] for r in results), 'One or more diagnostic cases failed'

if __name__ == '__main__':
    main()
