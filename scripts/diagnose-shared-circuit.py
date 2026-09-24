"""Restore shared camera circuitry and selected supply-clamp domains.

Keeps the original full-chip testbench and time-zero stimuli by default;
optional supply and equivalent-source controls are recorded explicitly.
Semiconductor and
resistor connectivity, excluding global supply/ground rails, partitions the
model into the functional camera, unused pads, and 15 clamp timing domains.
All non-clamp domains remain. Omitted clamp nodes are AC-grounded in incident
linear capacitors; capacitors wholly inside omitted domains are removed.
This is an isolation experiment, not a proposed physical model correction.
"""
from pathlib import Path
from collections import defaultdict
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
helpers = runpy.run_path(str(R/'scripts/diagnose-standalone-row.py'))
pins = helpers['pins']
read_raw = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
sha = lambda b: hashlib.sha256(b).hexdigest()


def partition(lines):
    devices = [line.split() for line in lines if line and line[0] in 'XD']
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def local(f):
        return [x for x in pins(f) if x not in ['VDD', 'GND', '0']]
    for f in devices:
        nodes = local(f)
        for node in nodes[1:]:
            parent[find(node)] = find(nodes[0])
    groups = defaultdict(list)
    for f in devices:
        nodes = local(f)
        groups[find(nodes[0]) if nodes else 'RAILS'].append(f)
    out = {}
    for group in groups.values():
        nodes = sorted({node for f in group for node in local(f)})
        labels = [n for n in nodes if n.startswith('PEX_SAFE_')]
        assert len(labels) <= 1
        label = labels[0] if labels else ('CAMERA' if 'PAD_RST2' in nodes else nodes[0] if nodes else 'RAILS')
        assert label not in out
        out[label] = dict(nodes=nodes, devices=[f[0] for f in group])
    assert len([k for k in out if k.startswith('PEX_SAFE_')]) == 15
    assert len(out['CAMERA']['devices']) == 189
    assert all(len(out[f'PEX_SAFE_{i}']['devices']) == 136 for i in range(15))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('name')
    p.add_argument('--clamps', nargs='*', type=int, choices=range(15), default=[])
    p.add_argument('--all-clamps', action='store_true')
    p.add_argument('--stop-ms', type=float, default=3.28)
    p.add_argument('--timeout', type=float, default=180)
    p.add_argument('--max-step-ns', type=float, default=5000)
    p.add_argument('--supply', choices=['original', 'ideal'], default='original')
    p.add_argument('--drivers', choices=['thevenin', 'norton'], default='thevenin')
    p.add_argument('--reset-driver', choices=['thevenin', 'norton'], default='thevenin')
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--simulator', default='ngspice')
    args = p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.name)
    assert args.stop_ms > 0 and args.timeout > 0 and args.max_step_ns > 0
    simulator = shutil.which(args.simulator)
    assert simulator
    dest = R/'build/shared-circuit'/args.name
    dest.mkdir(parents=True, exist_ok=False)
    original_model = (SOURCE/'model.spice').read_text()
    original_deck = (SOURCE/'test.spice').read_text()
    groups = partition(original_model.splitlines())
    selected = set(range(15)) if args.all_clamps else set(args.clamps)
    omitted_groups = [g for i in range(15) if i not in selected for g in [groups[f'PEX_SAFE_{i}']]]
    omitted_devices = {d for g in omitted_groups for d in g['devices']}
    omitted_nodes = {n for g in omitted_groups for n in g['nodes']}
    lines, cut_caps, dropped_caps = [], [], []
    for line in original_model.splitlines():
        f = line.split()
        if not f or f[0].startswith('*'):
            lines.append(line)
            continue
        if f[0] in omitted_devices:
            continue
        if f[0].startswith('C') and set(f[1:3]) & omitted_nodes:
            new = [f[0]] + ['0' if n in omitted_nodes else n for n in f[1:3]] + f[3:]
            if new[1] == new[2] or set(new[1:3]) <= {'GND', '0'}:
                dropped_caps.append(line)
                continue
            cut_caps.append(dict(original=line, substituted=' '.join(new)))
            line = ' '.join(new)
        lines.append(line)
    model = '\n'.join(lines)+'\n'
    if args.all_clamps:
        assert model == original_model, 'Full restoration must reproduce model byte-for-byte'
    (dest/'model.spice').write_text(model)
    circuit = original_deck.split('.save ')[0]
    assert '.tran ' not in circuit and '.control' not in circuit
    original_circuit = circuit
    if args.supply == 'ideal':
        assert circuit.count('Rsupply RAW VDD 2\n') == 1
        circuit = circuit.replace('Rsupply RAW VDD 2\n', 'Vsupply RAW VDD 0\n')
    if args.drivers == 'norton':
        for kind in ['RST', 'ROW', 'SEL']:
            for i in range(3):
                label = f'{kind}{i}'
                old = f'Bdrive_{label} DRIVE_{label} GND V=V(CTL_{label})*V(VDD,GND)\nRdrive_{label} DRIVE_{label} PAD_{label} 100\n'
                assert circuit.count(old) == 1
                # Identical pad terminal equation and current sign. DRIVE is
                # internal to this source/resistor pair; no other attachments.
                assert circuit.count(f'DRIVE_{label}') == 2
                new = f'Bdrive_{label} PAD_{label} GND I=(V(PAD_{label},GND)-V(CTL_{label})*V(VDD,GND))/100\n'
                circuit = circuit.replace(old, new)
    if args.reset_driver == 'norton':
        old = 'Vresetdrive RESETDRV GND 2\nRresetdrive RESETDRV PAD_VRESET 1\n'
        assert circuit.count(old) == 1 and circuit.count('RESETDRV') == 2
        circuit = circuit.replace(old, 'Bresetdrive PAD_VRESET GND I=(V(PAD_VRESET,GND)-2)/1\n')
    currents = re.findall(r'@\S+\[\w+\]', original_deck.split('.save ')[1].splitlines()[0])
    if args.reset_driver == 'norton':
        currents.append('@bresetdrive[i]')
    deck = circuit + '.save all '+' '.join(currents)+f'\n.tran {args.max_step_ns}n {args.stop_ms/1000:.12g} 0 {args.max_step_ns}n\n.control\nset klu\nset num_threads=1\nset filetype=binary\nrun stream.raw\nquit\n.endc\n.end\n'
    (dest/'test.spice').write_text(deck)
    init = dest/'init'
    init.mkdir()
    shutil.copyfile(SOURCE/'init/.spiceinit', init/'.spiceinit')
    audit = dict(domains=groups, omitted_devices=sorted(omitted_devices), omitted_nodes=sorted(omitted_nodes),
                 cut_caps=cut_caps, dropped_caps=dropped_caps, original_model_sha256=sha(original_model.encode()),
                 source_deck_sha256=sha(original_deck.encode()), model_sha256=sha(model.encode()),
                 original_testbench_sha256=sha(original_circuit.encode()), testbench_sha256=sha(circuit.encode()),
                 supply_control=args.supply, driver_form=args.drivers, reset_driver_form=args.reset_driver)
    (dest/'partition.json').write_text(json.dumps(audit, indent=2)+'\n')
    meta = dict(name=args.name, clamps=sorted(selected), supply=args.supply, drivers=args.drivers, reset_driver=args.reset_driver, retained_device_records=sum(len(g['devices']) for g in groups.values())-len(omitted_devices),
                simulator=simulator, simulator_sha256=sha(Path(simulator).read_bytes()),
                model_sha256=audit['model_sha256'], deck_sha256=sha(deck.encode()), target_s=args.stop_ms/1000,
                max_step_ns=args.max_step_ns, timeout_s=args.timeout, prepare_only=args.prepare_only,
                completed=False, accepted_full_chip=False, scope=__doc__)
    (dest/'run.json').write_text(json.dumps(meta, indent=2)+'\n')
    if args.prepare_only:
        print(json.dumps(meta), flush=True)
        return
    start = time.monotonic()
    with (dest/'ngspice.log').open('w') as log:
        proc = subprocess.Popen([simulator, '-b', 'test.spice'], cwd=dest, stdout=log, stderr=subprocess.STDOUT,
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
    meta.update(seconds=time.monotonic()-start, returncode=proc.returncode)
    log = (dest/'ngspice.log').read_text()
    meta['solver_errors'] = [line for line in log.splitlines() if re.search(r'aborted|timestep too small|^Error', line, re.I)]
    try:
        names, values = read_raw(dest/'stream.raw')
        assert len(values)>1 and np.isfinite(values).all() and np.all(np.diff(values[:, 0]) >= 0)
        meta.update(points=len(values), end_s=float(values[-1, 0]), vectors=len(names),
                    completed=bool(not meta['timed_out'] and proc.returncode == 0 and not meta['solver_errors'] and 'Using KLU as Direct Linear Solver' in log and values[-1, 0]>=meta['target_s']-1e-12))
    except Exception as exc:
        meta['capture_error'] = repr(exc)
    (dest/'result.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(json.dumps(meta), flush=True)


if __name__ == '__main__':
    main()
