"""Show the selected far-column readout controls without a full-bank claim."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = [('8 µm bus', ROOT / 'simulations/compact-bank-64-far-read.json')]
    grid_source = ROOT / 'simulations/compact-bank-64-ground-grid-read.json'
    if grid_source.exists():
        sources.append(('Ground grid', grid_source))
    acquisition_source = ROOT / 'simulations/compact-bank-64-acquisition12.json'
    if acquisition_source.exists():
        assert grid_source.exists()
        sources.append(('Ground grid\n12 µs acquisition', acquisition_source))
    results = [(label, json.loads(path.read_text())) for label, path in sources]
    for label, result in results:
        assert result['independent_audit_completed'] and not result['full_bank_accuracy_qualified']
        assert result['column_read'] == 62 and result['columns'] == 64
        assert bool(result['ground_return_grid']) == label.startswith('Ground grid')
    if len(results) >= 2:
        assert [(s['scan'], s['time_s']) for s in results[0][1]['samples']] == [(s['scan'], s['time_s']) for s in results[1][1]['samples']]
    fig, ax = plt.subplots(figsize=(9, 4.3), layout='constrained')
    labels, total, tracking = [], [], []
    for label, result in results:
        for sample in result['samples']:
            labels.append(label + '\n' + sample['scan'])
            total.append(abs(sample['total_error_uV']))
            tracking.append(abs(sample['tracking_error_uV']))
    x = np.arange(len(labels))
    ax.bar(x - .18, total, width=.34, color='#ad4c2d', label='Total capture/readout')
    ax.bar(x + .18, tracking, width=.34, color='#236a91', label='Output tracking')
    ax.axhline(500, color='#9c2626', ls='--', label='500 µV limit')
    ax.set(xticks=x, xticklabels=labels, ylabel='Absolute error (µV)', title='64-column physical bank: selected column 62 read twice\n27 °C, alternating 0/240 pA, 100 ns timestep')
    ax.grid(axis='y', alpha=.2); ax.legend(fontsize=9)
    fig.savefig(ROOT / 'docs/assets/compact-bank-64-read-probes.png', dpi=160)
    plt.close(fig)
    base = results[0][1]
    worst = max(abs(s['total_error_uV']) for s in base['samples'])
    track = max(abs(s['tracking_error_uV']) for s in base['samples'])
    table = ''.join(f'<tr><td>{label}</td><td>{s["scan"]}</td><td>{s["total_error_uV"]:.3f}</td><td>{s["tracking_error_uV"]:.3f}</td></tr>'
                    for label, result in results for s in result['samples'])
    grid_html = '<p><strong>Distributed-return candidate:</strong> its physical checks and matched readout are being investigated separately. No electrical result is claimed until the independent audit finishes.</p>'
    grid_md = 'The distributed-return candidate is still being investigated.\n'
    if len(results) >= 2:
        grid = results[1][1]
        meta = json.loads((ROOT / grid['layout'] / 'verification.json').read_text())
        geometry_path = ROOT / 'build/compact-bank-c64-ground-grid-geometry-20260927/result.json'
        geometry = json.loads(geometry_path.read_text())
        assert geometry['only_recorded_ground_additions'] and geometry['reference_identical']
        assert meta['magic_drc_errors'] == meta['klayout_main_drc_errors'] == 0 and meta['direct_and_resistor_collapsed_lvs']
        gw = max(abs(s['total_error_uV']) for s in grid['samples'])
        gt = max(abs(s['tracking_error_uV']) for s in grid['samples'])
        outcome = 'passes' if grid['selected_capture_readout_pass'] and grid['selected_tracking_pass'] else 'fails'
        grid_html = f'''<p><strong>The distributed-return candidate {outcome} this selected diagnostic with 10 µs acquisition:</strong> {gw:.3f} µV total error and {gt:.3f} µV tracking. Three 24 µm M4 rails across the top and left connect through M5 returns to every column's ground-plate route. Both main DRC checks and both LVS paths pass. A geometry audit verifies only the 647 recorded ground-metal/via additions, including 192 via4 cuts, with unchanged labels, independent reference and device census.</p>
<p>The new bank is {geometry['size_um'][0]:.2f} × {geometry['size_um'][1]:.2f} µm, within 2700 × 1100 µm. It adds no pixels or analog devices and keeps the optical apertures clear. This selected readout result does not qualify all columns, temperatures, patterns or complete frames.</p>'''
        grid_md = f'''The distributed-return candidate **{outcome} the selected diagnostic with 10 µs acquisition**:
{gw:.3f} µV worst total error and {gt:.3f} µV tracking. Both main DRC checks and
both LVS paths pass. The GDS audit restricts the change to 647 recorded ground
metal/via rectangles on layers 46/0, 41/0 and 81/0, including 192 via4 cuts.
Labels, reference circuit and device census are unchanged. Size is
{geometry['size_um'][0]:.2f} × {geometry['size_um'][1]:.2f} µm within the local
2700 × 1100 µm budget. Optical apertures remain clear.
'''
        network = json.loads((ROOT / 'simulations/compact-bank-ground-grid-network-20260927.json').read_text())
        assert network['all_test_current_patterns_nonincreasing_resistive_energy']
        network_text = (f"The extracted resistor-network diagnostic reduces far-column self resistance from "
                        f"{network['original_far_self_ohm']:.3f} to {network['revised_far_self_ohm']:.3f} Ω. "
                        f"Artificial uniform 1 µA-per-column injection gives a maximum ground rise of "
                        f"{network['original_max_uniform_uV']:.3f} → {network['revised_max_uniform_uV']:.3f} µV. "
                        "These test currents characterize the wiring; they are not simulated operating device currents.")
        grid_html += '<p>' + network_text + ' <a href="../simulations/compact-bank-ground-grid-network-20260927.json">Network evidence</a>.</p>'
        grid_md += '\n' + network_text + '\n\n[Network evidence](../simulations/compact-bank-ground-grid-network-20260927.json).\n'
        residual = max(abs(s['total_error_uV'] - s['tracking_error_uV']) for s in grid['samples'])
        split_text = (f"Subtracting output tracking from total error leaves at most {residual:.3f} µV "
                      "between the matched stored-state output reference and the capture reference. "
                      "This reference difference is separate from the 340 µV output-settling error; "
                      "it is not a direct measurement of a single physical error mechanism.")
        grid_html += '<p>' + split_text + '</p>'
        grid_md += '\n' + split_text + '\n'
    if len(results) == 3:
        timing = results[2][1]
        assert timing['acquisition_us'] == 12 and timing['unchanged_prefix_max_uV'] < 10
        total12 = max(abs(s['total_error_uV']) for s in timing['samples'])
        track12 = max(abs(s['tracking_error_uV']) for s in timing['samples'])
        outcome12 = 'passes' if timing['selected_capture_readout_pass'] and timing['selected_tracking_pass'] else 'fails'
        note = (f"With acquisition extended from 10 to 12 µs, the same ground-grid bank {outcome12} "
                f"this selected diagnostic at {total12:.3f} µV total error and {track12:.3f} µV tracking. "
                "Only the ACQ falling edges move by 2 µs; samples move to 1.423999 and 2.683999 ms. "
                "Reset and selection windows, all physical loads, model parameters and tolerances are unchanged. "
                f"Saved terminal comparisons before the first modified edge differ by at most {timing['unchanged_prefix_max_uV']:.6f} µV. "
                "The 20 µs slot length is unchanged, but this is still a one-column diagnostic with behavioral ADC controls.")
        grid_html += '<p><strong>Acquisition-time control:</strong> ' + note + ' <a href="../simulations/compact-bank-64-acquisition12.json">Audited timing result</a>.</p>'
        grid_md += '\n' + note + '\n\n[Audited timing result](../simulations/compact-bank-64-acquisition12.json).\n'
    html = f'''<section id="compact-bank-64-read-probes"><h2>64-column diagnostic: matched far-column readout</h2>
<p><strong>The 8 µm-bus control fails this selected readout test.</strong> Column 62 gives {worst:.3f} µV worst total capture/readout error against 500 µV. Its output tracking passes at {track:.3f} µV. This demonstrates why the passing 16-column result cannot qualify the full-width bank.</p>
<p>The complete physical 64-column circuit and loads are retained. Column 62 alone is selected twice, at sample times 1.421999 and 2.681999 ms, during a 2.7 ms transient. One capture reference freezes all 64 local pixel voltages before capture opens; two output references also freeze all storage voltages at their sample times. All three are independently simulated and re-read.</p>
<figure><img src="assets/compact-bank-64-read-probes.png" alt="Selected column 62 capture/readout and output tracking errors compared with the 500 microvolt limit"><figcaption>These two selected reads are a bounded diagnostic, not the 128-output full-bank schedule.</figcaption></figure>
<table><thead><tr><th>Layout</th><th>Read</th><th>Signed total error, µV</th><th>Signed tracking error, µV</th></tr></thead><tbody>{table}</tbody></table>
{grid_html}
<p>The reference generator reproduces all 96 archived nominal/hot 16-column reference decks byte for byte. The independent audit verifies circuit/deck hashes, complete finite waveforms, the two selected control windows, all unselected columns, every saved sample, the exact reference clamp voltages and the recomputed errors. It keeps <code>full_bank_accuracy_qualified=false</code>.</p>
<p class="note">Still required: complete 64-column first/late scans and all 192 independent references, numerical refinement of that full schedule, nominal/hot patterns, placement/process/wire/supply checks, local bias and supply measurements, real drivers, repeated rows and exact 64×64 manufacturing qualification. A selected diagnostic pass is not tapeout readiness.</p>
<p><a href="../simulations/compact-bank-64-far-read.json">8 µm-bus control audit</a>{' · <a href="../simulations/compact-bank-64-ground-grid-read.json">Ground-grid readout audit</a>' if len(results) >= 2 else ''} · <a href="compact-bank-64-read-probes.md">Reproduction and limits</a> · <a href="#compact-bank-64-ground8">Capture-window and ground-drop diagnosis</a></p></section>'''
    (ROOT / 'docs/compact-bank-64-read-probes-section.html').write_text(html + '\n')
    markdown = f'''# Selected far-column readout with the physical 64-column bank

The 8 µm-bus control **fails** at {worst:.3f} µV total capture/readout error
(500 µV limit), while output tracking passes at {track:.3f} µV. Column 62 is
selected twice with every physical column and load retained. Three independent
matched-state references are checked; this is not the complete 128-read schedule.

{grid_md}
![Selected-read comparison](assets/compact-bank-64-read-probes.png)

## Reproduction

Use a fresh directory for each experiment:

```sh
bash scripts/run-tools.sh python3 scripts/probe-bank-readout.py \\
  --layout build/compact-bank-c64-ground8-20260927 \\
  --out build/compact-bank-c64-selected-read-new \\
  --column 62 --step-ns 100 --temperature 27 --timeout 1800
bash scripts/run-tools.sh python3 scripts/report-bank-far-read.py \\
  --run build/compact-bank-c64-ground8-far-read-20260927
```

For the grid candidate, use `build/compact-bank-c64-ground-grid-20260927`
as the layout, a fresh run directory, and a separate audit `--out` path such as
`simulations/compact-bank-64-ground-grid-read.json`. Do not overwrite controls.

Build and check the distributed return:

```sh
bash scripts/run-tools.sh python3 scripts/build-compact-bank.py \\
  --columns 64 --ground-bus-width-um 8 --ground-return-grid \\
  --out build/compact-bank-c64-ground-grid-new
bash scripts/run-tools.sh python3 scripts/audit-bank-ground-grid.py \\
  --original build/compact-bank-c64-ground8-20260927 \\
  --revised build/compact-bank-c64-ground-grid-20260927 \\
  --out build/compact-bank-c64-ground-grid-geometry-new
```

The rails are 24 µm wide, below the installed PDK's 30 µm unslotted-metal
threshold. Main DRC still excludes density, antenna and cup checks; no release
qualification is implied. The ground-plate connection location is specific to
the verified compact 40 µm-pitch column with 32 × 77.76 µm MIM plates.

Reference-generator regression:

```sh
bash scripts/run-tools.sh python3 scripts/test-bank-probe-references.py \\
  --layout build/compact-bank-c16-ground8-20260927 \\
  --run build/compact-bank-c16-ground8-nominal-20260927 \\
  --run build/compact-bank-c16-ground8-patterns-20260927/inverse-125
bash scripts/run-tools.sh python3 scripts/render-bank-read-probes.py
python3 scripts/update-overview-sections.py
```

All 96 generated decks match the archived reference decks exactly. The readout
wrapper snapshots itself and records the modified schedule explicitly. The
independent auditor reopens all binary traces and DC outputs and checks the
reference clamp voltages and every recorded error. The selected transient has
a 1,800 s watchdog, as does each of its three references.

The complete 64-column schedule, 192 references, nominal/hot illumination,
refinement and placement/corner checks remain open. Bias/supply measurements,
repeated rows, real decoding/drivers, 64×64 assembly and provider release gates
remain necessary. Full-bank and manufacturing qualification flags stay false.

The 12 µs acquisition diagnostic uses the audited ground-grid run as its
source and proves that only the two ACQ falling edges and the include path
change. All three references are solved again at the new sample instants.
It rechecks the raw traces, reference clamp decks, source evidence hashes and
unchanged waveform prefix. Reproduce in a fresh directory:

```sh
bash scripts/run-tools.sh python3 scripts/test-bank-acquisition-deck.py
bash scripts/run-tools.sh python3 scripts/probe-bank-acquisition.py \\
  --out build/compact-bank-c64-grid-acquisition12-new
bash scripts/run-tools.sh python3 scripts/probe-bank-acquisition.py \\
  --out build/compact-bank-c64-grid-acquisition12-new --audit-only
```

Do not silently apply this fixture timing to the full-bank runner. Expose and
regression-check the timing option, then qualify the complete schedule with
its own references, refinement and pattern/corner coverage.
'''
    (ROOT / 'docs/compact-bank-64-read-probes.md').write_text(markdown)
    print('Rendered ' + str(len(results)) + ' selected-read layout control(s).')


if __name__ == '__main__':
    main()
