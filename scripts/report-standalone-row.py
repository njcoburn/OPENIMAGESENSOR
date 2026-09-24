"""Report row isolation and the captured full-chip reset failure."""
from pathlib import Path
import hashlib
import json
import runpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1]
root = R/'build/standalone-row'
source = R/'build/functional-camera-diagnostic/reset-edge-internal-20260920'
read = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
names, full = read(source/'stream.raw')
pixels = json.loads((R/'simulations/final-chip-pixel-map.json').read_text())['pixels']
audit = json.loads((root/'isolation-20260920/topology-audit.json').read_text())
assert hashlib.sha256((source/'model.spice').read_bytes()).hexdigest() == audit['source_model_sha256']
runs = ['isolation-20260920', 'isolation-fine-20260920', 'isolation-finite-20260920', 'isolation-finite-fine-20260920']
cases = []
for run in runs:
    result = json.loads((root/run/'result.json').read_text())
    for case in result['cases']:
        case = dict(case, run=run)
        path = root/run/f'r{case["row"]}-{case["stage"]}'
        assert hashlib.sha256((path/'test.spice').read_bytes()).hexdigest() == case['deck_sha256']
        cases.append(case)
assert len(cases) == 12 and all(x['completed'] for x in cases)
refinements = []
for supply, coarse, fine in [('ideal', runs[0], runs[1]), ('finite', runs[2], runs[3])]:
    a = json.loads((root/coarse/'r2-pads/result.json').read_text())['sense_after_reset_V']
    b = json.loads((root/fine/'r2-pads/result.json').read_text())['sense_after_reset_V']
    refinements.append(dict(supply=supply, checkpoint='1 us after row-2 reset edge; isolated sense nodes, not ADC samples',
        maximum_difference_uV=max(abs(a[k]-b[k]) for k in a)*1e6))
edge_summaries = []
fig, axs = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
for row in range(3):
    edge = .00127002+row*.001
    mask = (full[:, 0] >= edge-20e-9) & (full[:, 0] <= edge+20e-9)
    x = (full[mask, 0]-edge)*1e9
    px = next(p for p in pixels if p['row'] == row and p['column'] == 0)
    gate = full[mask, names.index(f'v(sensor_3x3_0.rst{row})')]
    sense = full[mask, names.index('v('+px['sense']+')')]
    current = full[mask, names.index('i(@m.'+px['reset'].lower()+'.m0[id])')]
    axs[0, 0].plot(x, gate, label=f'Row {row+1}'+(' (aborts)' if row == 2 else ''))
    axs[0, 1].plot(x, sense, label=f'Row {row+1}, column 1')
    axs[1, 0].plot(x, current*1e9, label=f'Row {row+1}, column 1')
    edge_summaries.append(dict(row=row, window_points=int(mask.sum()), window_last_relative_ns=float(x[-1]),
        reset_gate_range_V=[float(gate.min()), float(gate.max())], column0_sense_range_V=[float(sense.min()), float(sense.max())],
        column0_reset_drain_current_range_A=[float(current.min()), float(current.max())]))
edge = .00327002
for stage, label in [('devices', 'Devices'), ('caps', '+ wiring capacitance'), ('pads', '+ input-pad protection')]:
    n, v = read(root/runs[0]/f'r2-{stage}/stream.raw')
    mask = (v[:, 0] >= edge-20e-9) & (v[:, 0] <= edge+20e-9)
    axs[1, 1].plot((v[mask, 0]-edge)*1e9, v[mask, n.index('v(a_96842_137580#)')], label=label)
for ax, title, ylabel in [(axs[0, 0], 'Full chip: internal reset gate', 'Voltage (V)'),
                          (axs[0, 1], 'Full chip: pixel sense voltage', 'Voltage (V)'),
                          (axs[1, 0], 'Full chip: reset MOS drain current', 'Current (nA)'),
                          (axs[1, 1], 'Standalone third row: sense voltage', 'Voltage (V)')]:
    ax.set(title=title, xlabel='Time from reset falling endpoint (ns)', ylabel=ylabel, xlim=(-20, 20))
    ax.axvline(0, color='black', linestyle=':', alpha=.4)
    ax.grid(alpha=.2)
    ax.legend(fontsize=8)
fig.suptitle('Rows share device topology; isolated resets complete\nFull-chip row 3 trace stops at failure; standalone boundaries remove shared feedback')
fig.savefig(R/'docs/assets/standalone-row.png', dpi=150)
plt.close(fig)
summary = dict(rows_identical_devices=audit['rows_identical_devices'], device_records_per_row=34,
    source_model_sha256=audit['source_model_sha256'], source_raw_sha256=audit['source_raw_sha256'],
    incident_capacitance_fF=[r['total_incident_capacitance_fF'] for r in audit['rows']],
    cases=cases, isolated_refinement=refinements, captured_full_chip_reset_windows=edge_summaries,
    accepted_full_chip=False, failure_reproduced_in_isolated_row=False,
    conclusion='Identical local device topology; all 12 isolated cases cross reset. Shared chip feedback and charge history remain untested by this isolation; no causal device identified.')
(R/'simulations/standalone-row.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(dict(cases=len(cases), all_completed=True, refinements=refinements), indent=2))
