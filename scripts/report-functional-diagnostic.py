"""Summarize retained diagnostic points, including incomplete runs."""
from pathlib import Path
import argparse
import runpy
import json
import hashlib
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('run')
a = p.parse_args()
d = R/'build/functional-camera-diagnostic'/a.run
r = json.loads((d/'result.json').read_text())
read_raw = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
names, v = read_raw(d/'stream.raw')
t = v[:, 0]
def col(name):
    return v[:, names.index(name)]

# Group very small accepted timesteps by the nearest microsecond to expose stalls.
dt = np.diff(t)
small = dt < 1e-10
bins, counts = np.unique(np.round(t[1:][small]*1e6, 1), return_counts=True)
rank = np.argsort(counts)[::-1][:10]
summary = dict(run=a.run, completed=r['completed'], end_s=float(t[-1]), points=len(t),
               min_timestep_s=float(dt.min()), tiny_step_count=int(small.sum()),
               tiny_step_clusters=[dict(time_us=float(bins[i]), points=int(counts[i])) for i in rank],
               accepted_full_chip=False)
summary['supply_V'] = dict(min=float(col('v(vdd)').min()), max=float(col('v(vdd)').max()))
summary['sampling_peak_abs_A'] = {name: float(np.max(np.abs(col(name)))) for name in ['i(@bsample[i])', 'i(@bsample_reset[i])']}
summary['clamp_timing_V'] = {name: dict(min=float(col(name).min()), max=float(col(name).max())) for name in names if name.startswith('v(pex_safe_')}
summary['retained_window_only'] = True
printed_times = [format(x, ' 12.5e') for x in t]
summary['rounded_progress_clusters'] = []
for label, count in Counter(printed_times).most_common(5):
    indices = [i for i, value in enumerate(printed_times) if value == label]
    summary['rounded_progress_clusters'].append(dict(display=label.strip(), accepted_points=count,
        first_s=float(t[indices[0]]), last_s=float(t[indices[-1]]),
        actual_progress_s=float(t[indices[-1]]-t[indices[0]])))
conductance = lambda x: 1e-12+(0.01-1e-12)*(0.5+0.5*np.tanh((x-1.65)/0.1))
predictions = {
    'i(@bsample[i])': (col('v(adcin)')-col('v(hold)'))*conductance(col('v(acq)')),
    'i(@bsample_reset[i])': col('v(hold)')*conductance(col('v(rstadc)')),
}
if r['control'] == 'sample-off':
    predictions['i(@bsample[i])'] = (col('v(adcin)')-col('v(hold)'))*1e-12
summary['switch_equation_max_residual_A'] = {name: float(np.max(abs(col(name)-pred))) for name, pred in predictions.items()}
capinfo = json.loads((R/'build/functional-pad-model/caps.json').read_text())
frozen = json.loads((R/'build/functional-pad-model/frozen-model.json').read_text())
assert hashlib.sha256((d/'model.spice').read_bytes()).hexdigest() == frozen['frozen_sha256']
op = json.loads((R/'build/functional-camera/op-100ns/result.json').read_text())
assert hashlib.sha256((R/'build/functional-camera/op-100ns/result.json').read_bytes()).hexdigest() == frozen['op_sha256']
cv = lambda x: .001107+.00107*np.tanh(6.25*x-4.1875)
summary['cap_range_retained_window'] = []
for i, (positive, negative) in enumerate(capinfo['pairs']):
    assert negative == 'GND'
    voltage = col(f'v({positive.lower()})')
    bias = op['summary']['last_values'][17+i]
    summary['cap_range_retained_window'].append(dict(pair=[positive, negative],
        min_V=float(voltage.min()), max_V=float(voltage.max()),
        max_relative_C_error=float(np.max(abs(cv(voltage)/cv(bias)-1)))))
summary['retained_samples'] = []
pattern = [[0, 80, 240], [240, 0, 80], [80, 240, 0]]
for row in range(3):
    for column in range(3):
        sample_time = .002185 + row*.001 + column*18e-6
        if sample_time <= t[-1]:
            hold = float(np.interp(sample_time, t, col('v(hold)')))
            adc = float(np.interp(sample_time, t, col('v(adcin)')))
            summary['retained_samples'].append(dict(row=row, column=column, time_s=sample_time,
                light_pA=pattern[row][column], hold_V=hold, hold_minus_adc_mV=1000*(hold-adc)))
fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True, layout='constrained')
for name in ['v(pad_row0)', 'v(pad_row1)', 'v(pad_row2)', 'v(pad_sel0)', 'v(pad_sel1)', 'v(pad_sel2)']:
    axes[0].plot(t*1e3, col(name), label=name)
for name in ['v(pad_buf)', 'v(adcin)', 'v(hold)', 'v(sensor_3x3_0.out)']:
    axes[1].plot(t*1e3, col(name), label=name)
for name in names:
    if name == 'v(vdd)' or name.startswith('v(pex_safe_'):
        axes[2].plot(t*1e3, col(name), label=name, alpha=.7)
axes[3].semilogy(t[1:]*1e3, np.maximum(dt, 1e-30), '.', markersize=2)
for ax in axes[:2]:
    ax.legend(fontsize=7, ncol=3)
for ax in axes[:3]:
    ax.set_ylabel('Voltage (V)')
axes[2].set_title('Supply and 15 clamp timing nodes')
axes[3].set(ylabel='Accepted timestep (s)', xlabel='Time (ms)')
fig.suptitle(f'{a.run}: retained diagnostic waveform; completed={r["completed"]}\nBias-frozen MOS capacitance; no qualification claim')
fig.savefig(d/'response.png', dpi=140)
target_edge_ms = 3.2302 if r['control'] == 'row-slew-100ns' else 3.23002
edge_ms = target_edge_ms if t[-1]*1e3 >= target_edge_ms else t[-1]*1e3
axes[-1].set_xlim(max(0, edge_ms-.0002), min(t[-1]*1e3+.0001, edge_ms+.0003))
axes[-1].ticklabel_format(axis='x', useOffset=False, style='plain')
fig.savefig(d/'last-edge.png', dpi=140)
(d/'analysis.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary))
