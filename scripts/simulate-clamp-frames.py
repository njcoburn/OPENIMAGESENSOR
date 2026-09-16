"""Three-frame verification of the extracted sensor with supply-pad clamps.

Keep model geometry, timing, circuit loads, and the original reference evidence.
Explicit numerical settings and per-frame metrics make convergence reviewable.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import os
import re
import runpy
import subprocess
import shutil
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
os.environ['SPICE_USERINIT_DIR'] = str(ROOT/'checkpoints/pad-closure/ngspice-init')
ENGINE = runpy.run_path(str(ROOT/'scripts/simulate-pad-layout.py'))
MODEL = ROOT/'checkpoints/pad-closure/supply-pad-models.spice'
PAIR = ROOT/'circuits/sensor-supply-pads.spice'
CONDITIONS = {'nominal': (27, 3.3, 'diode_typical'), 'hot': (125, 3.0, 'diode_ff')}


def run_case(condition, abstol, step, clamped=True, timeout=1200, adapter=False, monitor=False, reltol=None):
    temp, supply, diode = CONDITIONS[condition]
    label = f'{"adapter_" if adapter else ""}{condition}_{"pair" if clamped else "control"}_abs{abstol:g}_step{step:g}us'
    label += '_monitor' if monitor else ''
    label += f'_rel{reltol:g}' if reltol is not None else ''
    out = ROOT/'build/clamp-frames'/label
    g = ENGINE['engine']('res_ss')
    original_base = g['base']
    g['out'] = out
    fingerprint = g['fingerprint'] + hashlib.sha256(MODEL.read_bytes()+PAIR.read_bytes()).hexdigest()
    durations = json.loads((out/'result.json').read_text()).get('runtime_s', {}) if (out/'result.json').exists() else {}

    def base(*args, **kwargs):
        circuit, delay = original_base(*args, **kwargs)
        circuit = circuit.replace('abstol=1e-14', f'abstol={abstol:g}')
        if clamped:
            circuit += f'.include {MODEL}\n.include {PAIR}\n'
            if adapter:
                # Exact one-port reformulation: Vout=Vin and Iin=Iout.
                # The controlled sources exchange equal/opposite power.
                circuit += 'Eclamp CLAMPDRIVE 0 VDD 0 1\nVclamp CLAMPDRIVE CLAMPRAIL 0\nFclamp VDD 0 Vclamp 1\nXsupply CLAMPRAIL 0 sensor_supply_pads\n'
            else:
                circuit += 'Xsupply VDD 0 sensor_supply_pads\n'
        return circuit, delay

    def ng(folder, circuit):
        folder.mkdir(parents=True, exist_ok=True)
        # Preserve the physical-pad engine's external resistor-pin measurements.
        circuit = circuit.replace('v(BIAS) v(PREF) v(VDD)', 'v(BIAS_PIN) v(PREF_PIN) v(VDD)')
        if reltol is not None:
            circuit = re.sub(r'reltol=\S+', f'reltol={reltol:g}', circuit)
        if step < .1 and not monitor and 'tran ' in circuit:
            vectors = re.search(r'(?m)^wrdata \S+ (.+)$', circuit)[1]
            circuit = re.sub(r'(?m)^(tran .+)$', lambda m: 'save '+vectors+'\n'+m[0], circuit)
        circuit = circuit.replace('\nquit\n', '\nrusage\nquit\n')
        if monitor and adapter and clamped and 'tran ' in circuit:
            extra = ' v(CLAMPRAIL) i(Vclamp) i(Eclamp) v(xsupply.xvdd.n4) v(xsupply.xvss.n4)'
            circuit = re.sub(r'(?m)^(wrdata .* v\(VDD\))$', lambda m: m[0]+extra, circuit)
            vectors = re.search(r'(?m)^wrdata \S+ (.+)$', circuit)[1]
            circuit = re.sub(r'(?m)^(tran .+)$', lambda m: 'save '+vectors+'\n'+m[0], circuit)
            circuit = circuit.replace('\nrusage\n', '\nrusage all\n')
        digest = hashlib.sha256((circuit+fingerprint).encode()).hexdigest()
        stamp = folder/'success.sha256'
        if stamp.exists() and stamp.read_text() == digest:
            return np.loadtxt(folder/'wave.txt', skiprows=1, ndmin=2)
        (folder/'testbench.spice').write_text(circuit)
        # Reuse a completed diagnostic only when its complete deck matches,
        # apart from output paths. Failed or partial runs never seed this cache.
        diagnostic = ROOT/'build/clamp-diagnostic'/('adapter' if adapter else ('abstol12' if abstol == 1e-12 else 'abstol5e13'))
        if condition == 'hot' and clamped and step == .1 and ((adapter and abstol == 1e-14) or (not adapter and abstol in [1e-12, 5e-13])) and folder.name != 'dc' and (diagnostic/'result.json').exists():
            prior = json.loads((diagnostic/'result.json').read_text())
            old = (diagnostic/'testbench.spice').read_text().replace(str(diagnostic), '__OUTPUT__')
            current = circuit.replace(str(folder), '__OUTPUT__')
            if prior['status'] == 'complete' and old == current:
                for filename in ['wave.txt', 'run.log']:
                    shutil.copy2(diagnostic/filename, folder/filename)
                (folder/'reuse.json').write_text(json.dumps({'source': str(diagnostic.relative_to(ROOT)), 'deck_equivalence': 'exact except output path', 'wave_sha256': hashlib.sha256((folder/'wave.txt').read_bytes()).hexdigest()}, indent=2)+'\n')
                durations[str(folder.relative_to(out))] = prior['wall_s']
                stamp.write_text(digest)
                return np.loadtxt(folder/'wave.txt', skiprows=1, ndmin=2)
        start = time.monotonic()
        with (folder/'run.log').open('w') as log:
            proc = subprocess.run(['ngspice', '-b', str(folder/'testbench.spice')], stdout=log,
                                  stderr=subprocess.STDOUT, timeout=timeout)
        durations[str(folder.relative_to(out))] = time.monotonic()-start
        log = (folder/'run.log').read_text()
        if proc.returncode or re.search(r'aborted|timestep too small|^Error', log, re.I|re.M):
            raise RuntimeError(f'Simulation failed: {folder}/run.log')
        data = np.loadtxt(folder/'wave.txt', skiprows=1, ndmin=2)
        assert np.isfinite(data).all()
        stamp.write_text(digest)
        return data

    g['base'] = base
    g['ng'] = ng
    name, result = g['scan']('typical', temp, supply, diode, ramp_us=1000, cext=1, step=step)
    result.update(label=label, clamped=clamped, adapter=adapter, monitor=monitor, reltol=reltol if reltol is not None else (1e-5 if step < .1 else 5e-5), abstol_A=abstol, runtime_s=durations)
    if result['status'] == 'complete':
        directory = out/'scan'/name
        wave = np.loadtxt(directory/'wave.txt', skiprows=1)
        dc = np.loadtxt(directory/'dc/wave.txt', skiprows=1)
        assert wave[-1, 0] >= .01025-1e-12
        frames = []
        for frame in range(3):
            samples = []
            for row in range(3):
                for col in range(3):
                    sample_time = .0012 + .000975 + .003*frame + .001*row + 18e-6*col + 10e-6
                    at = lambda column: float(np.interp(sample_time, wave[:, 0], wave[:, column]))
                    assert dc[0, 0] <= at(1) <= dc[-1, 0]
                    expected = float(np.interp(at(1), dc[:, 0], dc[:, 1]))
                    samples.append({'row': row, 'col': col, 'time_s': sample_time,
                                    'input_V': at(1), 'output_V': at(3), 'hold_V': at(5),
                                    'hold_error_mV': 1000*(at(5)-expected),
                                    'tracking_error_mV': 1000*(at(3)-expected)})
            matrix = np.array([s['output_V'] for s in samples]).reshape(3, 3)
            pattern = np.array([[0, 80, 240], [240, 0, 80], [80, 240, 0]])
            ordering = all(np.all(np.diff(matrix[i, np.argsort(pattern[i])]) < 0) for i in range(3))
            frames.append({'samples': samples, 'brightness_order_ok': bool(ordering),
                           'max_hold_error_mV': max(abs(s['hold_error_mV']) for s in samples),
                           'max_tracking_error_mV': max(abs(s['tracking_error_mV']) for s in samples)})
        if monitor:
            rail_error = float(np.max(np.abs(wave[:, 8]-wave[:, 9])))
            current_error = float(np.max(np.abs(wave[:, 10]+wave[:, 11])))
            power_error = float(np.max(np.abs(wave[:, 8]*wave[:, 10]+wave[:, 9]*wave[:, 11])))
            result['interface_checks'] = {'max_rail_difference_V': rail_error,
                'max_rail_difference_with_saved_precision_bound_V': rail_error+1e-8,
                'max_internal_current_balance_error_A': current_error,
                'max_net_interface_power_W': power_error,
                'post_startup_max_clamp_gate_V': float(np.max(np.abs(wave[wave[:, 0]>=.0012, 12:14]))),
                'pass': bool(rail_error+1e-8 < 1e-7 and current_error < 1e-12 and power_error < 1e-12)}
        result['frames'] = frames
        result['all_frames_max_hold_error_mV'] = max(f['max_hold_error_mV'] for f in frames)
        result['all_frames_max_tracking_error_mV'] = max(f['max_tracking_error_mV'] for f in frames)
        result['frame2_to_frame3_max_output_change_uV'] = max(
            abs(a['output_V']-b['output_V'])*1e6
            for a, b in zip(frames[1]['samples'], frames[2]['samples']))
        result['all_frames_pass'] = bool(
            result.get('interface_checks', {'pass': True})['pass']
            and all(f['brightness_order_ok'] for f in frames)
            and result['all_frames_max_hold_error_mV'] < .5
            and result['all_frames_max_tracking_error_mV'] < .5
            and result['startup_reference_relative_error'] < .01
            and result['frame2_to_frame3_max_output_change_uV'] < 50)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    return label, result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--condition', choices=['nominal', 'hot', 'both'], default='both')
    parser.add_argument('--abstol', type=float)
    parser.add_argument('--step-us', type=float, default=.1)
    parser.add_argument('--reltol', type=float)
    parser.add_argument('--monitor', action='store_true')
    parser.add_argument('--adapter', action='store_true')
    parser.add_argument('--control', action='store_true')
    parser.add_argument('--timeout', type=float, default=1200)
    args = parser.parse_args()
    if args.abstol is None:
        args.abstol = 1e-14 if args.adapter else 1e-12
    conditions = list(CONDITIONS) if args.condition == 'both' else [args.condition]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(run_case, c, args.abstol, args.step_us,
                                               not args.control, args.timeout, args.adapter, args.monitor, args.reltol) for c in conditions]):
            label, result = future.result()
            print(label, result['status'], result.get('all_frames_pass'), flush=True)
    # Aggregate separate invocations without discarding earlier results.
    results = {p.parent.name: json.loads(p.read_text()) for p in (ROOT/'build/clamp-frames').glob('*/result.json')}
    (ROOT/'simulations/clamp-frames.json').write_text(json.dumps({'cases': results,
        'scope': 'Three full frames. Original physical circuit, 1ms ramp, 200us reset hold. '
                 'Explicit current tolerance and time-step convergence checks. Ideal rails; HV MOS typical.',
        'screens': {'sampling_error_mV': .5, 'startup_reference_relative_error': .01,
                    'frame2_to_frame3_output_change_uV': 50}}, indent=2)+'\n')
