"""Render dated provider facts and conservative geometry arithmetic for the overview."""
from datetime import datetime
import hashlib
from html import escape
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/'simulations/wafer-space-run3-20260927.json'
    facts=json.loads(source.read_text())
    bankfile=ROOT/'build/compact-bank-c64-v1-20260926/verification.json'
    bank=json.loads(bankfile.read_text())
    cfg=json.loads((ROOT/'layout/64x64-floorplan-budget.json').read_text())
    x0,y0,x1,y1=map(float,re.findall(r'-?\d+(?:\.\d+)?',bank['bbox_um']))
    size=[x1-x0,y1-y0];array=[64*40,64*40]
    def fits(a,b):return (a[0]<=b[0] and a[1]<=b[1]) or (a[1]<=b[0] and a[0]<=b[1])
    slots=[]
    for s in facts['slots']:
        slots.append(dict(**s,array_fits_core=fits(array,s['core_um']),array_fits_inside_seal=fits(array,s['inside_seal_um'])))
    assert [s['name'] for s in slots if s['array_fits_core']]==['Full']
    assert [s['name'] for s in slots if s['array_fits_inside_seal']]==['Full']
    full=slots[-1];cw,ch=full['core_um']
    assert cfg['default_core_um']==full['core_um']
    blocks=dict(cfg['candidate_blocks_um']);blocks['capture_bank_budget']=[200,2760,*size]
    for name,(x,y,w,h) in blocks.items():assert 0<=x and 0<=y and x+w<=cw and y+h<=ch,name
    pairs=list(blocks.items())
    for i,(name,(x,y,w,h)) in enumerate(pairs):
        for other,(xx,yy,ww,hh) in pairs[i+1:]:
            assert x+w<=xx or xx+ww<=x or y+h<=yy or yy+hh<=y,(name,other)
    reserved=sum(w*h for x,y,w,h in blocks.values())/1e6
    report=dict(checked_on=facts['checked_on'],source_facts_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        bank_verification_sha256=hashlib.sha256(bankfile.read_bytes()).hexdigest(),
        slots=slots,array_um=array,actual_joined_bank_um=size,conservative_blocks_um=blocks,
        core_area_mm2=cw*ch/1e6,reserved_area_mm2=reserved,remaining_area_mm2=cw*ch/1e6-reserved,
        scope='Conservative nonoverlapping block reservation only; bank includes one pixel row. Exact assembly must add 63 rows, not duplicate a 65th row.',
        complete_chip_fit_verified=False)
    (ROOT/'simulations/wafer-space-fit-20260927.json').write_text(json.dumps(report,indent=2)+'\n')
    def mm(pair):return ' × '.join(f'{v/1000:.3f}' for v in pair)
    rows=''.join(f'<tr><th>{s["name"]}</th><td>{mm(s["die_um"])}</td><td>{mm(s["core_um"])}</td><td>${s["early_usd"]:,} / ${s["standard_usd"]:,}</td><td>{"Candidate" if s["array_fits_core"] else "Does not fit"}</td></tr>' for s in slots)
    dates=''.join(f'<tr><th>{label}</th><td>{datetime.fromisoformat(facts["deadlines_aoe"][key]).strftime("%d %B %Y, %H:%M")} AoE</td><td>{datetime.fromisoformat(facts["deadlines_aoe"][key]).astimezone(ZoneInfo("America/Los_Angeles")).strftime("%d %B %Y, %H:%M %Z")}</td></tr>' for key,label in [('early_bird','Early bird'),('purchase','Purchase'),('clean_gds','Clean GDS')])
    svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 530" role="img" aria-label="Conservative array, bank and row-driver reservations inside the full-slot default core">
<rect width="960" height="530" fill="#f3f7fa"/><g font-family="system-ui,sans-serif" fill="#182c3b">
<text x="40" y="30" font-size="19">Default core: 3.048 × 4.238 mm</text>
<rect x="40" y="50" width="304.8" height="423.8" fill="#e0e7ec" stroke="#182c3b"/>
<rect x="75" y="60" width="256" height="256" fill="#bddbf7" stroke="#21628d"/>
<text x="99" y="180" font-size="17">64 × 64 pixel reserve</text><text x="99" y="205" font-size="16">2.560 × 2.560 mm</text>
<rect x="50" y="60" width="15" height="256" fill="#ffe09a" stroke="#977323"/>
<rect x="60" y="326" width="262.776" height="97.828" fill="#a6e3c7" stroke="#267055"/>
<text x="76" y="360" font-size="16">Actual joined 1 × 64 bank</text><text x="76" y="386" font-size="16">2.628 × 0.978 mm</text>
<text x="410" y="95" font-size="20">A full slot is the viable planning size.</text>
<text x="410" y="133" font-size="16">Quarter and half slots fail even before adding readout.</text>
<text x="410" y="165" font-size="16">Yellow: 150 µm row-driver reservation.</text>
<text x="410" y="197" font-size="16">Gray: routing, references, controls and margins.</text>
<text x="410" y="245" font-size="16">The bank includes one pixel row.</text>
<text x="410" y="275" font-size="16">Final assembly must add 63 more rows.</text>
<text x="410" y="323" font-size="16">Block positions are a budget, not routed full-chip GDS.</text>
<text x="410" y="353" font-size="16">Pad-map changes require core dimensions to be rechecked.</text>
<text x="40" y="508" font-size="14">27 September 2026 · Actual bank bounds; conservative array reservation · No full-chip fit or tapeout pass claimed</text>
</g></svg>'''
    html=f'''<section id="wafer-space-run3"><h2>wafer.space Run 3: dates, cost and die fit</h2>
<p><strong>Checked 27 September 2026. Plan around a full slot; no slot has been reserved.</strong> Run 3 is the next published offering found. Parts are scheduled for Q2 2027. A later run date has not been established.</p>
<table><thead><tr><th>Milestone</th><th>Provider deadline</th><th>Los Angeles time</th></tr></thead><tbody>{dates}</tbody></table>
<p>Source: <a href="{facts['schedule_source']}">provider milestone table</a>, corroborated by the <a href="{facts['schedule_corroboration']}">provider GitHub profile</a>. The campaign funding widget says 19 December and the homepage has contradictory expired-countdown text; neither should replace the explicit submission timetable.</p>
<p class="note">The <a href="{facts['availability_source']}">19 September availability update</a> reports few full slots remaining. Inventory and the final checkout price need confirmation before an order. Readiness for the December deadline remains unproven.</p>
<h3>Fabrication budget: USD per batch of 1,000 dies</h3>
<div style="overflow-x:auto"><table><thead><tr><th>Slot</th><th>Die, mm</th><th>Default core, mm</th><th>Early / standard</th><th>Our 64² array</th></tr></thead><tbody>{rows}</tbody></table></div>
<p><a href="{facts['pricing_source']}">Published prices</a> are $7,000 early / $8,000 standard for the full slot. The $1,500 chip-on-board option makes those totals <strong>$8,500 / $9,500</strong>, conditional on packaging suitability. The <a href="{facts['campaign_source']}">campaign</a> includes worldwide shipping but assigns insurance and tariffs to the buyer. Taxes where applicable, optics, ADC/controller boards, characterization and custom optical packaging are not priced here.</p>
<p>The default pad ring is required for the chip-on-board option. Its optical access and encapsulation are unconfirmed; this sensor needs light to reach its junctions. Do not assume standard encapsulation is suitable. Bare dies leave bonding and handling costs unresolved.</p>
<h3>Die outline, seal-ring interior and usable core are different</h3>
<p>The <a href="{facts['dimensions_source']}">template dimensions</a> give a full die of 3.932 × 5.122 mm, an inside-seal region of 3.880 × 5.070 mm, and a default core of 3.048 × 4.238 mm ({report['core_area_mm2']:.3f} mm²). Dimensions were generated 4 June and checked today. The campaign's 3.88 × 5.07 mm product description refers to the inside-seal region, not the default core.</p>
{svg}
<p>At 40 µm pitch, 64² pixels reserve 6.554 mm². The actual joined bank uses {size[0]*size[1]/1e6:.3f} mm². Including the 0.384 mm² row-driver reservation leaves <strong>{report['remaining_area_mm2']:.3f} mm²</strong> of the default core unreserved. This arithmetic checks block bounds and nonoverlap only. The bank already includes one row: a final 4096-pixel assembly must add 63 rows and verify the exact device census. A half-height slot has only 2.479 mm inside the seal in its short dimension, less than the 2.560 mm array; changing the pad ring alone cannot fix that.</p>
<h3>Release gates still required</h3>
<p><strong>Process-stack check, 27 September:</strong> the <a href="https://wafer.space/technology.html">provider technology page</a> advertises five metal layers and MIM/MOS capacitors. Its <a href="https://github.com/wafer-space/gf180mcu-precheck/blob/main/precheck.py">precheck code</a> requires <code>gf180mcuD</code>; the <a href="https://github.com/wafer-space/gf180mcu-precheck/blob/main/Makefile">current Makefile</a> selects PDK commit <code>d658698bd8bcf4e05fc7b5991a701247ba0d744c</code>. This identifies a provider verification target, but does not establish approval of our exact MIM option, optical openings or packaging. Our installed metadata declares <code>MIM_2P0</code>/<code>METAL5</code> and open_pdks commit <code>b344c97eacc2aaf8e14ae7e43e2e9dc0871de2c0</code>; equivalence to that provider target is not established. See the <a href="../simulations/wafer-space-pdk-review-20260927.json">dated PDK comparison</a>. Reconcile the installed PDK and rerun the exact-chip provider checks before submission.</p>
<p>The fit illustration retains the original 2.628 × 0.978 mm bank as a dated baseline. The newer <a href="#compact-bank-64-read-probes">distributed ground-return candidate</a> is 2.668 × 1.070 mm and remains within the same 2.700 × 1.100 mm bank reservation. Recheck the final assembled chip rather than treating either block budget as a complete-chip fit.</p>
<ol><li>Qualify the physical 64-column bank with matched references, nominal/hot patterns, timestep refinement, shunt placements and supply/reference drops.</li><li>Add real row/column decoding and drivers; test repeated rows with the full 64-pixel column load.</li><li>Assemble and route the exact 64×64 chip, pad ring and power grid; verify ADC loading, startup and repeated frames.</li><li>Close the run-specific PDK/MIM, optical-access, DRC/LVS/ERC, density/antenna, pad/bond-map and provider precheck gates.</li></ol>
<p>The <a href="https://github.com/wafer-space/gf180mcu-precheck">provider precheck</a> checks the top cell, origin/grid, slot bounds, metal limit, density, antenna and Magic/KLayout DRC. CoB adds template identifiers and pad-opening checks. Our block-level main DRC/LVS passes do not replace that exact-chip review.</p>
<p><a href="../simulations/wafer-space-run3-20260927.json">Dated source facts</a> · <a href="../simulations/wafer-space-fit-20260927.json">Reproducible fit arithmetic</a> · <a href="../COMPLETION_PLAN.md">Completion plan</a></p></section>'''
    current_fit=ROOT/'simulations/wafer-space-current-bank-fit-20260927.json'
    if current_fit.exists():
        fit=json.loads(current_fit.read_text())
        assert fit['rectangles_fit'] and not fit['complete_chip_fit_verified']
        margin=fit['bank_reservation_margin_um']
        current_html=f'''<p><strong>Updated ground-grid budget:</strong> the current bank occupies {fit['bank_area_mm2']:.3f} mm², leaving {margin[0]:.2f} µm width and {margin[1]:.2f} µm height inside its allocation. With the full array and row-driver reservations, {fit['unreserved_area_mm2']:.3f} mm² remains unreserved. This space is fragmented; it does not establish routing or macro-placement feasibility. <a href="../simulations/wafer-space-current-bank-fit-20260927.json">Current bounding-box arithmetic and hashes</a>.</p>'''
        html=html.replace('<ol><li>Qualify the physical 64-column bank',current_html+'<ol><li>Qualify the physical 64-column bank')
    reconciliation=ROOT/'simulations/wafer-space-pdk-reconciliation-20260927.json'
    if reconciliation.exists():
        pdk=json.loads(reconciliation.read_text())
        pdk_html=f'''<h3>Provider-pinned source reconciliation</h3>
<p>The <a href="https://github.com/fossi-foundation/open-pdks/blob/d658698bd8bcf4e05fc7b5991a701247ba0d744c/gf180mcu/Makefile.in">pinned build configuration</a> selects five metals, 1.1 µm top metal and MIM between the top two metals; its <a href="https://github.com/fossi-foundation/open-pdks/blob/d658698bd8bcf4e05fc7b5991a701247ba0d744c/gf180mcu/gf180mcu.json">node template</a> declares 2 fF/µm² MIM. These declared options align with our M4/M5 storage capacitors. Exact tree comparison finds unchanged GF180 build/extraction sources apart from dependency metadata. The primitive-library update changes only a KLayout GUI macro; device-model sources are unchanged.</p>
<p>The provider-default verification library has 47 changed files, including test fixtures. Running that pinned main DRC source against the unchanged ground-grid bank reports <strong>{pdk['block_main_drc_errors']} violations</strong>. This uses the installed KLayout executable and excludes density, antenna and cup. It does not replace exact-chip origin/size/ID/pad checks, complete provider precheck, LVS/ERC, fill/extraction or optical-packaging review.</p>
<p><a href="../simulations/wafer-space-pdk-reconciliation-20260927.json">Source comparison, DRC result and evidence hashes</a> · <a href="wafer-space-pdk-reconciliation.md">Reproduction and scope</a>. Declared options and relevant source alignment are now checked, while full binary/tool equivalence and final-chip release checks remain unproven.</p>'''
        html=html.replace('<h3>Release gates still required</h3>',pdk_html+'<h3>Release gates still required</h3>')
        start=html.index('<p><strong>Process-stack check, 27 September:</strong>')
        end=html.index('</p>',start)+4
        html=html[:start]+'''<p>The <a href="../simulations/wafer-space-pdk-review-20260927.json">earlier PDK-version review</a> is retained as historical evidence. The source reconciliation above resolves its declared-option and relevant-source questions. Run the exact-chip provider precheck and resolve optical openings, packaging and remaining manufacturing requirements before submission.</p>'''+html[end:]
    (ROOT/'docs/wafer-space-run3-section.html').write_text(html+'\n')
    print(json.dumps({k:report[k] for k in ['actual_joined_bank_um','remaining_area_mm2','complete_chip_fit_verified']},indent=2))


if __name__=='__main__':main()
