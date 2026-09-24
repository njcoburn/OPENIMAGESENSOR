"""Static transfer references at captured pixel-charge states.

For each sample, freeze the nine photodiode sense voltages to their captured
values with explicit testbench voltage sources, hold the external controls at
that sample's levels, and solve DC with the same chip, supply and output load.
These sources represent stored pixel state for a reference calculation only;
they are not a modification proposed for the physical sensor.
"""
from pathlib import Path
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source')
    p.add_argument('name')
    p.add_argument('--samples', nargs='+', default=[f'{r}:{c}' for r in range(3) for c in range(3)])
    p.add_argument('--frames', nargs='+', type=int, default=[1,2,3], choices=[1,2,3])
    p.add_argument('--timeout', type=float, default=120)
    p.add_argument('--reuse', help='Reuse completed DC cases only when deck, model, simulator and init hashes match exactly')
    args = p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.name)
    selections = [tuple(map(int, item.split(':'))) for item in args.samples]
    assert all(len(x) == 2 and all(0 <= v < 3 for v in x) for x in selections)
    assert len(set(selections)) == len(selections)
    simulator = shutil.which('ngspice')
    assert simulator, 'Use a toolchain login shell'
    source = R/'build/shared-circuit'/args.source
    result = json.loads((source/'result.json').read_text())
    assert result['completed'] or result.get('timed_out'), 'Require a completed run or a retained watchdog trace'
    assert len(set(args.frames))==len(args.frames)
    assert result['reset_driver']=='norton' and result['supply']=='original' and result['drivers']=='thevenin' and result['clamps']==list(range(15)), 'Use the verified full camera with equivalent reset source'
    assert result['end_s']>=.00425+(max(args.frames)-1)*.003-1e-12, 'All requested frame windows must be captured'
    read_raw = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
    names, values = read_raw(source/'stream.raw')
    assert np.isfinite(values).all()
    pixel_map_path = R/'simulations/final-chip-pixel-map.json'
    pixel_map = json.loads(pixel_map_path.read_text())
    audit = json.loads((R/'build/filled-electrical-baseline/audit.json').read_text())
    assert pixel_map['source_sha256'] == audit['reference_sha256'] and audit['device_records_match']
    pixels = pixel_map['pixels']
    dest = R/'build/functional-dc-reference'/args.name
    dest.mkdir(parents=True, exist_ok=False)
    model = (source/'model.spice').read_bytes()
    assert hashlib.sha256(model).hexdigest() == result['model_sha256']
    (dest/'model.spice').write_bytes(model)
    base = (source/'test.spice').read_text().split('.save ')[0]
    assert '.tran ' not in base and '.control' not in base
    assert base.count('.include model.spice') == 1
    base = base.replace('.include model.spice', '.include ../model.spice')
    def at(node, sample_time):
        return float(np.interp(sample_time, values[:, 0], values[:, names.index(f'v({node.lower()})')]))
    meta = dict(source=args.source, source_raw_sha256=hashlib.sha256((source/'stream.raw').read_bytes()).hexdigest(),
                source_deck_sha256=result['deck_sha256'], model_sha256=result['model_sha256'],
                pixel_map_sha256=hashlib.sha256(pixel_map_path.read_bytes()).hexdigest(),
                scope=__doc__, timeout_per_sample_s=args.timeout, accepted_full_chip=False, samples=[], requested_frames=args.frames, simulator_sha256=hashlib.sha256(Path(simulator).read_bytes()).hexdigest(), init_sha256=hashlib.sha256((source/'init/.spiceinit').read_bytes()).hexdigest())
    reuse_root=R/'build/functional-dc-reference'/args.reuse if args.reuse else None
    reuse_meta=json.loads((reuse_root/'result.json').read_text()) if reuse_root else None
    reuse_compatible=reuse_meta is not None and all(reuse_meta.get(k)==meta[k] for k in ['model_sha256','simulator_sha256','init_sha256'])
    for frame, row, column in [(f,r,c) for f in args.frames for r,c in selections]:
        sample_time = .002185 + row*.001 + column*18e-6 + (frame-1)*.003
        assert sample_time <= values[-1, 0], 'Requested sample not captured'
        case = dest/f'f{frame}r{row}c{column}'
        case.mkdir()
        lines = []
        controls = {}
        for line in base.splitlines():
            fields = line.split()
            if fields and fields[0].startswith('V') and len(fields) >= 4 and (fields[1].startswith('CTL_') or fields[1] in ['ACQ', 'RSTADC']):
                voltage = at(fields[1], sample_time)
                controls[fields[1]] = voltage
                line = ' '.join(fields[:3]) + f' DC {voltage:.17g}'
            lines.append(line)
        assert len(controls) == 11
        for i in range(3):
            assert abs(controls[f'CTL_ROW{i}']-(i == row)) < 1e-9
            assert abs(controls[f'CTL_SEL{i}']-(i == column)) < 1e-9
            assert abs(controls[f'CTL_RST{i}']) < 1e-9
        assert abs(controls['ACQ']-3.3) < 1e-9 and abs(controls['RSTADC']) < 1e-9
        stored = []
        for pixel in pixels:
            node = pixel['sense']
            voltage = at(node, sample_time)
            name = f'Vstored{pixel["row"]}{pixel["column"]}'
            lines.append(f'{name} {node} GND {voltage:.17g}')
            stored.append(dict(source=name, node=node, voltage_V=voltage))
        vectors = ['v(VDD)', 'v(PAD_BIAS)', 'v(PAD_PREF)', 'v(sensor_3x3_0.OUT)', 'v(PAD_BUF)', 'v(ADCIN)', 'v(HOLD)', 'i(Vsource)']
        vectors += [f'v({x["node"]})' for x in stored] + [f'i({x["source"]})' for x in stored]
        lines += ['.control', 'set klu', 'set num_threads=1', 'set filetype=binary',
                  'set numdgt=17', 'set wr_singlescale', 'set wr_vecnames',
                  'save '+' '.join(vectors), 'op', 'wrdata op.dat '+' '.join(vectors), 'quit', '.endc', '.end']
        deck = '\n'.join(lines)+'\n'
        (case/'test.spice').write_text(deck)
        entry = dict(frame=frame, row=row, column=column, time_s=sample_time, controls=controls, stored_sense_voltages=stored,
                     deck_sha256=hashlib.sha256(deck.encode()).hexdigest(), completed=False)
        start = time.monotonic()
        try:
            prior=reuse_root/case.name if reuse_root else None
            cached=json.loads((prior/'result.json').read_text()) if prior and (prior/'result.json').exists() else None
            if reuse_compatible and cached and cached['completed'] and cached['deck_sha256']==entry['deck_sha256']:
                for name in ['op.dat','ngspice.log']:shutil.copyfile(prior/name,case/name)
                entry['reused_from']=str(prior.relative_to(R));returncode=0
            else:
                with (case/'ngspice.log').open('w') as log:
                    proc = subprocess.run([simulator, '-b', 'test.spice'], cwd=case, stdout=log, stderr=subprocess.STDOUT,
                        timeout=args.timeout, env={**os.environ, 'SPICE_USERINIT_DIR': str(source/'init'), 'OMP_NUM_THREADS': '1'})
                returncode=proc.returncode
            log_text = (case/'ngspice.log').read_text()
            assert returncode == 0 and 'Using KLU as Direct Linear Solver' in log_text
            assert not re.search(r'^Error|aborted|timestep too small', log_text, re.I|re.M)
            output = np.loadtxt(case/'op.dat', skiprows=1, ndmin=2)
            assert output.shape == (1, 1+len(vectors)) and np.isfinite(output).all()
            dc = dict(zip(vectors, output[0, 1:].tolist()))
            assert max(abs(dc[f'v({x["node"]})']-x['voltage_V']) for x in stored) < 1e-10
            held = at('HOLD', sample_time)
            adc = at('ADCIN', sample_time)
            entry.update(completed=True, dc=dc, transient_hold_V=held, transient_adc_V=adc,
                         hold_minus_dc_mV=1000*(held-dc['v(HOLD)']), adc_minus_dc_mV=1000*(adc-dc['v(ADCIN)']))
        except Exception as exc:
            entry['error'] = repr(exc)
        entry['seconds'] = time.monotonic()-start
        (case/'result.json').write_text(json.dumps(entry, indent=2)+'\n')
        meta['samples'].append(entry)
        (dest/'result.json').write_text(json.dumps(meta, indent=2)+'\n')
        print(json.dumps({k: entry[k] for k in ['frame', 'row', 'column', 'completed', 'seconds', 'hold_minus_dc_mV', 'error', 'reused_from'] if k in entry}), flush=True)
        if not entry['completed']:
            break
    meta['completed'] = len(meta['samples']) == len(selections)*len(args.frames) and all(x['completed'] for x in meta['samples'])
    (dest/'result.json').write_text(json.dumps(meta, indent=2)+'\n')


if __name__ == '__main__':
    main()
