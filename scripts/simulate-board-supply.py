"""Coupled extracted camera and supply clamps with an explicit board RLC supply.

Values are engineering assumptions for sensitivity testing, not measured PCB or
selected-regulator models. Reuses the qualified three-frame sampler unchanged.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import re
import runpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CASES = {'nominal': ('nominal', .5), 'hot': ('hot', .5), 'hot_stress': ('hot', 5.)}


def run(case, step=.1, timeout=1800):
    condition, resistance = CASES[case]
    module = runpy.run_path(str(ROOT/'scripts/simulate-clamp-frames.py'))
    runner = module['run_case']
    globals_ = runner.__globals__
    original_engine = globals_['ENGINE']['engine']
    board_name = 'board_' + case
    globals_['CONDITIONS'][board_name] = globals_['CONDITIONS'][condition]
    network = (f'Rboard BOARD_SOURCE BOARD_LEAD {resistance:g}\n'
               'Lboard BOARD_LEAD VDD 2n\n'
               'Rdec VDD DECAP_ESR .1\n'
               'Ldec DECAP_ESR DECAP_C 1n\n'
               'Cdec DECAP_C 0 100n\n')

    def engine(res):
        g = original_engine(res)
        original_base, original_control = g['base'], g['control']
        def base(*args, **kwargs):
            circuit, delay = original_base(*args, **kwargs)
            assert len(re.findall(r'(?m)^Vdd VDD 0 ', circuit)) == 1
            circuit = re.sub(r'(?m)^Vdd VDD 0 ', 'Vdd BOARD_SOURCE 0 ', circuit)
            return circuit + network, delay
        def control(folder, analysis, vectors):
            if analysis.startswith('tran '):
                vectors += ' v(BOARD_SOURCE) i(Lboard) i(Ldec) v(xsupply.xvdd.n4) v(xsupply.xvss.n4)'
                analysis = 'save ' + vectors.replace('v(BIAS) v(PREF)', 'v(BIAS_PIN) v(PREF_PIN)') + '\n' + analysis
            return original_control(folder, analysis, vectors)
        g['base'], g['control'] = base, control
        g['fingerprint'] += hashlib.sha256(network.encode()).hexdigest()
        return g

    globals_['ENGINE'] = {'engine': engine}
    label, result = runner(board_name, 1e-12, step, timeout=timeout)
    result['board'] = {'source_R_ohm': resistance, 'source_L_nH': 2,
                       'decoupling_nF': 100, 'decoupling_ESR_ohm': .1,
                       'decoupling_ESL_nH': 1, 'ground': 'ideal common reference'}
    if result['status'] == 'complete':
        wavepath = next((ROOT/'build/clamp-frames'/label/'scan').glob('*/wave.txt'))
        a = np.loadtxt(wavepath, skiprows=1)
        active = a[:, 0] >= .0012
        startup = (a[:, 0] >= .00119) & (a[:, 0] <= .0012)
        v = result['supply_V']
        ideal = json.loads((ROOT/'build/clamp-frames'/f'{condition}_pair_abs1e-12_step0.1us/result.json').read_text())
        differences = [(s['output_V']-ref['output_V'])*1e6
                       for frame, baseline in zip(result['frames'], ideal['frames'])
                       for s, ref in zip(frame['samples'], baseline['samples'])]
        metrics = {'active_rail_min_V': float(a[active, 8].min()),
                   'active_rail_max_V': float(a[active, 8].max()),
                   'active_rail_peak_to_peak_mV': float(np.ptp(a[active, 8])*1e3),
                   'active_max_rail_error_mV': float(np.max(abs(a[active, 8]-v))*1e3),
                   'startup_hold_max_rail_error_pct': float(np.max(abs(a[startup, 8]/v-1))*100),
                   'peak_source_current_mA': float(np.max(-a[:, 4])*1e3),
                   'active_peak_source_current_mA': float(np.max(-a[active, 4])*1e3),
                   'post_startup_max_clamp_gate_V': float(np.max(abs(a[active, 12:14]))),
                   'max_sample_change_vs_ideal_uV': max(abs(x) for x in differences),
                   'sample_changes_vs_ideal_uV': differences}
        # A 1% rail budget is a declared engineering screen, not foundry signoff.
        metrics['rail_screen_pass'] = bool(metrics['active_max_rail_error_mV'] < .01*v*1000
                                           and metrics['startup_hold_max_rail_error_pct'] < 1)
        result['board_metrics'] = metrics
        result['board_screen_pass'] = bool(result['all_frames_pass'] and metrics['rail_screen_pass'])
    else:
        result['board_screen_pass'] = False
    (ROOT/'build/clamp-frames'/label/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(case, result['status'], 'board pass:', result['board_screen_pass'], flush=True)
    return label, result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=[*CASES, 'all'], default='all')
    parser.add_argument('--step-us', type=float, default=.1)
    parser.add_argument('--timeout', type=float, default=1800)
    args = parser.parse_args()
    cases = list(CASES) if args.case == 'all' else [args.case]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda c: run(c, args.step_us, args.timeout), cases))
    results = {p.parent.name: json.loads(p.read_text()) for p in
               (ROOT/'build/clamp-frames').glob('board_*/result.json')}
    (ROOT/'simulations/board-supply.json').write_text(json.dumps({
        'cases': results,
        'scope': 'Three-frame coupled extracted camera and direct foundry supply clamps. '
                 'Assumed passive board supply impedance, ideal upstream ramp and ground. '
                 'Typical MOS; nominal and hot diode conditions. Not a regulator, package, '
                 'full pad-ring extraction, ESD or full PVT qualification.',
        'screens': {'hold_and_tracking_error_mV': .5, 'rail_error_pct': 1,
                    'startup_bias_error_pct': 1, 'frame_repeatability_uV': 50}}, indent=2)+'\n')
    if not all(r.get('board_screen_pass', False) for r in results.values()):
        raise SystemExit('One or more board-supply cases did not pass; see preserved logs/results.')
