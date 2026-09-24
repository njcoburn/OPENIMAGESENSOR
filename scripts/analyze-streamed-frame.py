"""Validate one completed nominal frame and its static transfer references.

Passing these nominal screens is not timestep refinement, repeated-frame,
startup/protection, PVT, wire-R, optical or ADC-specific qualification.
"""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('run')
p.add_argument('--reference', required=True)
a = p.parse_args()
d = R/'build/functional-camera-diagnostic'/a.run
r = json.loads((d/'result.json').read_text())
assert r['completed'] and r['control'] == 'baseline' and r['end_s'] >= .00425-1e-12
report = json.loads((d/'analysis.json').read_text())
assert report['completed'] and report['points'] == r['points']
read_raw = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
names, values = read_raw(d/'stream.raw')
assert np.isfinite(values).all() and np.all(np.diff(values[:, 0]) >= 0)
assert len(values) == r['points'] and values[-1, 0] >= .00425-1e-12
reference_path = R/'build/functional-dc-reference'/a.reference/'result.json'
reference = json.loads(reference_path.read_text())
assert reference['completed'] and reference['source'] == a.run
assert reference['source_raw_sha256'] == hashlib.sha256((d/'stream.raw').read_bytes()).hexdigest()
assert reference['model_sha256'] == r['model_sha256']
assert reference['source_deck_sha256'] == r['deck_sha256']
assert hashlib.sha256((d/'model.spice').read_bytes()).hexdigest() == r['model_sha256']
assert hashlib.sha256((d/'test.spice').read_bytes()).hexdigest() == r['deck_sha256']
assert reference['pixel_map_sha256'] == hashlib.sha256((R/'simulations/final-chip-pixel-map.json').read_bytes()).hexdigest()
ref_samples = {(x['row'], x['column']): x for x in reference['samples']}
assert len(reference['samples']) == len(ref_samples) == 9
assert set(ref_samples) == {(row, col) for row in range(3) for col in range(3)}
samples = report['retained_samples']
assert len(samples) == 9 and len({(x['row'], x['column']) for x in samples}) == 9
pattern = np.array([[0, 80, 240], [240, 0, 80], [80, 240, 0]])
deck = (d/'test.spice').read_text()
pixel_map = json.loads((R/'simulations/final-chip-pixel-map.json').read_text())
for pixel in pixel_map['pixels']:
    row, column = pixel['row'], pixel['column']
    expected = rf'^Ilight{row}{column}\s+{re.escape(pixel["sense"])}\s+GND\s+{pattern[row, column]}p$'
    assert re.search(expected, deck, re.M | re.I), 'Illumination source does not match pixel map and labeled pattern'
measured = np.full((3, 3), np.nan)
bias_errors = []
for sample in samples:
    key = sample['row'], sample['column']
    ref = ref_samples[key]
    assert ref['completed'] and abs(ref['time_s']-sample['time_s']) < 1e-15
    assert abs(ref['transient_hold_V']-sample['hold_V']) < 1e-12
    measured[key] = sample['hold_V']
    sample['dc_hold_V'] = ref['dc']['v(HOLD)']
    sample['hold_minus_dc_mV'] = ref['hold_minus_dc_mV']
    sample['adc_minus_dc_mV'] = ref['adc_minus_dc_mV']
    for node in ['VDD', 'PAD_BIAS', 'PAD_PREF']:
        transient = float(np.interp(sample['time_s'], values[:, 0], values[:, names.index(f'v({node.lower()})')]))
        settled = ref['dc'][f'v({node})']
        assert abs(settled) > .1
        bias_errors.append(dict(row=key[0], column=key[1], node=node,
            transient_V=transient, dc_V=settled, relative_difference=abs(transient-settled)/abs(settled)))
order = all(np.all(np.diff(measured[row, np.argsort(pattern[row])]) < 0) for row in range(3))
cap_error = max(x['max_relative_C_error'] for x in report['cap_range_retained_window'])
assert len(report['cap_range_retained_window']) == 16
max_tracking = max(abs(x['hold_minus_adc_mV']) for x in samples)
max_settling = max(abs(x['hold_minus_dc_mV']) for x in samples)
max_bias = max(x['relative_difference'] for x in bias_errors)
checks = dict(all_nine_samples=True, stimulus_topology=True, brightness_order=bool(order), cap_range=cap_error < 1e-6,
              sample_tracking=max_tracking < .5, dc_reference_settling=max_settling < .5,
              sampled_supply_bias=max_bias < .01)
result = dict(run=a.run, completed=True, accepted_full_chip=False, scope=__doc__,
              nominal_screens_pass=all(checks.values()), checks=checks,
              limits=dict(cap_relative_error=1e-6, tracking_mV=.5, dc_settling_mV=.5, bias_relative=.01),
              max_hold_minus_adc_mV=max_tracking, max_hold_minus_dc_mV=max_settling,
              max_bias_relative_difference=max_bias, max_cap_relative_error=cap_error,
              samples=samples, bias_comparisons=bias_errors,
              reference=a.reference, reference_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest(),
              source_raw_sha256=reference['source_raw_sha256'],
              pending=['Timestep/tolerance refinement (<10 uV sample difference)', 'Three repeated frames',
                       'PVT and realistic loads', 'Startup/protection', 'Distributed wire resistance',
                       'Board and ADC-specific timing', 'Optical and manufacturing qualification'])
(d/'frame-analysis.json').write_text(json.dumps(result, indent=2)+'\n')
fig, axes = plt.subplots(1, 2, figsize=(10, 4.7), layout='constrained')
axes[0].imshow(pattern, cmap='gray', vmin=0, vmax=240)
axes[0].set_title('Assumed light-current pattern')
im = axes[1].imshow(measured, cmap='gray_r', vmin=measured.min(), vmax=measured.max())
axes[1].set_title('Captured held voltages')
for row in range(3):
    for col in range(3):
        axes[0].text(col, row, f'{pattern[row, col]} pA', ha='center', va='center', color='black' if pattern[row, col]>120 else 'white')
        normalized = (measured[row, col]-measured.min())/max(float(np.ptp(measured)), 1e-12)
        axes[1].text(col, row, f'{measured[row, col]:.6f} V', ha='center', va='center', fontsize=9, color='white' if normalized>.5 else 'black')
for ax in axes:
    ax.set(xticks=[0, 1, 2], yticks=[0, 1, 2], xlabel='Column', ylabel='Row')
fig.suptitle('One nominal 3×3 frame — bias-frozen capacitance candidate')
fig.text(.5, -.015, 'Display brightness is an inverted voltage scale, not calibrated optical response. Refinement and full qualification remain open.', ha='center', fontsize=9)
fig.savefig(d/'nine-pixel-frame.png', dpi=160, bbox_inches='tight')
plt.close(fig)
print(json.dumps({k: result[k] for k in ['run', 'nominal_screens_pass', 'checks', 'max_hold_minus_adc_mV', 'max_hold_minus_dc_mV', 'max_bias_relative_difference', 'max_cap_relative_error']}))
