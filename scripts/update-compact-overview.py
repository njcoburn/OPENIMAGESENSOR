"""Refresh the current overview sections from the verified compact-bank report.

Uses only the standard library; preserves the existing historical notebook.
The full overview builder also reads the generated section.
"""
from pathlib import Path
import base64
import html
import json
import re

ROOT=Path(__file__).resolve().parents[1]


def main():
    report=json.loads((ROOT/'simulations/compact-bank.json').read_text())
    physical=report['physical'];electrical=report['electrical'];m=report['maxima']
    assert electrical['all_checks_pass'] and physical['direct_and_resistor_collapsed_lvs']
    assert physical['magic_drc_errors']==physical['klayout_main_drc_errors']==0
    assert physical['gds_sha256']==electrical['layout_gds_sha256']
    picture='data:image/png;base64,'+base64.b64encode((ROOT/'docs/assets/compact-bank.png').read_bytes()).decode()
    rows='\n'.join(f'<tr><td>{r["temperature_C"]}</td><td>{r["lights_pA"][0]} / {r["lights_pA"][1]}</td>'
                  f'<td>{r["max_total_capture_readout_error_uV"]:.3f}</td>'
                  f'<td>{r["physical_timestep_difference_uV"]:.3f}</td>'
                  f'<td>{r["max_output_placement_difference_uV"]:.4f}</td></tr>' for r in electrical['rows'])
    section=f'''<section id="compact-bank"><h2>Latest verified hardware: compact shared two-column bank</h2>
<p><strong>26 September 2026:</strong> two pixels and two capture columns now share physically routed supplies, references, capture controls and output. The small-bank development screen passes. The compact 64-column bank is the next implementation step.</p>
<div class="grid"><div class="card"><strong>{m['max_total_capture_readout_error_uV']:.3f} µV</strong>Worst total capture/readout error; 500 µV limit.</div><div class="card"><strong>{electrical['main_transients']+electrical['placement_transients']} transients</strong>27/125 °C, five illumination patterns, timestep and selected shunt-placement checks.</div><div class="card"><strong>{electrical['dc_references']} references</strong>Independent settled capture and output solves.</div><div class="card"><strong>DRC + LVS pass</strong>Magic/KLayout main DRC and direct/RC-collapsed LVS.</div></div>
<figure><img src="{picture}" alt="Actual compact two-column GDS, with physical reference transistors, shared buses and metal-clear pixel regions"><figcaption>Actual unfilled GDS: 147.76 × 978.28 µm, including both pixels and shared references. The columns retain 40 µm pitch and nominal 40 pF storage. This is a development layout; manufacturing qualification remains open.</figcaption></figure>
<h3>What the shared-bank test establishes</h3>
<p>The extracted circuit contains 22 MOS devices, 16 MIM capacitors, two photodiodes and 293 resistors. It captures both pixels together, deselects and resets them, then reads each retained value twice through the shared output. Dark/dark, dark/bright, bright/dark, medium/medium and bright/bright patterns give the expected brightness order.</p>
<div style="overflow-x:auto"><table><thead><tr><th>Temperature (°C)</th><th>Pixel currents (pA)</th><th>Capture/readout (µV)</th><th>200→100 ns (µV)</th><th>Output placement (µV)</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Worst output tracking is {m['max_output_tracking_error_uV']:.3f} µV. The maximum timestep difference is {m['physical_timestep_difference_uV']:.3f} µV; sampled storage placement sensitivity is {m['max_storage_placement_difference_uV']:.4f} µV. Both numerical limits are 10 µV. Seven selected placements conserve extracted shunt totals; the raw negative-shunt model remains diagnostic.</p>
<p class="note"><strong>Keep the comparisons separate:</strong> the physical and bare schematic integrated responses differ by up to {m['physical_minus_schematic_magnitude_uV']/1000:.3f} mV. Changing one pixel's illumination changes its neighbor's output by up to {m['neighbor_pattern_response_uV']:.3f} µV. These include changes in shared bias, supply and integrated pixel state; they are distinct from same-state capture/readout accuracy.</p>
<h3>Next: compact 1×64, then repeated multirow operation</h3>
<ol><li>Size and route shared supplies, references and output for 64 columns within the 2700 × 1100 µm bank budget.</li><li>Check all 64 physical outputs at 27/125 °C against settled references, then repeat timestep and shunt-placement checks.</li><li>Add real decoding/drivers, repeated row transitions and full-column loading before assembling 64×64.</li></ol>
<p>Only one capture and two reads per column are demonstrated here. Reference resistors, control drivers and the ADC remain external fixtures. Process/wire corners, repeated frames, density/antenna/CUP, selected-run MIM rules, optical access and final-chip release gates remain open.</p>
<p><a href="compact-bank.md">Full report and reproduction</a> · <a href="../simulations/compact-bank.json">Machine-readable results</a> · <a href="../checkpoints/compact-bank/README.md">Evidence inventory</a> · <a href="../NEXT_STEPS.md">Next steps</a></p>
<p class="small">Selected layout: <code>{html.escape(report['selected_layout'])}</code>. Earlier notebook sections below retain their original scope and do not supersede the current 64×64 plan.</p></section>
'''
    (ROOT/'docs/compact-bank-section.html').write_text(section)
    page=ROOT/'docs/overview.html';text=page.read_text()
    text=re.sub(r'<section id="compact-bank">.*?</section>\s*','',text,flags=re.S)
    current=(ROOT/'docs/64x64-first-silicon-section.html').read_text().strip()
    text,count=re.subn(r'<section id="first-silicon-64">.*?</section>',lambda _:current+'\n'+section,text,count=1,flags=re.S)
    assert count==1
    for anchor in ['first-silicon-64','compact-bank']:
        text=re.sub(r'<a href="#'+anchor+r'">.*?</a>','',text)
    text=text.replace('<nav>','<nav><a href="#first-silicon-64">Current 64×64 plan</a><a href="#compact-bank">Compact two-column results</a>',1)
    text=text.replace('A monochrome camera,<br>starting with one pixel.','Building a 64 × 64<br>monochrome image sensor.')
    text=text.replace('GF180MCU · Xschem · ngspice · future gdsfactory layout.','GF180MCU · Xschem · ngspice · Magic · KLayout.')
    page.write_text(text)
    print('Updated compact-bank section and overview from verified results.')


if __name__=='__main__':main()
