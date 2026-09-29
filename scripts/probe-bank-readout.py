"""Read one selected column twice with the entire physical bank still connected.

This bounded diagnostic is not the complete-bank readout schedule. It uses the
unchanged bank runner/circuit and independently checks one capture reference
and two output references. Other columns remain unselected throughout readout.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def reference_deck(transient_deck, meta, at, t, column, stores):
    """Build the same matched-state reference as simulate-compact-bank.py."""
    lines = transient_deck.splitlines()
    save, = [line for line in lines if line.startswith('.save ')]
    base = lines[:lines.index(save)]
    base = [line for line in base if not line.startswith(('Ilight', 'Vctl_', 'Vacq ', 'Vrst_adc '))]
    def node(name):
        return '0' if name == 'GND' else name if name in meta['ports'] else 'xtile.' + name
    for c in range(meta['columns']):
        role = meta['pixel_roles'][str(c)]
        sense, anode = node(role['sense']), node(role['anode'])
        voltage = at(sense, t) - at(anode, t)
        base.append(f'Bsense{c} {sense} {anode} I=(V({sense},{anode})-({voltage:.17g}))/1')
        if stores:
            base.append(f'Bstore{c} STORE{c} 0 I=(V(STORE{c})-({at(f"STORE{c}", t):.17g}))/1')
    controls = dict(RST0=int(stores), ROW0=int(not stores), SC=int(not stores),
                    **{f'SEL{c}': int(c == column) for c in range(meta['columns'])})
    base.extend(f'Vctl_{name} CTL_{name} 0 {value}' for name, value in controls.items())
    base.extend(['Vacq ACQ 0 3.3', 'Vrst_adc RSTADC 0 0', save, '', '.control', 'set klu',
                 'set num_threads=1', 'set filetype=binary', 'optran 1 1 1 100n 400u 0', 'op', 'write op.raw', 'quit', '.endc', '.end'])
    return '\n'.join(base) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--column', type=int, required=True)
    p.add_argument('--step-ns', type=float, default=100)
    p.add_argument('--temperature', type=float, default=27)
    p.add_argument('--timeout', type=float, default=1800)
    a = p.parse_args()
    assert not a.out.exists()
    meta = json.loads((a.layout / 'verification.json').read_text())
    nc = meta['columns']
    assert 0 <= a.column < nc and nc % 2 == 0
    bank = module('bank', 'simulate-compact-bank.py')
    slots = [('first', a.column, .00141), ('last', a.column, .00267)]
    def schedule(columns):
        assert columns == nc
        return slots, .00270
    bank.readout_schedule = schedule
    sys.argv = ['simulate-compact-bank.py', '--layout', str(a.layout), '--out', str(a.out),
                '--lights-pa', ','.join(map(str, [0, 240] * (nc // 2))), '--temperature', str(a.temperature),
                '--step-ns', str(a.step_ns), '--solver', 'klu', '--timeout', str(a.timeout), '--transient-only']
    try:
        bank.main()
    finally:
        if a.out.exists():
            (a.out / 'probe-runner.py').write_bytes(Path(__file__).read_bytes())
        if (a.out / 'result.json').exists():
            result = json.loads((a.out / 'result.json').read_text())
            result.update(diagnostic_only=True, full_bank_readout_completed=False, electrical_accuracy_qualified=False,
                          diagnostic_scope=__doc__, column_read=a.column)
            (a.out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    assert result['completed'] and len(result['samples']) == 2
    reader = module('reader', 'diagnose-capture-transient.py')
    dc = module('dc', 'report-compact-bank-16.py')
    ix, data = reader.trace(a.out / 'transient/stream.raw')
    at = bank.trace_sampler(ix, data)
    transient_deck = (a.out / 'transient/test.spice').read_text()
    jobs = [('capture', .0014 - 1e-9, False)] + [(s['slot'], s['time_s'], True) for s in result['samples']]
    references = {}
    for name, t, stores in jobs:
        directory = a.out / (name + '-probe-reference')
        directory.mkdir()
        deck = reference_deck(transient_deck, meta, at, t, a.column, stores)
        (directory / 'test.spice').write_text(deck)
        start = time.monotonic()
        expired = False
        with (directory / 'ngspice.log').open('w') as log:
            try:
                process = subprocess.run(['ngspice', '-b', 'test.spice'], cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=a.timeout, env={**os.environ, 'SPICE_USERINIT_DIR': str(a.out.resolve()), 'OMP_NUM_THREADS': '1'})
                code = process.returncode
            except subprocess.TimeoutExpired:
                expired = True
                code = None
        log = (directory / 'ngspice.log').read_text()
        errors = [line for line in log.splitlines() if re.search(r'timestep too small|aborted|^Error|no such command', line, re.I)]
        execution = dict(returncode=code, timed_out=expired, errors=errors, seconds=time.monotonic() - start,
                         deck_sha256=sha(directory / 'test.spice'))
        (directory / 'execution.json').write_text(json.dumps(execution, indent=2) + '\n')
        assert code == 0 and not expired and not errors, name
        values = dc.dc_values(directory / 'op.raw')
        assert abs(values['v(adcin)'] - values['v(hold)']) < 1e-8
        references[name] = dict(execution=execution, values=values)
        print('Matched reference complete: ' + name, flush=True)
    samples = []
    for sample in result['samples']:
        samples.append(dict(column=a.column, scan=sample['slot'], time_s=sample['time_s'], hold_V=sample['values']['HOLD'],
                            total_error_uV=(sample['values']['HOLD'] - references['capture']['values']['v(hold)']) * 1e6,
                            tracking_error_uV=(sample['values']['HOLD'] - references[sample['slot']]['values']['v(hold)']) * 1e6))
    report = dict(scope=__doc__, layout=str(a.layout), run=str(a.out), columns=nc, column_read=a.column,
                  step_ns=a.step_ns, temperature_C=a.temperature, completed=True, full_bank_readout_completed=False,
                  full_bank_accuracy_qualified=False, samples=samples, references=references,
                  selected_capture_readout_pass=all(abs(s['total_error_uV']) < 500 for s in samples),
                  selected_tracking_pass=all(abs(s['tracking_error_uV']) < 500 for s in samples),
                  limits=['Only one column selected twice; all physical bank columns/loads retained',
                          'Readout order differs from the full-bank first/late scans; no full-bank qualification',
                          'Typical process, nominal supply, alternating 0/240 pA, one temperature/timestep'],
                  evidence_hashes={str(f.resolve().relative_to(ROOT)): sha(f) for f in sorted(a.out.rglob('*')) if f.is_file()})
    (a.out / 'probe-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['samples', 'selected_capture_readout_pass', 'selected_tracking_pass']}, indent=2))


if __name__ == '__main__':
    main()
