"""Bounded, streaming diagnostics derived from an archived functional deck.

Raw binary output retains completed records even if the watchdog stops ngspice.
No run produced here is a qualification pass.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import shutil
import time
import numpy as np

R = Path(__file__).resolve().parents[1]


def read_raw(path):
    data = path.read_bytes()
    header, body = data.split(b'Binary:\n', 1)
    header = header.decode()
    assert 'Flags: real' in header
    names = [line.split()[1] for line in header.split('Variables:\n', 1)[1].splitlines() if line.strip()]
    assert len(names) == int(re.search(r'No. Variables:\s*(\d+)', header)[1])
    width = len(names) * 8
    # A killed process may leave an incomplete last record and stale point count.
    values = np.frombuffer(body[:len(body)//width*width], dtype=np.float64).reshape(-1, len(names))
    return names, values


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('name')
    p.add_argument('--source', choices=['frame-5000ns', 'frame-5000ns-gear'], default='frame-5000ns')
    p.add_argument('--timeout', type=float, default=1200)
    p.add_argument('--stop-ms', type=float, default=3.24)
    p.add_argument('--internal-capture', action='store_true', help='Save core gates and reset/select MOS drain currents without changing the circuit')
    p.add_argument('--control', choices=['baseline', 'sample-off', 'row-slew-100ns'], default='baseline')
    args = p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.name)
    assert args.timeout > 0 and args.stop_ms > 0
    simulator = shutil.which('ngspice')
    if simulator is None:
        p.error('ngspice is not on PATH; run through scripts/run-tools.sh or a toolchain login shell')
    source = R/'build/functional-camera'/args.source
    dest = R/'build/functional-camera-diagnostic'/args.name
    dest.mkdir(parents=True, exist_ok=False)
    original = (source/'test.spice').read_text()
    circuit = original.split('.control')[0]
    modifications = []
    if args.control == 'sample-off':
        circuit, count = re.subn(r'^Bsample .*$', 'Bsample ADCIN HOLD I=V(ADCIN,HOLD)*1e-12', circuit, flags=re.M)
        assert count == 1
        modifications.append('Sampling conductance held at original off-state 1e-12 S; reset switch unchanged. Diagnostic isolation only.')
    elif args.control == 'row-slew-100ns':
        circuit, count = re.subn(r'^(Vs[012] .*?)10n 10n', r'\g<1>100n 100n', circuit, flags=re.M)
        assert count == 3
        modifications.append('Row-source rise/fall times 10 ns -> 100 ns; finite driver-slew sensitivity control, not an accepted timing change.')
    vectors = re.search(r'^save (.*)$', original, re.M)[1].split()
    vectors += [f'v({prefix}{kind}{i})' for prefix in ['CTL_', 'PAD_'] for kind in ['ROW', 'SEL', 'RST'] for i in range(3)]
    vectors += ['v(ACQ)', 'v(RSTADC)', '@bsample[i]', '@bsample_reset[i]', 'i(Lbond)']
    if args.internal_capture:
        model = (source/'model.spice').read_text()
        devices = []
        for line in model.splitlines():
            fields = line.split()
            if (len(fields) >= 6 and fields[0].startswith('X')
                    and fields[5] == 'nfet_03v3'
                    and re.fullmatch(r'sensor_3x3_0\.(RST|ROW|SEL)[012]', fields[2])):
                devices.append(fields[0])
                vectors += [f'v({node})' for node in fields[1:5]]
                vectors.append(f'@m.{fields[0].lower()}.m0[id]')
        assert len(devices) == 21, f'Expected 9 reset, 9 row and 3 column switches: {devices}'
        vectors += [f'@bdrive_{kind}{i}[i]' for kind in ['rst', 'row', 'sel'] for i in range(3)]
    vectors = list(dict.fromkeys(vectors))
    deck = circuit + '.save ' + ' '.join(vectors) + f'\n.tran 5000n {args.stop_ms/1000:.12g} 0 5000n\n.control\nset klu\nset num_threads=1\nset filetype=binary\nrun stream.raw\nquit\n.endc\n.end\n'
    (dest/'test.spice').write_text(deck)
    (dest/'model.spice').write_bytes((source/'model.spice').read_bytes())
    init = dest/'init'
    init.mkdir()
    (init/'.spiceinit').write_text((R/'checkpoints/clamp-review/package/init/.spiceinit').read_text())
    meta = dict(source=args.source, control=args.control, modifications=modifications,
                internal_capture=args.internal_capture, saved_vectors=vectors,
                timeout_s=args.timeout, target_s=args.stop_ms/1000,
                source_deck_sha256=hashlib.sha256(original.encode()).hexdigest(),
                deck_sha256=hashlib.sha256(deck.encode()).hexdigest(),
                model_sha256=hashlib.sha256((dest/'model.spice').read_bytes()).hexdigest(),
                completed=False, accepted_full_chip=False,
                scope='Diagnostic with bias-frozen MOS capacitance; original history from t=0; no qualification claim.')
    (dest/'run.json').write_text(json.dumps(meta, indent=2)+'\n')
    start = time.monotonic()
    timed_out = False
    with (dest/'ngspice.log').open('w') as log:
        proc = subprocess.Popen([simulator, '-b', 'test.spice'], cwd=dest,
                                stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, 'SPICE_USERINIT_DIR': str(init), 'OMP_NUM_THREADS': '1'})
        try:
            proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    meta.update(seconds=time.monotonic()-start, timed_out=timed_out, returncode=proc.returncode)
    try:
        names, values = read_raw(dest/'stream.raw')
        assert len(values) and np.isfinite(values).all() and np.all(np.diff(values[:, 0]) >= 0)
        np.savez_compressed(dest/'waveforms.npz', names=names, values=values)
        meta.update(points=len(values), end_s=float(values[-1, 0]),
                    ranges={n: dict(min=float(values[:, i].min()), max=float(values[:, i].max()), last=float(values[-1, i])) for i, n in enumerate(names)},
                    last_timestep_s=float(values[-1, 0]-values[-2, 0]))
        log_text = (dest/'ngspice.log').read_text()
        meta['solver'] = 'KLU' if 'Using KLU as Direct Linear Solver' in log_text else 'unexpected'
        meta['completed'] = bool(meta['solver'] == 'KLU' and not timed_out and proc.returncode == 0 and values[-1, 0] >= meta['target_s']-1e-12 and not re.search(r'aborted|timestep too small|^Error', log_text, re.I|re.M))
    except Exception as exc:
        meta['capture_error'] = repr(exc)
    (dest/'result.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(json.dumps({k: v for k, v in meta.items() if k != 'ranges'}), flush=True)


if __name__ == '__main__':
    main()
