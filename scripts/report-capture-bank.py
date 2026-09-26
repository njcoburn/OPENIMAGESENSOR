"""Publish measured shared-bank physical checks and bounded transient status."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import klayout.db as k
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank',type=Path,required=True)
    p.add_argument('--runs',type=Path,nargs='*',default=[])
    p.add_argument('--dc',type=Path,nargs='*',default=[])
    a=p.parse_args();bank=a.bank.resolve()
    physical=json.loads((bank/'verification.json').read_text())
    assert physical['columns']==64 and physical['direct_and_resistor_collapsed_lvs']
    assert physical['magic_drc_errors']==physical['klayout_main_drc_errors']==0
    for name,digest in physical['hashes'].items():
        assert hashlib.sha256((bank/name).read_bytes()).hexdigest()==digest
    runs=[]
    for path in a.runs:
        result=json.loads((path/'result.json').read_text())
        assert result['source_sha256']['bank.spice']==hashlib.sha256((path/'bank.spice').read_bytes()).hexdigest()
        runs.append(dict(path=str(path.relative_to(ROOT) if path.is_absolute() else path),result=result))
    dc=[dict(path=str(path),report=json.loads((path/'report.json').read_text())) for path in a.dc]
    ly=k.Layout();ly.read(str(bank/'bank.gds'));top=ly.cell('capture_bank')
    fig=plt.figure(figsize=(13,6),layout='constrained')
    grid=fig.add_gridspec(2,2,width_ratios=[1,2])
    axes=[fig.add_subplot(grid[0,:]),fig.add_subplot(grid[1,0])]
    chart=fig.add_subplot(grid[1,1])
    colors=[((42,0),'#a06b35','M3'),((46,0),'#3c8b8a','M4'),((81,0),'#647ec9','M5'),((75,0),'#cf765c','MIM plates')]
    for ax in axes:
        for layer,color,label in colors:
            region=k.Region(top.begin_shapes_rec(ly.layer(*layer))).merged()
            # Each polygon's hull is sufficient here: narrow contact holes are
            # below plot resolution. The archived GDS is the geometry authority.
            polys=[[(p.x*ly.dbu,p.y*ly.dbu) for p in poly.each_point_hull()] for poly in region.each()]
            ax.add_collection(PolyCollection(polys,facecolors=color,edgecolors='none',label=label,alpha=.8))
        ax.set_aspect('equal');ax.set_xlabel('x (µm)');ax.set_ylabel('y (µm)')
    axes[0].set(xlim=(-100,5130),ylim=(-205,700),title='64-column bank: 450 MOS devices and 512 physical storage plates')
    axes[0].legend(loc='upper right',ncol=4,fontsize=8)
    for layer,color in [((34,0),'#724267'),((36,0),'#357267')]:
        region=k.Region(top.begin_shapes_rec(ly.layer(*layer))).merged()
        polygons=[[(p.x*ly.dbu,p.y*ly.dbu) for p in poly.each_point_hull()] for poly in region.each()]
        axes[1].add_collection(PolyCollection(polygons,facecolors=color,edgecolors='none'))
    axes[1].set(xlim=(-90,180),ylim=(-195,135),title='References and supply feeds')
    curves={}
    for screen in dc:
        for row in screen['report']['comparisons']:
            if row['temperature_C']==27 and row['input_V']>0:curves[row['input_V']]=row
    for level,row in sorted(curves.items()):
        chart.plot(range(64),[v*1e3 for v in row['buffer_shifts_V']],label=f'{level:g} V input')
    chart.axhline(0,color='#888',lw=.8);chart.grid(alpha=.2)
    chart.set(xlabel='Column',ylabel='Physical − ideal buffer (mV)',title='Static shared-bank shift at 27 °C')
    if curves:chart.legend(fontsize=8)
    image=ROOT/'docs/assets/capture-bank.png';fig.savefig(image,dpi=160);plt.close(fig)
    summary=dict(selected_layout=str(bank.relative_to(ROOT)),physical=physical,
                 runs=runs,isolated_dc_screens=dc,full_readout_accuracy_qualified=False,
                 scope='Physical standalone bank verified; coupled row uses ideal terminal links. Full capture/output accuracy, numerical and capacitance-placement qualification remain open.')
    (ROOT/'simulations/capture-bank.json').write_text(json.dumps(summary,indent=2)+'\n')
    affected=physical['negative_shunt_approximations']
    rows=[]
    for run in runs:
        r=run['result'];kind='DC operating point' if r['op_only'] else f"{r['step_ns']:g} ns, {r['stop_ms']:g} ms transient"
        setup=r.get('solver','sparse')+(' + nodesets' if r.get('nodeset_initial_guesses') else '')
        rows.append(f"| {r['model']}, {r['temperature_C']:g} °C, {setup} | {kind} | {'Complete' if r['completed'] else 'Incomplete'} | {len(r.get('samples',[]))} | {r.get('last_time_s',0)*1e3:.6f} |")
    table='\n'.join(rows)
    dcrows=[]
    for screen in dc:
        for result in screen['report']['results']:
            dcrows.append(f"| {result['solver']} | {result['model']} | {result['temperature_C']} | {result['input_V']:g} | {'Complete' if result['completed'] else 'Incomplete'} |")
    dctable='\n'.join(dcrows)
    comparisons={}
    for screen in dc:
        for row in screen['report']['comparisons']:
            comparisons[row['temperature_C'],row['input_V']]=row
    shift_table='\n'.join(f"| {t} | {v:g} | {r['max_buffer_shift_V']*1e3:.3f} | {r['physical_buffer_span_V']*1e3:.3f} |"
        for (t,v),r in sorted(comparisons.items()))
    complete=sum(r['result']['completed'] and not r['result']['op_only'] for r in runs)
    md=f'''# Shared physical capture bank — 2026-09-25

**The 64-column bank passes Magic/KLayout main DRC and both direct and
resistor-collapsed LVS.** Its {physical['mos']} MOS devices and
{physical['mim_devices']} MIM plates match the schematic contract exactly.
Full readout accuracy is not yet qualified.

![Physical bank layout and supply detail](assets/capture-bank.png)

## Physical implementation

The qualified isolated column is repeated at 80 µm pitch. Shared capture clocks,
BIAS/PREF reference lines and output bus use 4 µm M4 routing. Each supply uses
five parallel 8 µm M5 straps, joined by M4 crossbars and distributed 3×3 vias.
The two shared reference transistors are placed once to the left of the bank.
External 500 kΩ/12.4 kΩ bias resistors remain fixture components.

The extent is 5.198 × 0.86504 mm (4.49648 mm²) including routing and references.
All 512 storage plates retain separate M4 bottom islands. Their individual
64 × 38.88 µm areas match the conditional 2 fF model. No manufacturing capacitor
option is selected. The two-column control also passes both DRC/LVS paths.
The first control's unslotted 40 µm straps failed KLayout MSLOT5.1 (seven
markers); that rejected layout and its reports are retained.

## Extracted model

All 327 bank ports remain distinct and connected to their expected devices.
The raw extraction retains **{physical['resistors']:,} resistors** and
**{physical['parasitic_capacitors']:,} parasitic capacitors**, in addition to the
512 modeled MIM devices. Every resistor has positive resistance, and shorting
only those resistors reproduces the independent schematic devices and terminals.

Raw Magic capacitance corrections contain {len(physical['negative_parasitic_capacitors'])}
negative substrate shunts across {len(affected)} nets. Derived near/far diagnostic
models preserve every resistor and each affected net's total shunt capacitance,
placing that total at either the port or the furthest node by shortest resistive
path. **Their placement sensitivity is not qualified.** This shared-bank
approximation needs its own test; the earlier isolated-column result does not
establish it. Raw extraction is archived without modification.

Magic's global substrate-capacitance node 0 is explicitly bound to the bank GND
feed in derived models. Ground-routing resistors remain present; substrate
spreading resistance is not modeled. Shortest resistive path lengths in the
machine-readable report are topology measurements, not effective network
resistances or supply-droop predictions.

## Coupled row diagnostics

The new runner replaces all 450 schematic peripheral MOS devices and 64 ideal
storage capacitors with one physical bank instance. It keeps the accepted row's
4,378 resistors, 2,353 capacitors, 256 pixel devices, stimulus, ADC loading,
500 kΩ/12.4 kΩ fixture and solver tolerances. Physical reference MOS devices
are included once. The fixture retains 100 Ω behavioral control drivers,
2 Ω supply impedance, 100 pF board and 20 pF sample loads.

Row and bank connect at ideal COL/supply terminals: joining routes have not
been placed or extracted. These are two extracted blocks electrically coupled,
not a completed physical camera tile.

| Condition | Requested analysis | Status | Readout samples | Last transient time (ms) |
|---|---|---|---:|---:|
{table}

Completed transient runs: {complete}. A completed trace alone is not a 500 µV
accuracy pass. Independent capture/output references, all 64 sample/control
checks, nominal/hot refinement and near/far placement comparisons remain open.
Incomplete runs retain exact decks, logs and available trace records and are
excluded from qualification. See `simulations/capture-bank.json` for precise
status, errors and measurements.

The unseeded SPARSE transient completes transient-assisted initialization and
then slows sharply near the 0.2 ms reset-release edge, before the 1.4 ms capture.
The watchdog keeps it incomplete. Shorter standalone coupled operating-point
controls also time out. The seeded KLU control aborts because it cannot create
a required matrix element for a nodeset; it is excluded, not a circuit failure.
No solver accuracy tolerance was relaxed, and no full readout sample is claimed.
An independent audit reads back all 16 static raw results, confirms direct DC
convergence without transient fallback for those isolated controls, verifies
retention of every bank resistor in both placement models, and checks the
unchanged coupled source/load/control/tolerance lines.

The isolated DC control imposes the same voltage on all 64 COL inputs, holds
capture on and selects only output 0. Its 1 TΩ output load and ideal input
sources make it a bank-only static diagnostic. The reference uses identical
physical capacitor devices and ideal wiring. It cannot replace camera accuracy
or switching/retention checks.

| Solver | Model | Temperature (°C) | COL input (V) | DC status |
|---|---|---:|---:|---|
{dctable}

Independent completed pairs report all 64 buffer-voltage shifts and the
equal-input spatial spread in `simulations/capture-bank.json`. Timeouts are
numerical/runtime outcomes, not demonstrated hardware failures.

| Temperature (°C) | Imposed COL (V) | Largest physical–ideal buffer shift (mV) | Equal-input buffer spread (mV) |
|---|---:|---:|---:|
{shift_table}

These millivolt-scale static differences require shared power/reference routing
investigation. They are neither matched transient tracking errors nor an
established camera calibration/noise result. Zero input is a reset-state
diagnostic, outside the earlier 1.2–2.0 V isolated-column input screen.

## Next and reproduction

Investigate the shared power/reference contribution to the static spatial
spread and isolate coupled-bank reset-edge/runtime behavior before extending
the qualification. Nodeset diagnostics use only Newton initial guesses from
completed bank/row controls, without changing equations or tolerances; they do
not qualify power-up or select a unique operating point.
Then compute independent capture targets and all 64 matched output references,
repeat 27/125 °C and timestep/placement checks under the retained 500 µV output
and 10 µV numerical limits. Route the row-to-bank links, then test repeated and
multirow captures and real control drivers. Wire/process corners, startup,
noise, pads/fill/manufacturing gates and frame-rate selection remain open.

Selected layout: `{bank.relative_to(ROOT)}`. Use fresh output directories:

```sh
bash scripts/run-tools.sh python3 scripts/build-capture-bank.py \\
  --columns 64 --out build/capture-bank-reproduce
bash scripts/run-tools.sh bash -lc 'cd build/capture-bank-reproduce && klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc -rd input=bank.gds -rd report=main-drc.lyrdb -rd topcell=capture_bank -rd variant=gf180mcuD -rd decks=all,-antenna,-density,-cup -rd threads=2 > klayout.log 2>&1'
bash scripts/run-tools.sh python3 scripts/verify-capture-bank.py \\
  --run build/capture-bank-reproduce
bash scripts/run-tools.sh python3 scripts/simulate-capture-bank.py \\
  --bank build/capture-bank-reproduce --out build/capture-bank-new-run \\
  --temperature 27 --step-ns 200 --timeout 600
```

Main DRC excludes antenna, density and CUP. This development bank is unfilled
and contains no optical array. No release GDS, carrier, commit or push changed.
Evidence and failed controls are retained in `checkpoints/capture-bank/`.
'''
    (ROOT/'docs/capture-bank.md').write_text(md)
    section=f'''<section id="capture-bank"><h2>Shared physical capture bank</h2><p>The 64-column bank passes both main DRC checks and both LVS paths: 450 MOS devices, 512 MIM plates, {physical['resistors']:,} extracted resistors. Full coupled-row accuracy and capacitance-placement qualification remain open.</p><img alt="Physical 64-column bank and shared supply detail" style="max-width:100%" src="data:image/png;base64,{base64.b64encode(image.read_bytes()).decode()}"><p><a href="capture-bank.md">Measurements, diagnostic status and reproduction</a>.</p></section>'''
    (ROOT/'docs/capture-bank-section.html').write_text(section+'\n')
    print(json.dumps(dict(layout=summary['selected_layout'],complete_transients=complete,physical_checks_pass=True)),flush=True)


if __name__=='__main__':main()
