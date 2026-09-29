"""Finish five-pattern refinement and screen shunt placement at the worst prior case.

Eight physical 50 ns runs complete the existing five-pattern, two-temperature
refinement pairs. Four inverse-pattern schematic runs add 100/50 ns comparisons
at both temperatures. Twenty transient-only hot inverse runs move the 19 shunt
totals individually and jointly. This is not the full placement/corner matrix.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {'inverse': [240, 0] * 8, 'dark': [0] * 16,
            'middle': [80] * 16, 'bright': [240] * 16}


def jobs(meta):
    cases = []
    for pattern in PATTERNS:
        for temperature in [125, 27]:
            cases.append(dict(name=f'fine-{pattern}-{temperature}', pattern=pattern,
                              temperature_C=temperature, step_ns=50, model='rc-port', references=True))
    for temperature in [125, 27]:
        for step in [100, 50]:
            cases.append(dict(name=f'schematic-inverse-{temperature}-{step}', pattern='inverse',
                              temperature_C=temperature, step_ns=step, model='reference', references=True))
    variants = ['rc-far'] + ['rc-' + v['net'].lower() + '-far' for v in meta['shunt_approximations']]
    for model in variants:
        cases.append(dict(name=f'placement-inverse-125-{model}', pattern='inverse',
                          temperature_C=125, step_ns=100, model=model, references=False))
    assert len(cases) == 32 and len({c['name'] for c in cases}) == 32
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--workers', type=int, choices=range(1, 5), default=4)
    a = p.parse_args()
    meta = json.loads((a.layout / 'verification.json').read_text())
    assert meta['columns'] == 16 and meta['ground_bus_width_um'] == 8
    cases = jobs(meta)
    a.out.mkdir(parents=True, exist_ok=False)
    for name in ['extend-bank-16-screen.py', 'simulate-compact-bank.py',
                 'diagnose-capture-transient.py', 'compact-bank-reuse.py']:
        (a.out / name).write_bytes((ROOT / 'scripts' / name).read_bytes())
    manifest = dict(scope=__doc__, layout=str(a.layout), expected=len(cases),
                    workers=a.workers, planned_cases=cases, runs=[])

    def save():
        temporary = a.out / 'batch.json.tmp'
        temporary.write_text(json.dumps(manifest, indent=2) + '\n')
        temporary.replace(a.out / 'batch.json')

    save()

    def run(case):
        directory = a.out / case['name']
        command = [sys.executable, str(ROOT / 'scripts/simulate-compact-bank.py'),
                   '--layout', str(a.layout), '--out', str(directory),
                   '--lights-pa', ','.join(map(str, PATTERNS[case['pattern']])),
                   '--temperature', str(case['temperature_C']), '--step-ns', str(case['step_ns']),
                   '--model', case['model'], '--solver', 'klu', '--timeout', '1800', '--reference-workers', '2']
        if not case['references']:
            command.append('--transient-only')
        start = time.monotonic()
        expired = False
        print('Starting ' + case['name'], flush=True)
        with (a.out / (case['name'] + '.log')).open('w') as log:
            with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True) as process:
                try:
                    code = process.wait(timeout=3600)
                except subprocess.TimeoutExpired:
                    expired = True
                    os.killpg(process.pid, signal.SIGKILL)
                    code = process.wait()
        result = json.loads((directory / 'result.json').read_text()) if (directory / 'result.json').exists() else {}
        record = dict(case, run=str(directory), seconds=time.monotonic() - start,
                      completed=bool(result.get('completed')) and code == 0,
                      returncode=code, overall_timeout=expired,
                      capture_readout_pass=result.get('capture_readout_pass'), tracking_pass=result.get('tracking_pass'))
        print(json.dumps(record), flush=True)
        return record

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = [pool.submit(run, case) for case in cases]
        for future in as_completed(futures):
            manifest['runs'].append(future.result())
            save()
    if not all(r['completed'] and (not r['references'] or
               (r['capture_readout_pass'] and r['tracking_pass'])) for r in manifest['runs']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
