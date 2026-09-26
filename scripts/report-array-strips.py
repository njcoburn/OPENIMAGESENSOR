"""Report the completed 64-pixel strip experiments without implying full-camera signoff."""
from pathlib import Path
import argparse, json, hashlib, runpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--extraction',required=True);p.add_argument('--settling',required=True);p.add_argument('--settling-supplement',nargs='+',default=[]);p.add_argument('--refinement',required=True);p.add_argument('--refinement-supplement',nargs='+',default=[]);p.add_argument('--placement',required=True);p.add_argument('--imaging',nargs='+',required=True);p.add_argument('--imaging-refinement',nargs='+',required=True);p.add_argument('--imaging-second-refinement',nargs='+',default=[]);a=p.parse_args()
def load(name):return [{**v,'run_directory':name} for v in json.loads((R/name/'results.json').read_text())]
ex=R/a.extraction;coarse=load(a.settling)+[v for name in a.settling_supplement for v in load(name)];fine=load(a.refinement)+[v for name in a.refinement_supplement for v in load(name)];placement=load(a.placement)
# Imaging batches can include superseded tall-row DC references; select latest case.
imaging={v['case']:v for name in a.imaging for v in load(name)}
imfine={v['case']:v for name in a.imaging_refinement for v in load(name)}
assert len(coarse)==12 and all(v['completed'] for v in coarse)
assert set(imaging)=={'r1c64','r64c1'} and all(v['completed'] for v in imaging.values())
assert set(imfine)==set(imaging) and all(v['completed'] for v in imfine.values())
def compare(x,y):
    assert x['completed'] and y['completed']
    assert len(x['samples'])==len(y['samples'])
    values=[]
    for u,v in zip(x['samples'],y['samples']):
        assert (u['row'],u['column'],u['time_s'])==(v['row'],v['column'],v['time_s'])
        values.append(abs(u['capture']['HOLD']-v['capture']['HOLD']))
    delta=max(values)
    return {'max_sample_difference_V':delta,'limit_V':10e-6,'pass':delta<10e-6}
initial_imaging_checks=[]
second={v['case']:v for name in a.imaging_second_refinement for v in load(name)}
for case in list(imaging):
    test=compare(imaging[case],imfine[case]);initial_imaging_checks.append({'case':case,'kind':'initial imaging 200 to 100 ns',**test})
    if not test['pass'] and case in second:
        imaging[case],imfine[case]=imfine[case],second[case]
checks=[]
for f in fine:
    c=next(v for v in coarse if v['case']==f['case'] and v['mode']==f['mode']);checks.append({'case':f['case'],'kind':'settling timestep',**compare(c,f)})
for f in placement:
    c=imaging[f['case']] if f['fixture']=='imaging' else next(v for v in coarse if v['case']==f['case'] and v['mode']=='rc-port');checks.append({'case':f['case'],'kind':'reset capacitance placement ('+f['fixture']+')',**compare(c,f)})
for case,f in imfine.items():checks.append({'case':case,'kind':f'imaging timestep {imaging[case]["step_ns"]:g} to {f["step_ns"]:g} ns',**compare(imaging[case],f)})
read_raw=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
waveform_metrics={}
for case,v in imaging.items():
    meta=json.loads((ex/case/'extraction.json').read_text());names,data=read_raw(R/v['run_directory']/f"{case}-{v['mode']}"/'transient/stream.raw')
    ix={n:i for i,n in enumerate(names)};mask=data[:,0]>=.0012;port=data[mask,ix['v(vdd)']]
    def trace(n):
        if n=='GND':return np.zeros(len(port))
        key='v('+ (n if n in meta['ports'] else 'xarray.'+n).lower()+')'
        return data[mask,ix[key]]
    drops=[];grounds=[];rails=[]
    for pixel in meta['roles']['rc'].values():
        local=trace(pixel['vdd']);gnd=trace(pixel['gnd']);drops.append(float(np.max(port-local)));grounds.append(float(np.max(np.abs(gnd))));rails.append(float(np.min(local-gnd)))
    waveform_metrics[case]={'window_start_s':.0012,'max_local_vdd_loss_V':max(drops),'max_abs_local_ground_V':max(grounds),'min_local_vdd_minus_ground_V':min(rails),'max_source_current_A':float(np.max(-data[mask,ix['i(vsource)']]))}
    del data

audits={d.name:json.loads((d/'rc-audit.json').read_text()) for d in ex.glob('r*c*')};extractions={d.name:json.loads((d/'extraction.json').read_text()) for d in ex.glob('r*c*')}
comparisons=[]
for case in extractions:
    c=next(v for v in coarse if v['case']==case and v['mode']=='capacitance');rc=next(v for v in coarse if v['case']==case and v['mode']=='rc-port')
    comparisons.append({'case':case,'max_sample_difference_V':compare(c,rc)['max_sample_difference_V'],'note':'Physical R effect, not a numerical-refinement pass requirement.'})
solver_checks=json.loads((R/'build/array-strip-dc-solver-20260924/results.json').read_text());assert len(solver_checks)==3 and all(v['max_voltage_difference_V']<1e-6 for v in solver_checks)
result={'dc_solver_crosschecks':solver_checks,'scope':'Nominal unfilled 1x64 and 64x1 extracted strips with short controls; schematic shared readout and finite drivers/supply. Main column RC uses signed reset-shunt consolidation with placement sensitivity. Fixed-sense settling is a diagnostic; imaging uses free integration. Not a full 64x64 camera or startup/PVT/signoff qualification.','runs':vars(a),'extractions':extractions,'rc_audits':audits,'imaging_waveform_metrics':waveform_metrics,'settling':coarse,'refinement':fine,'placement':placement,'imaging':list(imaging.values()),'imaging_refinement':list(imfine.values()),'checks':checks,'initial_imaging_checks':initial_imaging_checks,'physical_R_comparisons':comparisons}
(R/'simulations/array-strips.json').write_text(json.dumps(result,indent=2)+'\n')
rows=[]
for v in coarse:
    rows.append(f"| {v['rows']}×{v['columns']} | {v['mode']} | {v['max_tracking_error_V']*1e6:.3f} | {v['max_local_vdd_drop_V']*1e3:.3f} | {v['max_gate_50pct_ns']:.3f} | {v['tracking_screen_pass']} |")
imrows=[]
for v in imaging.values():
    imrows.append(f"| {v['rows']}×{v['columns']} | {len(v['samples'])} | {v['max_tracking_error_V']*1e6:.3f} | {v['max_local_vdd_drop_V']*1e3:.3f} | {v['max_supply_current_A']*1e6:.1f} | {v['tracking_screen_pass']} |")
checkrows=[f"| {v['case']} | {v['kind']} | {v['max_sample_difference_V']*1e6:.3f} | {v['pass']} |" for v in checks]
exposure=[]
for case,v in imaging.items():
    lows=[s for s in v['samples'] if s['sense_differential_V']<0]
    exposure.append({'case':case,'samples_with_forward_biased_photodiode':len(lows),'min_sense_differential_V':min(s['sense_differential_V'] for s in v['samples'])})
result['exposure_limits']=exposure
(R/'simulations/array-strips.json').write_text(json.dumps(result,indent=2)+'\n')
wide=imaging['r1c64'];medium=[s for s in wide['samples'] if s['photocurrent_pA']==80]
exposure_note=f"**Exposure limit found:** at 240 pA, {next(x['samples_with_forward_biased_photodiode'] for x in exposure if x['case']=='r1c64')} late samples in the wide row have sense-to-anode voltage below zero (minimum {min(s['sense_differential_V'] for s in wide['samples']):.3f} V), indicating forward-biased photodiodes after over-integration. At the same 80 pA illumination, HOLD changes from {medium[0]['capture']['HOLD']:.3f} V at column {medium[0]['column']} to {medium[-1]['capture']['HOLD']:.3f} V at column {medium[-1]['column']}. A readout tracking pass does not make this exposure schedule a usable uniform-exposure camera mode."
wave_note=' Full readout-window (not only sample-time) maximum local VDD losses are '+', '.join(f"{case}: {v['max_local_vdd_loss_V']*1e3:.3f} mV" for case,v in waveform_metrics.items())+'. These exclude power-up and do not include driver source power.'
netrows=[]
for case in ['r1c3','r1c64','r3c1','r64c1']:
    x=audits[case]['net_metrics'];e=extractions[case]
    netrows.append(f"| {e['rows']}×{e['columns']} | {e['resistors']} | {e['capacitors']} | {x['ROW0']['max_ohm']:.1f} | {x['COL0']['max_ohm']:.1f} | {x['VDD']['max_ohm']:.1f} |")
fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for case,net,label in [('r1c64','ROW0','64-column row select'),('r64c1','COL0','64-row column')]:
    vs=audits[case]['net_metrics'][net]['effective_resistance_ohm'];items=sorted(vs.items(),key=lambda kv:tuple(map(int,kv[0].split('_'))));ax[0,0].plot(range(len(items)),[v for k,v in items],label=label)
ax[0,0].set(xlabel='Pixel index',ylabel='Port-to-terminal resistance (Ω)',title='Extracted long-wire resistance');ax[0,0].legend()
for case in ['r1c64','r64c1']:
    v=next(v for v in coarse if v['case']==case and v['mode']=='rc-port')
    ax[0,1].plot([5,15,30],[max(abs(s['errors_V'][str(us)]) for s in v['samples'])*1e6 for us in [5,15,30]],'o-',label=case)
ax[0,1].axhline(500,color='red',ls='--',label='500 µV screen');ax[0,1].set_yscale('symlog',linthresh=.01);ax[0,1].set(xlabel='Acquisition time (µs)',ylabel='Worst DC tracking error (µV)',title='Fixed-sense settling diagnostic');ax[0,1].legend()
for case,v in imaging.items():
    ax[1,0].plot(range(len(v['samples'])),[s['local_vdd_drop_V']*1e3 for s in v['samples']],label=case)
ax[1,0].set(xlabel='Readout index',ylabel='Local VDD loss relative to port (mV)',title='Wire voltage drop during imaging');ax[1,0].legend()
for case,v in imaging.items():
    ss=[s for s in v['samples'] if s['photocurrent_pA']==80]
    ax[1,1].plot([s['row']*v['columns']+s['column'] for s in ss],[s['capture']['HOLD'] for s in ss],'o-',label=case+' at 80 pA')
ax[1,1].set(xlabel='Readout index',ylabel='Sampled HOLD (V)',title='Continuing integration across serial readout');ax[1,1].legend()
fig.savefig(R/'docs/assets/array-strips.png',dpi=160);plt.close(fig)
text='''# 64-pixel row and column extraction tests

The next array target is **64×64; frame rate remains undecided**. These tests exercise physical 1×64 and 64×1 strips with 1×3 and 3×1 controls. They do not assemble the full camera.

## Physical checks and extracted wiring

All four unfilled layouts pass Magic DRC and two device-connectivity LVS checks: direct extraction and the independently resistor-collapsed RC model, each against an independent schematic. Each long strip retains 192 NMOS devices and 64 photodiodes. Pixel pitch is 80×50 µm; the nominal long dimensions are 5.12 mm horizontally and 3.20 mm vertically.

| Strip (rows×columns) | Resistors | Capacitors | Max ROW0 R (Ω) | Max COL0 R (Ω) | Max VDD R (Ω) |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(netrows)+'''

Resistance is effective port-to-device resistance, not a fitted lumped value. Coupling capacitance remains in the model. Extraction uses the installed nominal GF180 Magic technology, 1 Ω resistance threshold, 0.1 Ω minimum resistor and zero delay threshold. This is engineering PEX, not foundry signoff.

**Capacitance-placement limitation:** Magic emits one −0.30922 fF reset shunt per pixel in the narrow column strips. The main model consolidates each reset net's signed ground-shunt sum at its port; the alternate puts the same sum at its reset gate. All resistors, semiconductor devices and coupling capacitors remain. Every resistor-collapsed capacitance-pair sum is conserved. This is an explicit placement approximation, not complete distributed-capacitance qualification. Raw extraction and both placements are retained; neither is declared a physical worst-case bound.

## Fixed-sense settling experiment

The diagnostic holds each local diode voltage at one of 1.95, 1.75 or 1.30 V through an explicit 1 Ω source. This freezes exposure to isolate readout settling; it is not a pixel imaging simulation. The reference states are verified within 1 µV at sampling. Every sample has an independently solved matching DC reference.

The fixture uses 3.3 V through 2 Ω, a 2 V/1 Ω reset source, 100 Ω rail-referenced control drivers, the existing 100 kΩ control pulls, schematic column current sinks/multiplexer and output buffer, 49.9 kΩ PREF and 5.1 MΩ BIAS. The external fixture is 100 pF board + 20 pF sampling capacitance. Columns use 50 µs slots with acquisition from 2–32 µs after selection. This is a generic sample/hold load, not an actual ADC conversion schedule. Peripheral interconnect, pads, clamps, fill, package routing and addressing are not extracted.

| Strip | Model | Max 30 µs error (µV) | Max local VDD loss (mV) | Max gate 50% time (ns) | <500 µV |
|---|---|---:|---:|---:|---|
'''+ '\n'.join(rows)+'''

Gate time is measured from the start of the 10 ns source edge; about 5 ns is the driver's own half-rise time. Supply loss is measured at sampled pixel source-follower drains relative to the array supply port, separately from the external 2 Ω drop.

## Free integration

Each pixel begins held in reset. Reset is released about 1 ms before its row starts readout; photocurrents cycle through 0, 80 and 240 pA. All 64 pixels are read once. The long-row imaging timestep criterion remains unmet, as documented below; completion and tracking accuracy are separate from numerical qualification. The wide row's later columns keep integrating during its 3.15 ms first-to-last sample interval. The tall column uses staggered row resets, preserving the same nominal exposure age for each row. Consequently, a brightness-versus-position trend in the wide row is not automatically a settling failure. The DC reference freezes the actual sampled local sense voltages and reproduces the control states, including future rows still in reset.

| Strip | Samples | Max DC tracking error (µV) | Max local VDD loss (mV) | Max sampled source current (µA) | <500 µV |
|---|---:|---:|---:|---:|---|
'''+ '\n'.join(imrows)+'\n\n'+exposure_note+'\n\n'+wave_note+'''

Source current includes the VDD-connected reset pullups and schematic readout. Behavioral control sources supply their output energy independently; their driver power is not charged to VDD, so this is not total interface or full-camera power. The 100 kΩ reset pullups draw current whenever reset is driven low, making direct-control replication particularly costly in the tall strip.

## Refinement and placement checks

| Strip | Comparison | Maximum sample change (µV) | Below 10 µV |
|---|---|---:|---|
'''+ '\n'.join(checkrows)+'''

The initial timestep ceiling is 200 ns. The long row's imaging comparison at 100 ns changed a sample by about 17.1 µV, above the retained 10 µV numerical screen; that failed comparison is preserved. The follow-up 100→50 ns row comparison changes a sample by about 20.3 µV and also fails that screen. **Long-row imaging numerical qualification remains open**; its tracking results are provisional. Other comparisons use 200 ns against 100 ns. Solver method and warnings are preserved per run. Some runs use ngspice's transient-assisted operating-point fallback; successful normal-operation traces do not qualify nonlinear power-up. Three selected tall-strip DC references are also checked with the independent SPARSE solver; terminal voltages agree within 1 µV. Very small printed tracking errors are numerical results, not a sensor noise-floor claim. Full waveforms, matching DC decks, runner snapshots, extraction settings, model hashes and failed fixture-development attempts are preserved separately from the accepted comparisons.

![Extracted wire resistance, settling, supply drop and exposure effects](assets/array-strips.png)

## What this permits next

Resolve the long-row imaging numerical refinement and use the clear exposure-skew result to design the 64×64 addressing and readout schedule, then test an intermediate tile with realistic shared routing. Fifty microseconds per pixel would consume 204.8 ms for 4096 pixels (4.88 frames/s before overhead), but this strip schedule is a diagnostic, not a selected frame rate or a demonstrated full-array throughput. A shorter acquisition result alone does not prove that all switching, reset, ADC and transfer overhead can be shortened by the same amount.

The full 64×64 still needs its own supply routing, long parallel-line coupling, fill, shared-readout extraction, operating corners, nonlinear startup and physical/manufacturing checks. The existing 3×3 release hardware is unchanged.

## Reproduce

Run the scripts inside the project's tools container with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`. Use fresh output directories: `prepare-array-strips.py --output ...`, then `audit-array-strip-rc.py <extraction-directory>`, then `simulate-array-strips.py --source <extraction-directory> --output ...`. Default simulation arguments run the four fixed-sense strips in device/C-only/RC modes. Use `--cases r1c64 r64c1 --modes rc-port --fixture imaging --method gear` for free integration, `--step-ns 100` for refinement, and `--cases r64c1 --modes rc-gate --fixture imaging --method gear` for the placement check. Machine-readable run paths and exact runner snapshots preserve the executed versions. `--reuse-transients` is permitted only when the transient deck is identical after output-directory normalization; it recomputes DC references without changing the saved trace.

The earlier fixture-development failures are classified in the checkpoint's `build/array-strips-20260924/attempts.json`; they must not be used as physical pass/fail results. The corrected coarse imaging batch replaces the tall strip's initial DC references, which had incorrectly driven future row resets low.

Machine-readable results: [array-strips.json](../simulations/array-strips.json). See [tapeout readiness](tapeout-readiness.md) for the remaining release gates.
'''
(R/'docs/array-strips.md').write_text(text)
print('Published',len(coarse),'settling cases,',sum(len(v['samples']) for v in imaging.values()),'imaging samples; checks',checks,flush=True)
