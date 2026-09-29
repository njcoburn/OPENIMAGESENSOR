"""Render the audited refinement/placement extension in the engineering notebook."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    r = json.loads((ROOT / 'simulations/compact-bank-16-extension.json').read_text())
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), layout='constrained', gridspec_kw={'width_ratios': [1, 1.2]})
    patterns = ['alternating', 'inverse', 'dark', 'middle', 'bright']
    for offset, temperature, color in [(-.18, 27, '#236a91'), (.18, 125, '#b75423')]:
        values = [next(x['terminals']['max_uV'] for x in r['refinement'] if x['temperature_C'] == temperature and x['pattern'] == pattern)
                  for pattern in patterns]
        axes[0].scatter(values, np.arange(5) + offset, label=f'{temperature} °C', color=color, s=40)
    axes[0].set(yticks=np.arange(5), yticklabels=patterns, title='100 → 50 ns: all saved terminals', xlabel='Largest sampled change (µV)')
    axes[0].invert_yaxis()
    axes[0].legend(loc='lower right')
    places = sorted(r['placement'], key=lambda p: (20 if len(p['nets']) > 1 else
                    (['BIAS'] + [f'COL{c}' for c in range(16)] + ['SC', 'SCB']).index(p['nets'][0])))
    labels = ['all jointly' if len(p['nets']) > 1 else p['nets'][0] for p in places]
    axes[1].scatter([p['hold']['max_uV'] for p in places], np.arange(20) - .18, label='HOLD', color='#236a91', s=25)
    axes[1].scatter([p['stores']['max_uV'] for p in places], np.arange(20) + .18, label='STORE', color='#b75423', s=25)
    axes[1].set(yticks=np.arange(20), yticklabels=labels, title='Placement: inverse pattern, 125 °C', xlabel='Largest sampled change (µV)')
    axes[1].invert_yaxis()
    axes[1].legend(loc='lower right')
    for axis in axes:
        axis.axvline(10, color='#a12424', ls='--', lw=1.5, label='10 µV limit')
        axis.set_xscale('log')
        axis.grid(axis='x', alpha=.2)
    fig.suptitle('Revised 16-column bank: selected numerical and placement checks\nDashed line: 10 µV comparison limit', fontsize=13)
    fig.savefig(ROOT / 'docs/assets/compact-bank-16-extension.png', dpi=160)
    plt.close(fig)
    outcome = 'passes' if r['selected_screen_pass'] else 'fails'
    fine_max = max(x['terminals']['max_uV'] for x in r['refinement'])
    hold_max = max(x['hold']['max_uV'] for x in r['placement'])
    store_max = max(x['stores']['max_uV'] for x in r['placement'])
    schematic_max = max(x['physical_schematic_output_difference']['max_uV'] for x in r['schematic'])
    schematic_fine = max(x['terminals']['max_uV'] for x in r['schematic'])
    accuracy_rows = ''.join(f'<tr><td>{x["temperature_C"]:g}</td><td>{x["pattern"]}</td><td>{x["model"]}</td><td>{x["step_ns"]:g}</td><td>{x["total_error_uV"]:.3f}</td><td>{x["tracking_error_uV"]:.3f}</td></tr>'
                            for x in sorted(r['rows'], key=lambda x: (x['model'], x['temperature_C'], x['pattern'], -x['step_ns'])) if x['references'])
    placement_rows = ''.join(f'<tr><td>{"all jointly" if len(x["nets"]) > 1 else x["nets"][0]}</td><td>{x["hold"]["max_uV"]:.6f}</td><td>{x["stores"]["max_uV"]:.6f}</td></tr>' for x in places)
    schematic_rows = ''.join(f'<tr><td>{x["temperature_C"]}</td><td>{x["terminals"]["max_uV"]:.3f}</td><td>{x["physical_schematic_output_difference"]["max_uV"]:.3f}</td><td>{x["physical_schematic_store_difference"]["max_uV"]:.3f}</td></tr>' for x in r['schematic'])
    html = f'''<section id="compact-bank-16-extension"><h2>16-column continuation: refinement and individual shunt placement</h2>
<p><strong>The revised bank {outcome} this selected extension.</strong> Thirty-two new transients and 576 independent references bring the combined screen to <strong>46 transients and 1,152 references</strong>. Worst total capture/readout error is {r['max_total_error_uV']:.3f} µV and worst output tracking is {r['max_tracking_error_uV']:.3f} µV, each checked against 500 µV. The 8 µm ground-bus layout and strict simulator tolerances are unchanged.</p>
<p>Every physical illumination pattern now has paired 100/50 ns runs at 27 and 125 °C: alternating, inverse, uniform dark, middle and bright. The largest change across all saved terminals at the readout instants is <strong>{fine_max:.3f} µV</strong>, below the 10 µV comparison limit. Contrast and brightness ordering are rechecked at both timesteps.</p>
<figure><img src="assets/compact-bank-16-extension.png" alt="Timestep changes for five illumination patterns and individual shunt placement changes for the hot inverse pattern"><figcaption>The placement extension uses the previous screen's highest-error case, inverse 240/0 pA at 125 °C. It does not cover every pattern and temperature.</figcaption></figure>
<p>All 19 shunt totals (BIAS, COL0–COL15, SC and SCB) are moved individually, followed by a joint far-placement comparison. Each model is checked line by line: only the intended shunt endpoint changes; capacitance totals and every resistor/device are retained. Largest sampled differences are <strong>{hold_max:.3f} µV at HOLD</strong> and <strong>{store_max:.3f} µV across STORE0–STORE15</strong>, against 10 µV.</p>
<details><summary>All hot inverse placement comparisons</summary><table><thead><tr><th>Moved net</th><th>HOLD change, µV</th><th>Largest STORE change, µV</th></tr></thead><tbody>{placement_rows}</tbody></table></details>
<h3>Schematic comparison: inverse pattern at both temperatures</h3>
<p>Four schematic controls add 100/50 ns pairs and their own 48 independent references each. Their largest timestep change is {schematic_fine:.3f} µV. Comparing the physical and schematic 50 ns outputs gives up to <strong>{schematic_max / 1000:.3f} mV</strong> difference. This measures model-dependent integrated response; it is separate from same-state capture/readout accuracy and has no assigned acceptance threshold.</p>
<table><thead><tr><th>Temperature, °C</th><th>Schematic timestep, µV</th><th>Layout–schematic HOLD, µV</th><th>Layout–schematic STORE, µV</th></tr></thead><tbody>{schematic_rows}</tbody></table>
<details><summary>Combined physical and schematic accuracy results</summary><div style="overflow-x:auto"><table><thead><tr><th>°C</th><th>Pattern</th><th>Model</th><th>Step, ns</th><th>Total error, µV</th><th>Tracking, µV</th></tr></thead><tbody>{accuracy_rows}</tbody></table></div></details>
<p>The audit verifies all {r['prior_evidence_files_verified']:,} prior evidence hashes, reopens every combined transient and DC result, checks the frozen pixel/storage voltages in the reference decks, and recomputes sample errors. Corruption controls reject altered samples, missing scan samples, false reference values, relabelled accuracy and unintended circuit edits. New evidence hashes chain to the unchanged prior report.</p>
<p class="note"><strong>Still open:</strong> placement at the other pattern/temperature combinations; the other schematic patterns; process, wire and supply corners; and the remaining local supply/reference-drop checks. Real drivers/decoding, repeated rows, the corrected 64-column bank and assembled 64×64 release checks remain ahead. This selected extension is not full 16-column or tapeout qualification.</p>
<p><a href="../simulations/compact-bank-16-extension.json">Audit, results and evidence hashes</a> · <a href="compact-bank-16-extension.md">Reproduction and next steps</a> · <a href="#compact-bank-16-screen">Earlier thermal/pattern screen</a> · <a href="#wafer-space-run3">Run 3 schedule, price and die fit</a></p></section>'''
    (ROOT / 'docs/compact-bank-16-extension-section.html').write_text(html + '\n')
    print(json.dumps(dict(outcome=outcome, refinement_uV=fine_max, placement_hold_uV=hold_max,
                          placement_store_uV=store_max, schematic_output_difference_uV=schematic_max), indent=2))


if __name__ == '__main__':
    main()
