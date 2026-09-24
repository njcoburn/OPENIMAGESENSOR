"""Compare bounded shared-circuit diagnostics without qualifying a correction."""
from pathlib import Path
import hashlib
import json
import runpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1]
B = R/'build/shared-circuit'
read = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
source = R/'build/functional-camera-diagnostic/reset-edge-internal-20260920'
bn, bv = read(source/'stream.raw')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
runs = ['camera-no-clamps-20260920', 'camera-clamp0-20260920', 'camera-clamps0-6-20260920',
        'all-clamps-ideal-supply-20260920', 'ideal-supply-local46-control-20260920', 'all-clamps-norton-drivers-20260920',
        'ideal-supply-norton-reset-20260920', 'no-clamps-ideal-short-20260920', 'clamp0-ideal-short-20260920',
        'no-clamps-ideal-norton-reset-20260920']
summary = dict(accepted_full_chip=False, source_model_sha256=sha(source/'model.spice'),
               source_raw_sha256=sha(source/'stream.raw'), cases=[], driver_equation_baseline={})
fig, axs = plt.subplots(2, 1, figsize=(11, 8), layout='constrained')
axs[0].plot(bv[:, 0]*1e3, bv[:, bn.index('v(hold)')], label='Original full chip (aborts)', color='black', linewidth=2)
for run in runs:
    d = B/run
    r = json.loads((d/'result.json').read_text())
    assert r['model_sha256'] == sha(d/'model.spice') and r['deck_sha256'] == sha(d/'test.spice')
    n, v = read(d/'stream.raw')
    r['classification'] = 'completed diagnostic' if r['completed'] else 'watchdog stop' if r['timed_out'] else 'solver abort' if r['solver_errors'] else 'incomplete'
    r['crossed_original_reset_failure'] = bool(v[-1, 0] > .003270020001)
    r['retained_samples'] = []
    for row in range(2):
        for col in range(3):
            t = .002185+row*.001+col*18e-6
            if t <= v[-1, 0]:
                held = float(np.interp(t, v[:, 0], v[:, n.index('v(hold)')]))
                original = float(np.interp(t, bv[:, 0], bv[:, bn.index('v(hold)')]))
                r['retained_samples'].append(dict(row=row, column=col, hold_V=held, difference_from_original_uV=(held-original)*1e6))
    if 'ideal' not in run:
        label = f'{len(r["clamps"])} clamp domains' + ('; Norton drivers' if r.get('drivers') == 'norton' else '')
        axs[0].plot(v[:, 0]*1e3, v[:, n.index('v(hold)')], label=label, alpha=.8)
        # Show the accepted time steps around the known row turn-off slowdown.
        dt = np.diff(v[:, 0])
        mask = (v[1:, 0] >= .0032299) & (v[1:, 0] <= .0032302)
        axs[1].semilogy((v[1:, 0][mask]-.00323002)*1e9, np.maximum(dt[mask], 1e-30), '.', markersize=3, label=label)
    summary['cases'].append(r)
for kind in ['rst', 'row', 'sel']:
    for i in range(3):
        label = kind+str(i)
        col = lambda key: bv[:, bn.index(key)]
        expected = (col('v(pad_'+label+')')-col('v(ctl_'+label+')')*col('v(vdd)'))/100
        residual = col('i(@bdrive_'+label+'[i])')-expected
        summary['driver_equation_baseline'][label] = dict(max_residual_A=float(np.max(np.abs(residual))),
            max_equivalent_voltage_residual_uV=float(np.max(np.abs(residual)))*100*1e6)
audit = B/'full-restoration-audit-20260920'
summary['full_restoration_model_exact'] = sha(audit/'model.spice') == sha(source/'model.spice')
assert summary['full_restoration_model_exact']
# The local v46 build reproduces the changed-supply control; this is not a
# version comparison of the original-supply full-chip failure.
n1, v1 = read(B/'all-clamps-ideal-supply-20260920/stream.raw')
n2, v2 = read(B/'ideal-supply-local46-control-20260920/stream.raw')
summary['ideal_supply_local46_exact_match'] = bool(n1 == n2 and np.array_equal(v1, v2))
nr, vr = read(B/'ideal-supply-norton-reset-20260920/stream.raw')
voltage_keys = ['v(vdd)', 'v(pad_vreset)', 'v(sensor_3x3_0.vreset)']
voltage_keys += ['v('+p['sense']+')' for p in json.loads((R/'simulations/final-chip-pixel-map.json').read_text())['pixels']]
summary['short_reset_formulation_comparison'] = dict(
    scope='Common captured interval of ideal-supply controls only; interpolated waveforms, not full-chip qualification',
    end_s=float(v1[-1, 0]),
    max_voltage_difference_uV={key: float(np.max(np.abs(v1[:, n1.index(key)]-np.interp(v1[:, 0], vr[:, 0], vr[:, nr.index(key)]))))*1e6 for key in voltage_keys})
nn, vn = read(B/'no-clamps-ideal-short-20260920/stream.raw')
nnr, vnr = read(B/'no-clamps-ideal-norton-reset-20260920/stream.raw')
summary['small_short_reset_formulation_comparison'] = dict(
    scope='Common interval of 317-device ideal-supply control; different event from original third-row failure',
    end_s=float(vn[-1, 0]),
    max_voltage_difference_uV={key: float(np.max(np.abs(vn[:, nn.index(key)]-np.interp(vn[:, 0], vnr[:, 0], vnr[:, nnr.index(key)]))))*1e6 for key in voltage_keys})
dt = np.diff(bv[:, 0]); mask = (bv[1:, 0] >= .0032299) & (bv[1:, 0] <= .0032302)
axs[1].semilogy((bv[1:, 0][mask]-.00323002)*1e9, np.maximum(dt[mask], 1e-30), '.', color='black', markersize=2, label='Original full chip')
axs[0].set(xlabel='Time (ms)', ylabel='Held output (V)', title='Retained output traces; partial runs are not frame passes', xlim=(2.15, 3.29))
axs[1].set(xlabel='Time relative to second-row turn-off (ns)', ylabel='Accepted timestep (s)', title='Shared-circuit slowdown around 3.23002 ms', xlim=(-10, 30))
for ax in axs:
    ax.grid(alpha=.2)
    ax.legend(fontsize=8)
fig.savefig(R/'docs/assets/shared-circuit.png', dpi=150)
plt.close(fig)
fig, axs = plt.subplots(2, 1, figsize=(10, 7), sharex=True, layout='constrained')
for n, v, label, current in [(nn, vn, 'Original source (aborts)', 'i(vresetdrive)'),
                            (nnr, vnr, 'Equivalent Norton source (completes)', 'i(@bresetdrive[i])')]:
    x = (v[:, 0]-.00122)*1e9
    mask = (x >= -1) & (x <= 20)
    axs[0].plot(x[mask], (v[mask, n.index('v(sensor_3x3_0.vreset)')]-2)*1e6, '.-', markersize=2, label=label)
    axs[1].plot(x[mask], v[mask, n.index(current)]*1e6, '.-', markersize=2, label=label)
for ax in axs:
    ax.axvline((vn[-1, 0]-.00122)*1e9, linestyle=':', color='black', label='Original abort')
    ax.grid(alpha=.2)
    ax.legend(fontsize=8)
axs[0].set(ylabel='Reset reference minus 2 V (µV)', title='Fast 317-device control: same terminal equation, different numerical outcome')
axs[1].set(ylabel='Reset-source current (µA)', xlabel='Time from initial reset falling start (ns)', xlim=(-1, 20))
fig.suptitle('Ideal-supply diagnostic only; not the original third-row failure')
fig.savefig(R/'docs/assets/shared-circuit-reset-source.png', dpi=150)
plt.close(fig)
(R/'simulations/shared-circuit.json').write_text(json.dumps(summary, indent=2)+'\n')
for r in summary['cases']:
    print(r['name'], r['classification'], f'{r["end_s"]*1000:.12g} ms', f'{r["seconds"]:.2f} s')
print('Ideal-supply local46 exact match:', summary['ideal_supply_local46_exact_match'])
