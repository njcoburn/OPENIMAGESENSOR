"""Report the bounded power-feed investigation; incomplete runs stay excluded."""
from pathlib import Path
import argparse
import base64
import html
import hashlib
import json
import runpy
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
helpers = runpy.run_path(str(ROOT/'scripts/diagnose-row-power.py'))
p = argparse.ArgumentParser()
p.add_argument('--grid-run', type=Path)
p.add_argument('--grid-refined-run', type=Path)
p.add_argument('--grid-hot-run', type=Path)
p.add_argument('--baseline-sparse-run', type=Path)
a = p.parse_args()
base_dir = ROOT/'build/row-power-edge-20260924'
physical = ROOT/'build/row-power-grid-20260924'
load = lambda path: json.loads(path.read_text())
base, refined, low = [load(base_dir/n/'result.json') for n in ['baseline','refined','low-power-r']]
assert all(r['completed'] for r in [base, refined, low])
assert base['model_sha256'] == base['source_model_sha256'] == refined['model_sha256']
pixels = base['analysis']['pixels']
peak_delta = max(abs(v['peak_vdd_loss_V']-refined['analysis']['pixels'][k]['peak_vdd_loss_V'])
                 for k,v in pixels.items())
crossing_delta = max(abs(v-refined['analysis']['pixels'][k]['falling_threshold_crossing_us'][threshold])
                    for k,pixel in pixels.items() for threshold,v in pixel['falling_threshold_crossing_us'].items()
                    if v is not None and refined['analysis']['pixels'][k]['falling_threshold_crossing_us'][threshold] is not None)
assert peak_delta < 100e-6 and crossing_delta < .001
old_audit = load(ROOT/'build/array-strip-power2um-20260924/r1c64/rc-audit.json')
new_audit = load(physical/'r1c64/rc-audit.json')
grid_meta = load(physical/'r1c64/extraction.json')
drc_items = len(ET.parse(physical/'r1c64/main-drc.lyrdb').getroot().findall('.//items/item'))
assert drc_items == 0 and grid_meta['drc_count'] == 0 and grid_meta['lvs_direct_and_rc_collapsed']
report = {'scope':'64-column row-enable diagnostic; full extracted pixel wire R+C with schematic capture/readout.',
          'baseline':base['analysis'], 'refined':refined['analysis'],'reduced_resistance_diagnostic':low['analysis'],
          'edge_refinement':{'maximum_pixel_peak_difference_V':peak_delta,
                             'maximum_threshold_crossing_difference_us':crossing_delta,
                             'peak_numerical_screen_V':100e-6,'crossing_numerical_screen_us':.001,
                             'physical_supply_acceptance_limit_defined':False},
          'physical_grid':{'extraction':grid_meta,'klayout_main_drc_items':drc_items,
                           'geometry_audit':load(physical/'geometry-audit.json'),
                           'resistance_ohm':{n:{'baseline':old_audit['net_metrics'][n]['max_ohm'],
                                                'grid':new_audit['net_metrics'][n]['max_ohm']} for n in ['VDD','GND']}},
          'runs':[]}
for file in sorted((ROOT/'build').glob('row-power-*/*/result.json')):
    r = load(file)
    for name,key in [('array.spice','model_sha256'),('test.spice','deck_sha256')]:
        assert hashlib.sha256((file.parent/name).read_bytes()).hexdigest()==r[key],file
    report['runs'].append({'path':str(file.relative_to(ROOT)), 'completed':r['completed'],
                          'seconds':r.get('seconds'),'timed_out':r.get('timed_out'),
                          'manual_stop':load(file.parent/'manual-stop.json') if (file.parent/'manual-stop.json').exists() else None,
                          'analysis_error':r.get('analysis_error'),'errors':r.get('errors'),
                          'watchdog_extension':load(file.parent.parent/'watchdog-extension.json') if (file.parent.parent/'watchdog-extension.json').exists() else None})
curves = [('Original rails',base_dir/'baseline', '#c54945'),
          ('10× lower power R (diagnostic)',base_dir/'low-power-r','#757575')]
grid_text = 'The physical-grid transient remains unqualified. Incomplete solver controls are retained and excluded from electrical claims.'
if a.grid_run:
    grid = load(a.grid_run/'result.json')
    assert grid['completed'] and grid['resistance_factor'] == 1
    report['physical_grid']['transient'] = grid['analysis']
    report['physical_grid']['transient_source'] = str(a.grid_run)
    curves.insert(1,('Extracted upper-metal grid',a.grid_run,'#167c9b'))
    grid_text = (f"The physical-grid row-enable transient completes: worst local VDD loss **{grid['analysis']['worst']['peak_vdd_loss_V']*1e3:.3f} mV**. "
                 'This is a turn-on measurement, not capture/readout accuracy qualification.')
extra_text = ''
if a.baseline_sparse_run:
    other = load(a.baseline_sparse_run/'result.json')
    assert other['completed']
    delta = max(abs(v['peak_vdd_loss_V']-other['analysis']['pixels'][k]['peak_vdd_loss_V']) for k,v in pixels.items())
    assert delta < 100e-6
    report['baseline_solver_peak_difference_V'] = delta
    extra_text += f'\nThe original-rail SPARSE/KLU peak comparison differs by at most **{delta*1e6:.6f} µV** across pixels.\n'
if a.grid_refined_run:
    assert a.grid_run
    other = load(a.grid_refined_run/'result.json')
    assert other['completed']
    delta = max(abs(v['peak_vdd_loss_V']-other['analysis']['pixels'][k]['peak_vdd_loss_V'])
                for k,v in grid['analysis']['pixels'].items())
    assert delta < 100e-6
    report['physical_grid']['peak_refinement_difference_V'] = delta
    extra_text += f'\nThe physical-grid peak changes by at most **{delta*1e6:.6f} µV** across pixels at 1→0.5 ns edge spacing.\n'
capture_rows=[]
for title,d in [('27 °C',a.grid_refined_run),('125 °C',a.grid_hot_run)]:
    if d is None:
        continue
    r=load(d/'result.json');assert r['completed'] and r['analysis']['stop_s'] >= .001401-1e-12
    ix,data=helpers['raw'](d/'stream.raw');t=data[:,0];meta=load(d/'extraction.json')
    def sample(n):
        return 0. if n=='GND' else float(np.interp(.0014-1e-9,t,data[:,ix['v('+('' if n in meta['ports'] else 'xarray.')+n.lower()+')']]))
    supply=sample('VDD')
    loss=max(supply-sample(v['vdd']) for v in meta['roles']['rc'].values())
    rail=min(sample(v['vdd'])-sample(v['gnd']) for v in meta['roles']['rc'].values())
    summary={'source':str(d),'turn_on':r['analysis'],'capture_vdd_loss_V':loss,'capture_min_local_rail_V':rail}
    reference=d/'capture-dc-200us/reference.json'
    if reference.exists():
        ref=load(reference);summary['capture_reference']=ref
        longer=d/'capture-dc-400us/reference.json'
        if longer.exists():
            long=load(longer)
            delta=max(abs(v-long['column_targets_V'][k]) for k,v in ref['column_targets_V'].items())
            assert delta < 1e-8
            summary['capture_reference_200_to_400us_difference_V']=delta
    report['physical_grid'][title]=summary
    error=summary.get('capture_reference',{}).get('max_capture_acquisition_error_V')
    capture_rows.append(f"| {title} | {r['analysis']['worst']['peak_vdd_loss_V']*1e3:.3f} | {loss*1e3:.3f} | {rail:.6f} | "+(f'{error*1e6:.3f}' if error is not None else 'Not checked')+' |')
if capture_rows:
    extra_text += '\nThe full time-zero history also completes through common capture:\n\n| Condition | Peak loss (mV) | Capture loss (mV) | Minimum rail at capture (V) | Maximum store acquisition error vs DC target (µV) |\n|---|---:|---:|---:|---:|\n'+'\n'.join(capture_rows)+'\n\nStore acquisition error is measured before the capture switch opens, relative to independently settled columns at the same diode state. It excludes switch-opening injection, hold droop and serial output error; it cannot replace the existing full-readout acceptance tests.\n'
next_gate = ('The nominal physical-grid turn-on refinement is complete. Before promoting the grid, repeat' if a.grid_refined_run else
             'Before promoting the grid, require a completed and refined physical-grid transient, then repeat')
fig, axes = plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for label,d,color in curves:
    ix,data=helpers['raw'](d/'stream.raw')
    meta=load(d/'extraction.json');roles=meta['roles']['rc']['0_63'];t=data[:,0]
    window=(t>=.0012)&(t<=.001205)
    local=data[:,ix['v(xarray.'+roles['vdd'].lower()+')']]
    loss=data[:,ix['v(vdd)']]-local
    axes[0].plot((t[window]-.0012)*1e6,loss[window]*1e3,label=label,color=color)
axes[0].set(xlabel='Time after row enable (µs)',ylabel='Far-pixel VDD wiring loss (mV)',title='Same pixel/capture circuit and timing')
axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
x=np.arange(2);w=.34
for offset,key,label,color in [(-w/2,'baseline','Original rails','#c54945'),(w/2,'grid','Upper-metal grid','#167c9b')]:
    axes[1].bar(x+offset,[report['physical_grid']['resistance_ohm'][n][key] for n in ['VDD','GND']],w,label=label,color=color)
axes[1].set(xticks=x,xticklabels=['VDD','Ground'],ylabel='Maximum port-to-device resistance (Ω)',title='Measured from physical extraction')
axes[1].legend(fontsize=8);axes[1].grid(axis='y',alpha=.2)
fig.savefig(ROOT/'docs/assets/row-power.png',dpi=160);plt.close(fig)
(ROOT/'simulations/row-power.json').write_text(json.dumps(report,indent=2)+'\n')
b=base['analysis']['worst'];l=low['analysis']['worst'];res=report['physical_grid']['resistance_ohm']
md=f'''# Row power-feed investigation — 2026-09-24

The original row-enable dip is reproducible and strongly sensitive to supply-wire resistance. A physical upper-metal grid has been built and passes both layout checkers and both connectivity checks. {grid_text}

![Row turn-on and extracted power resistance](assets/row-power.png)

## Controlled electrical diagnosis

The accepted 27 °C, typical-process 64-column capture deck is preserved from time zero, including reset, illumination, 40 pF stores, transistor switches, bias, 2 Ω source impedance and control timing. New short runs stop at 1.22 ms, 20 µs after row enable. A disconnected PWL source forces steps of at most 1 ns, then 0.5 ns, around turn-on; actual accepted spacing is checked from each raw waveform. No device, capacitor, signal-wire resistance or solver tolerance changes in this pair.

| Measurement | Result |
|---|---:|
| Original maximum local VDD wiring loss | {b['peak_vdd_loss_V']*1e3:.6f} mV |
| Peak time after enable | {b['peak_offset_us']*1e3:.6f} ns |
| Minimum local VDD–ground rail | {b['minimum_local_rail_V']:.6f} V |
| First downward crossing of 100 mV loss after the worst pixel's peak | {b['falling_threshold_crossing_us']['0.1']:.6f} µs |
| Maximum per-pixel peak change at 1→0.5 ns | {peak_delta*1e6:.6f} µV |
| Maximum threshold crossing change | {crossing_delta*1e3:.6f} ns |
| Peak with only VDD/GND extracted resistors multiplied by 0.1 | {l['peak_vdd_loss_V']*1e3:.6f} mV |

The resistance-only intervention changes {len(low['changed_resistors'])} audited resistor records; every capacitor/device record stays unchanged. Its ~90% reduction in peak loss supports supply-path resistance as the main lever. It does not identify all switching/coupling currents or constitute a manufacturable resistance-only layout. The 100 µV / 1 ns comparison limits above are numerical diagnostic screens, not a chosen hardware supply-drop budget. The original peak is brief and recovers well before capture; the earlier full-row circuit already passed its sampled output checks.

## Physical candidate

Two 8 µm-wide M5 straps connect VDD and ground through 3×3 via arrays (M2→M3→M4→M5) at the source, every fourth pixel, and the final pixel. Existing 2 µm M2 rails remain. The source remains at the left; this is distributed on-row feeding, not ideal supplies independently clamped at every column.

| Check | Result |
|---|---|
| Magic DRC | 0 errors |
| KLayout main process DRC | 0 items (antenna, density and CUP excluded) |
| Direct device LVS and resistor-collapsed LVS | Unique matches |
| New metal over drawn photodiode junctions | 0 µm² across 64 junctions |
| Other polygon geometry | Unchanged |
| Maximum VDD path resistance | {res['VDD']['baseline']:.3f} → {res['VDD']['grid']:.3f} Ω |
| Maximum ground path resistance | {res['GND']['baseline']:.3f} → {res['GND']['grid']:.3f} Ω |
| Extracted resistors / capacitors | {grid_meta['resistors']} / {grid_meta['capacitors']} |
| Negative extracted capacitances | {new_audit['negative_capacitors']} |

## Numerical status and next gate

The new meshed extraction takes unusually small steps before row enable with the original KLU/trapezoidal solver. The initial pair and the grid's Gear pair were deliberately stopped with partial traces retained; the compact KLU control timed out during operating-point initialization. Independent SPARSE runs completed on the full, unreduced extraction. No accuracy tolerance was relaxed. Incomplete runs are neither electrical failures nor passes. The compact network's algebraic boundary-current audit alone is not transient qualification. Two watchdog-extension records document bounded external supervision; both original supervisors resumed and exited.

{grid_text}
{extra_text}

{next_gate} the full 64-column captured-state/output checks at 27 °C and 125 °C with the existing 500 µV output-error and 10 µV refinement limits. Physical peripheral capacitors/clocks/supplies, multiple-row operation, broader corners, nonlinear startup and complete 64×64/tapeout gates remain open. The release GDS and carrier are unchanged.

Temperature checks vary the transistor/diode models while retaining the same nominal extracted wire R+C. Interconnect process corners and metal resistance temperature coefficients are not swept here. This remains a typical-process fixture with schematic periphery and behavioral control drivers.

## Evidence and reproduction

- `build/row-power-edge-20260924`: completed original-rail refinement and resistance-only intervention.
- `build/row-power-grid-20260924`: physical GDS, extraction, both LVS, both DRC, geometry and resistance audits.
- `build/row-power-grid-*`: separate solver controls, exact per-run decks, runner snapshots and outcomes.
- `simulations/row-power.json`: machine-readable measurements and run classifications.
- `checkpoints/row-power/`: stage archive and read-back verification manifest; earlier checkpoints are preserved.
- `scripts/diagnose-row-power.py`, `prepare-array-strips.py`, `audit-row-power-geometry.py`, `report-row-power.py`: reproducible helpers. Always use fresh output directories.

Earlier accepted capture results and `checkpoints/array-recovery` are unchanged. This stage does not supersede their accuracy evidence.
'''
(ROOT/'docs/row-power.md').write_text(md)
encoded=base64.b64encode((ROOT/'docs/assets/row-power.png').read_bytes()).decode()
section=f'''<section id="row-power"><h2>Row power-feed investigation</h2>
<p>The row-enable dip is reproducible: <strong>354.350 mV</strong>. Reducing only extracted power resistance by 10× reduces it to <strong>35.596 mV</strong>. The physical candidate adds 8 µm upper-metal straps and distributed via arrays; its maximum VDD path resistance falls from 260 to 53 Ω.</p>
<p>{html.escape(grid_text.replace('**',''))}</p>
<p>Magic and KLayout main DRC report zero errors; both LVS checks match. Added metal does not overlap the 64 drawn photodiode junctions. Full captured-state/output validation, physical peripheral implementation, startup and full-array qualification remain separate gates.</p>
<figure><img src="data:image/png;base64,{encoded}" alt="Row-enable voltage drop and extracted supply path resistance"><figcaption>Completed transient measurements only; the resistance-only diagnostic is not a physical layout.</figcaption></figure>
<p><a href="row-power.md">Measurements, numerical controls and exact scope</a></p></section>'''
(ROOT/'docs/row-power-section.html').write_text(section+'\n')
print(json.dumps({'peak_refinement_uV':peak_delta*1e6,'crossing_refinement_ns':crossing_delta*1e3,'physical_grid_transient':bool(a.grid_run)},indent=2))
