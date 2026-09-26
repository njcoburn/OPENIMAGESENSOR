"""Report complete power-grid readout qualification; no incomplete-run passes."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--runs',type=Path,required=True)
a=p.parse_args();root=a.runs.resolve()
load=lambda p:json.loads(p.read_text())
workflow=load(root/'manifest.json')
assert len(workflow['runs'])==4 and all(r['transient_completed'] for r in workflow['runs'].values())
selected=workflow.get('selected_matched_runs',{})
if selected:assert workflow['reference_retry']['completed']
fixture_check=load(root/'fixture-verification/result.json')
assert fixture_check['all_four_circuits_and_stimuli_match']
assert {(d['temperature_C'],d['step_ns']) for d in fixture_check['decks']}=={(t,s) for t in [27,125] for s in [100,200]}
for check in fixture_check['decks']:
    deck=root/f"{check['temperature_C']}-{check['step_ns']}/r1c64-rc-port/transient/test.spice"
    assert hashlib.sha256(deck.read_bytes()).hexdigest()==check['deck_sha256']
rows=[];details={};comparisons=[]
fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained')
for temp,color in [(27,'#187f9b'),(125,'#b44345')]:
    coarse=load(root/f'{temp}-200/r1c64-rc-port/result.json')
    fine=load(root/f'{temp}-100/r1c64-rc-port/result.json')
    d=root/selected.get(str(temp),f'{temp}-100-matched')/'r1c64-rc-port'
    matched=load(d/'result.json');metrics=load(d/'recovery-analysis.json')
    coarse_metrics=load(root/f'{temp}-200/r1c64-rc-port/recovery-analysis.json')
    assert all(r['completed'] and len(r['samples'])==64 for r in [coarse,fine,matched])
    assert coarse['model_sha256']==fine['model_sha256']==matched['model_sha256']
    assert matched['model_sha256']==fixture_check['source_model_sha256']
    assert hashlib.sha256((d/'array.spice').read_bytes()).hexdigest()==matched['model_sha256']
    for key in ['temperature_C','method','solver','tolerances','slot_us','acquisition_us',
                'bias_ohm','pref_ohm','column_storage_pF','reset_after_capture','capture_time_s']:
        assert coarse[key]==fine[key]==matched[key],key
    assert (coarse['step_ns'],fine['step_ns'])==(200,100)
    assert matched['capture_reference'] and 'Total deterministic capture' in matched['accuracy_scope']
    normalized=lambda path:path.read_text().replace(str(path.parent.parent),'/CASE')
    assert normalized(d/'transient/test.spice')==normalized(root/f'{temp}-100/r1c64-rc-port/transient/test.spice')
    errors=[];deltas=[]
    for x,y,z in zip(coarse['samples'],fine['samples'],matched['samples']):
        assert (x['row'],x['column'],x['time_s'])==(y['row'],y['column'],y['time_s'])==(z['row'],z['column'],z['time_s'])
        assert y['capture']['HOLD']==z['capture']['HOLD']
        errors.append(z['capture']['HOLD']-z['dc']['v(hold)'])
        deltas.append(y['capture']['HOLD']-x['capture']['HOLD'])
    maxerr=max(map(abs,errors));maxdelta=max(map(abs,deltas))
    controls=metrics['all_capture_readout_controls_pass'] and coarse_metrics['all_capture_readout_controls_pass']
    groups=[[s['capture']['HOLD'] for i,s in enumerate(matched['samples']) if i%3==j] for j in range(3)]
    brightness=min(groups[0])>max(groups[1]) and min(groups[1])>max(groups[2])
    reverse_biased=metrics['capture_min_sense_V']>0
    assert abs(maxerr-matched['max_tracking_error_V'])<1e-12
    passed=maxerr<500e-6 and maxdelta<10e-6 and controls and brightness and reverse_biased
    details[str(temp)]={'max_output_error_V':maxerr,'max_timestep_difference_V':maxdelta,
                        'controls_pass':controls,'brightness_order_correct':brightness,
                        'all_capture_diodes_reverse_biased':reverse_biased,
                        'passed':passed,'errors_V':errors,'timestep_differences_V':deltas,
                        'matched_result':matched,'waveform_metrics':metrics,
                        'coarse_control_checks':coarse_metrics['capture_readout_control_checks']}
    rows.append(f'| {temp} °C | {maxerr*1e6:.3f} | {maxdelta*1e6:.3f} | {"Pass" if controls else "Fail"} | {"Pass" if passed else "Fail"} |')
    axes[0].plot(range(64),np.array(errors)*1e6,'.-',color=color,label=f'{temp} °C')
    axes[1].plot(range(64),np.array(deltas)*1e6,'.-',color=color,label=f'{temp} °C')
for ax,limit,title in [(axes[0],500,'Total captured-state → output error'),(axes[1],10,'200 → 100 ns change in sampled output')]:
    ax.axhline(limit,color='#555',ls='--',lw=1);ax.axhline(-limit,color='#555',ls='--',lw=1)
    ax.set(title=title,xlabel='Column',ylabel='Error (µV)',xlim=(-1,64));ax.grid(alpha=.2);ax.legend()
fig.savefig(ROOT/'docs/assets/grid-readout.png',dpi=160);plt.close(fig)
report={'scope':'One extracted 64-column row with physical power grid; schematic capture/readout; typical process and fixed nominal wire RC at 27/125 C.',
        'limits':{'output_error_V':500e-6,'timestep_difference_V':10e-6},
        'all_conditions_pass':all(r['passed'] for r in details.values()),'conditions':details,
        'fixture_verification':fixture_check,
        'workflow':workflow}
reference_check=load(root/'reference-verification/result.json')
assert all(r['maximum_target_difference_V']<1e-8 for r in reference_check['capture'].values())
assert all(r['target_difference_V']<1e-8 and r['hold_adcin_residual_V']<1e-8 for r in reference_check['output'])
assert set(reference_check['capture'])=={'27','125'} and len(reference_check['output'])>=4
report['reference_settling_verification']=reference_check
(ROOT/'simulations/grid-readout.json').write_text(json.dumps(report,indent=2)+'\n')
outcome='passes' if report['all_conditions_pass'] else 'does not pass all of'
intro=f'The full 64-column readout on the physical upper-metal power grid **{outcome} the retained nominal/hot accuracy and timestep checks**. Each condition includes all 64 output samples and independently settled references at the common optical capture state.'
next_step=('Next, physically implement the capture/readout tile with actual capacitors, shared supply and clock routing; re-extract it and check repeated/multirow operation.' if report['all_conditions_pass'] else
           'Resolve the failed condition(s) above and repeat the affected comparison before promoting this circuit or proceeding to the physical capture/readout tile.')
md=f'''# Full readout on the row power grid — 2026-09-24

{intro}

| Device temperature | Worst total output error (µV; limit 500) | Largest 200→100 ns difference (µV; limit 10) | Sampled controls | Combined result |
|---|---:|---:|---|---|
'''+ '\n'.join(rows)+'''

![Full row output accuracy and numerical refinement](assets/grid-readout.png)

## What was checked

All four simulations begin at time zero, reset/integrate, enable the row at 1.2 ms, capture at 1.4 ms, turn the row off and reset its pixels, then read all 64 stores sequentially until 2.7 ms. The 40 pF stores, 500 kΩ BIAS, 12.4 kΩ PREF, 10 µs acquisition, 20 µs slots, generic 100 pF board/20 pF ADC load and 2 Ω source impedance are unchanged.

The independent references first freeze all diode states immediately before common capture and solve the settled column targets. Each output reference clamps the stores to those targets, not to their already imperfect captured voltages. The reported total error therefore includes acquisition error, capture-switch disturbance, retention and output settling. All references must have ADCIN–HOLD residual below 10 nV. Finite waveforms, full stop time and all 64 samples are required. Sampled capture/mux/ADC/row-reset states are checked independently.

The capture targets and selected first/last/worst output references are independently checked with twice the DC settling duration (200→400 µs), requiring agreement within 10 nV. Brightness ordering and reverse-biased capture diode states are also checked; these deterministic checks do not characterize optical performance or noise.

The physical model retains 4,378 extracted resistors and 2,353 capacitors from the checked M5-grid layout. No equivalent-network reduction or relaxed accuracy tolerance is used. The SPARSE solver is used consistently for the new-grid transient comparisons. Previous short controls established the original-rail SPARSE/KLU peak agreement. The isolated breakpoint fixture used to resolve the earlier power pulse is removed; a deck audit verifies that the chip/capture circuit and stimuli are otherwise identical.

## Scope and next stage

This qualifies the tested single-row readout fixture, not the full camera or tapeout. Storage capacitors, readout devices/interconnect and control drivers remain schematic. Both temperature tests retain nominal extracted wire RC; metal temperature coefficients and process/interconnect corners remain open. There is no startup, noise/mismatch, optical/package, repeated/multirow or full 64×64 qualification here.

'''+next_step+''' Retain the separate full-chip startup and manufacturing gates. The release GDS and carrier are unchanged.

The [physical tile implementation plan](capture-tile-plan.md) inventories the tested devices and separates capacitor, shared-routing and real-driver implementation checks.

## Evidence

- `build/grid-readout-20260924`: four complete transients, exact commands/runners, two sets of 64 matched DC output references and control/power analyses.
- `build/row-power-grid-20260924`: the unchanged layout/extraction from the preceding [power-grid investigation](row-power.md).
- `simulations/grid-readout.json`: complete per-column results, limits and provenance.
- `scripts/qualify-grid-readout.py`, `finish-column-capture.py`, `report-grid-readout.py`: reproducible workflow; always use fresh output directories.

Earlier power-grid and array-recovery checkpoints remain unchanged.
'''
if selected:
    md+='\nThe nominal reference batch was deliberately stopped after its successful early solves to increase concurrency from 3 to 12 independent workers. Its completed references were reused only after exact normalized-deck matching; partial solves were recomputed in `27-100-matched-parallel`. The original attempt and supervisor stop are preserved and excluded from the final qualification. No circuit or numerical settings changed.\n'
(ROOT/'docs/grid-readout.md').write_text(md)
encoded=base64.b64encode((ROOT/'docs/assets/grid-readout.png').read_bytes()).decode()
section=f'''<section id="grid-readout"><h2>Full readout on the new power grid</h2><p>{intro.replace('**','')}</p><table><tr><th>Temperature</th><th>Total error (µV)</th><th>Refinement (µV)</th></tr>'''
for temp,r in details.items():section+=f'<tr><td>{temp} °C</td><td>{r["max_output_error_V"]*1e6:.3f}</td><td>{r["max_timestep_difference_V"]*1e6:.3f}</td></tr>'
section+=f'''</table><figure><img src="data:image/png;base64,{encoded}" alt="All 64 output errors and timestep differences"><figcaption>Limits unchanged: 500 µV total output error and 10 µV refinement.</figcaption></figure><p>Pixels and row power wiring use extracted R+C; storage/readout periphery remains schematic. Physical tile, multirow, wire corners and startup gates remain open. <a href="grid-readout.md">Detailed evidence and scope</a>.</p></section>'''
(ROOT/'docs/grid-readout-section.html').write_text(section+'\n')
print(json.dumps({temp:{k:v for k,v in r.items() if k in ['max_output_error_V','max_timestep_difference_V','controls_pass','passed']} for temp,r in details.items()},indent=2))
