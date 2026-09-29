"""Render physical checks and capture-window diagnosis for the revised 64 bank."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    r = json.loads((ROOT / 'simulations/compact-bank-64-ground8.json').read_text())
    meta = json.loads((ROOT / r['layout'] / 'verification.json').read_text())
    assert r['physical_checks_pass'] and r['capture_completed'] and not r['full_bank_accuracy_qualified']
    x = [c['column'] for c in r['columns']]
    original, revised = [[c['comparison'][i]['store_changes_uV']['row_off'] for c in r['columns']] for i in [0, 1]]
    fig, grid = plt.subplots(2, 2, figsize=(12, 8.5), layout='constrained')
    axes = grid.ravel()
    for values, label, color in [(original, 'Original 2 µm bus', '#9d452c'), (revised, 'Revised 8 µm bus', '#236a91')]:
        axes[0].plot(x, [v / 1000 for v in values], label=label, color=color)
    axes[0].set(title='Storage terminal: row-deselection shift', xlabel='Column', ylabel='STORE change (mV)')
    for key, label, color in [('upper_V', 'Upper plate', '#236a91'), ('ground_V', 'Ground plate', '#9d452c'),
                               ('differential_V', 'Across capacitor', '#368263')]:
        axes[1].plot(x, [c['revised_row_off_mim_change_uV'][key] for c in r['columns']], label=label, color=color)
    axes[1].set(title='Revised bank: average of eight MIM plates', xlabel='Column', ylabel='Change (µV)')
    for key, label, color in [('original_mim_events', 'Original', '#9d452c'), ('revised_mim_events', 'Revised', '#236a91')]:
        for event, style, suffix in [('before_row_off', '-', 'before'), ('after_row_off', '--', 'after')]:
            axes[2].plot(x, [c[key][event]['ground_V'] * 1000 for c in r['columns']], label=label + ' ' + suffix, color=color, ls=style)
    axes[2].set(title='Actual MIM ground rise above the GND port', xlabel='Column', ylabel='Ground voltage (mV)')
    network = json.loads((ROOT / r['ground_network_diagnostic']).read_text())
    for width, label, color in [(2, 'Original', '#9d452c'), (8, 'Revised', '#236a91')]:
        case, = [v for v in network['cases'] if v['columns'] == 64 and v['ground_width_um'] == width]
        axes[3].plot(x, [v / 1000 for v in case['uniform_1uA_per_column_ground_uV']], label=label, color=color)
    axes[3].set(title='Resistor-network probe: 1 µA per column', xlabel='Column', ylabel='Ground voltage (mV)')
    for axis in axes:
        axis.grid(alpha=.2)
        axis.legend(fontsize=9)
    fig.suptitle('64 columns, 27 °C, alternating 0/240 pA: capture-window diagnosis\nEvent shifts are not matched ADC/readout errors', fontsize=12)
    fig.savefig(ROOT / 'docs/assets/compact-bank-64-ground8.png', dpi=160)
    plt.close(fig)
    worst = max(r['columns'], key=lambda c: abs(c['comparison'][1]['store_changes_uV']['row_off']))
    c = worst['column']
    old_max, new_max = max(map(abs, original)), max(map(abs, revised))
    ground = worst['revised_row_off_mim_change_uV']['ground_V']
    differential = worst['revised_row_off_mim_change_uV']['differential_V']
    old_ground = max(c['original_mim_events']['before_row_off']['ground_V'] for c in r['columns']) * 1000
    new_ground = max(c['revised_mim_events']['before_row_off']['ground_V'] for c in r['columns']) * 1000
    network64, = [c for c in r['ground_network_comparisons'] if c['columns'] == 64]
    refinement = r['capture_refinement']
    reproduction = r['original_prefix_reproduction']
    minutes = r['full_run_budget']['extrapolated_transient_seconds'] / 60
    html = f'''<section id="compact-bank-64-ground8"><h2>64-column ground-bus candidate: physical checks and capture window</h2>
<p><strong>The 8 µm ground-bus correction has a separately verified 64-column candidate.</strong> Both main DRC checks and both LVS paths pass with {meta['mos']} MOS devices, {meta['mim']} MIM plates and {meta['diodes']} photodiodes. A full-layout XOR audit proves that only the intended M4 ground rectangle changes, with unchanged labels and independent reference circuit.</p>
<p>The candidate measures <strong>{r['size_um'][0]:.2f} × {r['size_um'][1]:.2f} µm</strong>, leaving {r['budget_margin_um'][0]:.2f} µm width and {r['budget_margin_um'][1]:.2f} µm height inside the 2700 × 1100 µm bank budget. The extra 1.8 µm width does not establish complete-chip fit. This bank already contains one pixel row; final assembly adds 63 rows.</p>
<p>A fresh {r['capture_step_ns']:g} ns nominal trace completes initialization, capture, row deselection and pixel reset through <strong>1.405 ms</strong> in {r['capture_transient_seconds']:.1f} wall seconds, with physical MIM plate probes. The original timed-out full trace contains this entire early window; its nine archived file hashes are verified before using that prefix. Every photocurrent source is checked against its corresponding extracted diode, allowing for renamed ground terminals. The remaining stimuli/options match after excluding the model include path, stop time and additional saved probes.</p>
<figure><img src="assets/compact-bank-64-ground8.png" alt="Original and revised 64-column storage-node row-deselection shifts, and revised MIM plate contributions"><figcaption>Before row-off: 1.402 ms − 1 ns; after row-off: 1.4025 ms. The original full run remains a timeout; only its verified capture prefix is used here.</figcaption></figure>
<p>Worst row-deselection STORE movement changes from <strong>{old_max / 1000:.3f} to {new_max / 1000:.3f} mV</strong>. At the revised worst column ({c}), the mean physical ground plate changes by {ground:.3f} µV and the across-capacitor voltage by {differential:.3f} µV. These measurements diagnose stored-voltage movement; they are not same-state capture/readout or ADC error measurements and are not judged against the 500 µV output criterion.</p>
<p><strong>The 16-column electrical improvement does not automatically scale.</strong> A fresh original-layout capture with identical physical probes reproduces the retained prefix within {reproduction['max_uV']:.6f} µV at the six event times. The revised 200→100 ns event comparison differs by at most {refinement['max_uV']:.6f} µV across common saved terminals (10 µV diagnostic comparison limit: {'pass' if refinement['passes'] else 'fail'}). The larger revised STORE shift needs further investigation.</p>
<p>Worst actual pre-deselection MIM ground rise drops from {old_ground:.3f} to {new_ground:.3f} mV, but remains substantial. A separate resistor-network calculation reduces far-end self-resistance from {network64['original_far_self_ohm']:.3f} to {network64['revised_far_self_ohm']:.3f} Ω. With an artificial 1 µA test current per column, maximum ground rise falls from {network64['original_max_uniform_uV']:.3f} to {network64['revised_max_uniform_uV']:.3f} µV. Those test currents are not the operating circuit currents; the calculation demonstrates improved extracted resistance, not corrected transient behavior.</p>
<p><strong>Full readout remains open.</strong> The old layout reached 14 of 128 readout instants before its 900 s watchdog. A simple extrapolation from its readout phase gives about {minutes:.0f} minutes for the transient alone. The next full experiment should allow a 10,800 s watchdog and budget additional time for 64 capture plus 128 output references. This estimate is not a runtime guarantee; routing and concurrent workloads can change it.</p>
<p class="note">No complete 64-column readout or accuracy pass is claimed. Nominal/hot patterns, timestep and placement checks, process/wire/supply corners, actual local supply/reference drops, real drivers, repeated rows and assembled-chip manufacturing checks remain ahead. Main DRC excludes density, antenna and cup checks.</p>
<p>The subsequent <a href="#compact-bank-64-read-probes">matched far-column readout and distributed-return comparison</a> quantify the output error. Preserve this candidate and the original traces as controls; local bias/supply checks and a complete qualified full-bank scan remain necessary.</p>
<p><a href="../simulations/compact-bank-64-ground8.json">Physical/capture evidence and hashes</a> · <a href="compact-bank-64-ground8.md">Reproduction</a> · <a href="#compact-bank-16-extension">16-column continuation</a> · <a href="#wafer-space-run3">Manufacturing envelope</a></p></section>'''
    (ROOT / 'docs/compact-bank-64-ground8-section.html').write_text(html + '\n')
    markdown = f'''# 64-column 8 µm ground-bus candidate

Both main DRC checks and both LVS paths pass. The independent reference remains
byte-identical, and a complete GDS XOR audit restricts the change to the intended
M4 ground rectangle. Device census: {meta['mos']} MOS, {meta['mim']} MIM plates,
{meta['diodes']} diodes. Size: {r['size_um'][0]:.2f} × {r['size_um'][1]:.2f} µm,
within the 2700 × 1100 µm local budget.

The nominal alternating 0/240 pA capture diagnostic completes 1.405 ms with
{r['capture_step_ns']:g} ns steps in {r['capture_transient_seconds']:.1f} s.
It saves actual MIM terminal voltages and stops before the first output selection.
The original 900 s full-run timeout is preserved. Its fully recorded early window
is used only for event diagnosis, after verifying all nine archived file hashes.

Worst row-off STORE movement changes from {old_max:.3f} to {new_max:.3f} µV.
At the revised worst column {c}, average MIM ground/across-capacitor changes are
{ground:.3f}/{differential:.3f} µV. These are event shifts, not matched ADC errors.
There are no full-bank sample references or electrical accuracy claims here.

The 200→100 ns comparison changes common saved event terminals by at most
{refinement['max_uV']:.6f} µV (10 µV diagnostic comparison limit;
{'passes' if refinement['passes'] else 'fails'}). A fresh original-layout capture
with physical probes reproduces its earlier prefix within {reproduction['max_uV']:.6f} µV.
The maximum actual pre-row-off MIM ground rise changes from {old_ground:.3f}
to {new_ground:.3f} mV. The 64-column candidate is not established as an
electrical correction: the row-off STORE shift is slightly larger.

The separate [ground-network calculation](../simulations/compact-bank-ground-network-20260927.json)
shows that far-end self-resistance falls from {network64['original_far_self_ohm']:.3f}
to {network64['revised_far_self_ohm']:.3f} Ω. Uniform 1 µA-per-column probes give
{network64['original_max_uniform_uV']:.3f}/{network64['revised_max_uniform_uV']:.3f} µV
maximum original/revised ground rise. These are artificial test currents,
not measured operating currents. Both 16- and 64-column network comparisons
pass residual, reciprocity and positive-energy checks; widening reduces
resistive energy for the sampled MIM terminal current basis.

![Capture-window comparison](assets/compact-bank-64-ground8.png)

## Reproduce with fresh output directories

```sh
bash scripts/run-tools.sh python3 scripts/build-compact-bank.py \\
  --columns 64 --ground-bus-width-um 8 \\
  --out build/compact-bank-c64-ground8-new
bash scripts/run-tools.sh python3 scripts/audit-bank-ground-scaling.py \\
  --original build/compact-bank-c64-v1-20260926 \\
  --revised build/compact-bank-c64-ground8-new \\
  --out build/compact-bank-c64-ground8-geometry-new
bank_capture_lights=$(python3 -c "print(','.join(['0','240']*32))")
bash scripts/run-tools.sh python3 scripts/simulate-compact-bank.py \\
  --layout build/compact-bank-c64-ground8-new \\
  --out build/compact-bank-c64-ground8-capture-new \\
  --lights-pa "$bank_capture_lights" --temperature 27 --step-ns 200 \\
  --phase capture --solver klu --timeout 1200 --save-mim-terminals
```

Repeat the capture command with 100 ns and a separate output directory for
refinement. Repeat the 200 ns command using the original
`build/compact-bank-c64-v1-20260926` layout and another fresh directory for
the original-layout MIM-probe control. All three use the same illumination,
temperature, strict settings and physical terminal saves.

Audit and render the retained evidence:

```sh
bash scripts/run-tools.sh python3 scripts/report-bank-64-ground8.py \\
  --layout build/compact-bank-c64-ground8-20260927 \\
  --geometry build/compact-bank-c64-ground8-geometry-audit-20260927 \\
  --run build/compact-bank-c64-ground8-capture-20260927 \\
  --refined build/compact-bank-c64-ground8-capture100-20260927 \\
  --original-probed build/compact-bank-c64-original-capture-probes-20260927
bash scripts/run-tools.sh python3 scripts/render-bank-64-ground8.py
python3 scripts/update-overview-sections.py
```

## Next full-run budget and limits

The original readout phase observed 14/128 scheduled readout instants. Extrapolating
that phase gives {minutes:.0f} minutes for a complete transient; allow a 10,800 s
watchdog and additional time for 192 independent references. Routing and
concurrency affect runtime, so this is a planning estimate only.

The [subsequent matched far-column readout](compact-bank-64-read-probes.md)
quantifies the output error and compares a distributed ground-return candidate.
The improved resistor network alone does not establish an electrical fix.
Complete the remaining 16-column scope and then qualify complete 64-column
readout, nominal/hot patterns, refinement, placements and local supply/reference
drops. Main DRC excludes density/antenna/cup; this is an unfilled development
block with external resistors, behavioral drivers and an external ADC fixture.
Exact-chip fit, real controls, repeated rows, final power/pads, optical packaging
and provider prechecks remain open. The bank already has one pixel row; add 63
rows for the 4096-pixel chip.

[Overview](overview.html#compact-bank-64-ground8) ·
[Evidence report](../simulations/compact-bank-64-ground8.json)
'''
    (ROOT / 'docs/compact-bank-64-ground8.md').write_text(markdown)
    print(json.dumps(dict(original_store_shift_uV=old_max, revised_store_shift_uV=new_max,
                          revised_worst_column=c, revised_mim_ground_uV=ground,
                          revised_mim_differential_uV=differential), indent=2))


if __name__ == '__main__':
    main()
