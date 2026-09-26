"""Publish completed bounded camera load/PVT results without rerunning simulations."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('runs',nargs='+');a=p.parse_args()
reports=[]
for run in a.runs:
 path=R/'build/camera-operating-corners'/run/'summary.json'
 d=json.loads(path.read_text())
 for name,c in d['cases'].items():
  for phase in ['stock-op','frozen-op']:
   e=path.parent/name/phase/'execution.json'
   if e.exists():c[phase+'_execution']=json.loads(e.read_text())
 assert len(d['cases'])==len(d['planned_cases']), 'Wait for the batch to finish'
 reports.append(dict(run=run,summary_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),**d))
nominal=json.loads((R/'simulations/three-frames.json').read_text())
out=dict(scope='Bounded normal-operation load/PVT screening on the final-layout capacitance model. Stock DC bias calculated at each condition; only 1680 MOS capacitors frozen. No startup, distributed-R, manufacturing or operating-range qualification.',
 baseline=dict(run=nominal['run'],samples=27,frame_2_to_3_max_V=nominal['frame_changes'][-1]['max_abs_difference_V'],tracking_max_V=nominal['dc_reference']['max_hold_minus_dc_V']),batches=reports)
# Pair any finer-step run with its corresponding coarse run, preserving failures.
comparisons=[]
for fine in reports:
 for coarse in reports:
  if fine['step_ns']>=coarse['step_ns'] or fine['frames']!=coarse['frames']:continue
  for name,x in fine['cases'].items():
   y=coarse['cases'].get(name)
   if not y or x.get('configuration')!=y.get('configuration'):continue
   comp=dict(case=name,coarse=coarse['run'],fine=fine['run'],limit_V=10e-6,pass_screen=False)
   if x.get('completed') and y.get('completed'):
    xx={(s['frame'],s['row'],s['column']):s for s in x['samples']};yy={(s['frame'],s['row'],s['column']):s for s in y['samples']}
    assert xx.keys()==yy.keys()
    comp['max_sample_difference_V']=max(abs(xx[k]['HOLD']-yy[k]['HOLD']) for k in xx)
    comp['pass_screen']=comp['max_sample_difference_V']<10e-6
   comparisons.append(comp)
out['refinements']=comparisons
coldpath=R/'build/camera-operating-corners/cold-pad-diagnostic-20260924/summary.json'
if coldpath.exists():out['cold_pad_diagnostic']=json.loads(coldpath.read_text())
(R/'simulations/camera-operating-corners.json').write_text(json.dumps(out,indent=2)+'\n')
rows=[];labels=[];errors=[];repeat=[]
for batch in reports:
 for name in batch['planned_cases']:
  c=batch['cases'][name];conf=batch['planned_cases'][name];ex=c.get('execution',{})
  status='PASS' if c.get('screen_pass') else 'screen fail' if c.get('completed') else 'watchdog' if ex.get('timed_out') else 'DC watchdog' if any(c.get(phase+'_execution',{}).get('timed_out') for phase in ['stock-op','frozen-op']) else 'incomplete'
  tracking=c.get('max_tracking_error_V');drift=c.get('frame_2_to_3_max_V')
  rows.append(f"| {batch['run']} / {name} | {conf['mos']}/{conf['diode']}/{conf['resistor']}/{conf['moscap']} | {conf['supply_V']:g} | {conf['temp_C']} | {conf['board_pF']}/{conf['sample_pF']} | {conf['input_ohm']/1000:g} | {len(c.get('samples',[]))}/{9*batch['frames']} | {tracking*1e6:.3f}" if tracking is not None else f"| {batch['run']} / {name} | {conf['mos']}/{conf['diode']}/{conf['resistor']}/{conf['moscap']} | {conf['supply_V']:g} | {conf['temp_C']} | {conf['board_pF']}/{conf['sample_pF']} | {conf['input_ohm']/1000:g} | {len(c.get('samples',[]))}/{9*batch['frames']} | —")
  rows[-1]+=f" | {drift*1e6:.3f} | {status} |" if drift is not None else f" | — | {status} |"
  labels.append(name+f" ({batch['frames']}f/{batch['step_ns']:g}ns)");errors.append(tracking*1e6 if tracking is not None else np.nan);repeat.append(drift*1e6 if drift is not None else np.nan)
txt='''# Full-camera load and operating-corner screen — 2026-09-24

This is a bounded engineering screen of the existing normal-operation candidate. The previous nominal case completed three frames with 27 samples, 5.733 µV frame-two/three drift and 167.766 µV maximum matched DC tracking error.

## Conditions and measured results

Process columns list MOS / diode / resistor / MOS-cap sections. Temperatures and 3.0–3.6 V endpoints are selected stress points, not a qualified product rating. Light currents remain fixed at 0, 80 and 240 pA. The external sample switch keeps its original 3.3 V control levels; chip row/reset/select drivers follow the changed chip supply. Board/sample capacitances and input resistance are external loads.

| Batch / case | Process sections | Supply (V) | °C | Board/sample (pF) | Input (kΩ) | Samples | Max DC error (µV) | Frame 2→3 (µV) | Result |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
'''+ '\n'.join(rows)+'\n\n'
txt+='PASS requires completed requested frames, valid sampled controls, correct per-row brightness order, matched HOLD/ADCIN DC errors below 500 µV, sampled bias agreement within 1%, and capacitor approximation bounds below 0.1%. Three-frame cases additionally require frame-two/three change below 50 µV. A one-frame pass does not establish repeatability at that condition. Incomplete numerical runs are not electrical failures or passes.\n\n'
first=reports[0]['cases']
headline=f"**Initial {len(first)}-case screen:** {sum(c.get('screen_pass',False) for c in first.values())} pass, {sum(c.get('completed',False) and not c.get('screen_pass',False) for c in first.values())} completed accuracy failure, and {sum(not c.get('completed',False) for c in first.values())} incomplete DC cases. Follow-up controls below distinguish load settling, numerical refinement and loaded repeatability.\n\n"
txt=txt.replace('This is a bounded engineering screen',headline+'This is a bounded engineering screen',1)
txt+='## Capacitor approximation and provenance\n\n'
for batch in reports:
 for name,c in batch['cases'].items():
  ranges=c.get('frozen_cap_bias_ranges',[])
  if ranges:
   error=max(max(x['max_C_relative_error'],x['max_differential_C_relative_error']) for x in ranges)
   txt+=f"- {batch['run']} / {name}: capacitor terminal range {min(x['min_V'] for x in ranges):.6f}–{max(x['max_V'] for x in ranges):.6f} V; worst relative capacitance bound {error:.3g}; stock/frozen DC voltage difference {c['stock_frozen_op_max_voltage_difference_V']*1e6:.6g} µV.\n"
  if c.get('error'):txt+=f"- {batch['run']} / {name}: {c['error']}\n"
  if not c.get('screen_pass'):
   txt+=f"- {batch['run']} / {name} failed or unestablished checks: "+', '.join(k for k in ['completed','cap_approximation_pass','controls_pass','brightness_order_pass','tracking_pass','bias_pass','frame_repeatability_pass'] if c.get(k) is False)+'\n'
txt+='''
Each condition first attempts a complete stock-circuit DC solve with all nonlinear MOS capacitors present. Only after that succeeds are the 1,680 capacitor values recomputed at that condition's settled terminal voltages, including PDK process multipliers (typical 1, fast 0.9, slow 1.1). Every other extracted chip record is preserved. A second DC solve verifies unchanged bias. The installed model formula has no explicit temperature coefficient; temperature still affects the DC operating point through the semiconductor models. Both C(V) and the differential d[V·C(V)]/dV are bounded across every captured point against the frozen values. The 0.1% approximation limit is an explicit engineering screening threshold, not foundry signoff.

Each readout reference holds all nine pixel charge-state voltages at their captured values, freezes the digital controls at the sampling instant, and solves the same loaded circuit at DC. These extra state-holding sources exist only in the DC reference, never in the transient or physical chip. Tolerances, equivalent reset source, 2 Ω supply resistance, acquisition timing, all fifteen clamp domains and nominal layout wiring capacitance are retained.

## Refinement and remaining qualification

'''
for c in comparisons:
 txt+=f"- {c['case']}: {c['coarse']} → {c['fine']}; sample difference {c.get('max_sample_difference_V',float('nan'))*1e6:.3f} µV; <10 µV screen: {c['pass_screen']}.\n"
if not comparisons:txt+='No new timestep-refinement comparison is included in this batch.\n'
txt+='''
This selection does not cover the full process/diode/resistor/capacitor cross-product, all load combinations, interconnect variation, external component tolerances, mismatch/noise or optical/dark-current behavior. Nonlinear startup and full distributed resistance-plus-capacitance qualification remain open. The fast generic sample/hold fixture is not an ADS1115 conversion model. First-frame results and selected repeat/refinement results must not be promoted into a full PVT qualification claim.

Exact decks, stock and frozen models, operating points, full transient waveforms, DC references, simulator/PDK hashes and failure logs are under `build/camera-operating-corners/`. Machine-readable results: [camera-operating-corners.json](../simulations/camera-operating-corners.json).

![Tracking and repeatability results](assets/camera-operating-corners.png)

## Capacitive-load settling diagnostic

In the first heavy-capacitive-load acquisition, HOLD rises from 1.903714 V at 4 µs to 1.969918 V at 5 µs, still below its 2.318731 V DC target. The nominal load is already settled. The load-isolation cases vary each capacitor separately; the finer-step case checks numerical reproducibility of the combined-load failure.

![Nominal and heavy capacitive load waveforms](assets/camera-load-diagnostic.png)
'''
if 'cold_pad_diagnostic' in out:
 txt+='\n## Isolated cold-pad DC control\n\nThe eight protection diodes attached to unused pad NC_P10 reproduce the cold singular-matrix warning with ideal rails. The isolated cold solves finish only after ngspice falls back to transient-assisted operating-point calculation; these are not accepted direct DC/camera results. The warm control and a cold control with an added 1 TΩ pad-to-ground path converge without that warning or fallback. The added path is diagnostic only and is not included in any full-camera transient. This supports further investigation of floating unused-pad conditioning; it does not qualify a cold operating corner or establish a hardware defect. Exact controls are in `build/camera-operating-corners/cold-pad-diagnostic-20260924/`.\n'
txt+='\n## Reproduction\n\nRun in the existing toolchain with a fresh output name; existing directories are deliberately never overwritten:\n\n```sh\nbash scripts/run-tools.sh python3 scripts/screen-camera-operating-corners.py new-first-frame-screen --cases heavy-cap heavy-resistive supply-low supply-high ss-hot-low ff-cold-high fs-hot sf-cold --workers 4\n```\n\nUse `--frames 3 --timeout 3000 --cases heavy-resistive` for the selected loaded repeatability test, `--step-ns 500 --cases heavy-cap fs-hot` for refinement, and `--cases heavy-board-only heavy-sample-only` for load isolation, each with a distinct run name. The evidence archive retains the exact executed runner snapshots and all per-case decks; simulator and PDK hashes are recorded in each batch summary.\n'
(R/'docs/camera-operating-corners.md').write_text(txt)
fig,axs=plt.subplots(2,1,figsize=(12,max(8,len(labels)*.45+3)),layout='constrained',gridspec_kw={'height_ratios':[3,1]})
for ax,values,limit,label,names in [(axs[0],errors,500,'Maximum matched DC tracking error (µV)',labels),
 (axs[1],[out['baseline']['frame_2_to_3_max_V']*1e6]+[v for v in repeat if np.isfinite(v)],50,'Frame 2→3 difference (µV)',
 ['Saved nominal reference']+[n for n,v in zip(labels,repeat) if np.isfinite(v)])]:
 y=np.arange(len(names))
 ax.barh(y,values,color=['#318a65' if np.isfinite(v) and v<limit else '#b85b41' for v in values]);ax.set_yticks(y,names);ax.invert_yaxis();ax.axvline(limit,color='black',linestyle='--',label=f'{limit} µV screen');ax.set_xlabel(label);ax.grid(axis='x',alpha=.2);ax.legend();ax.set_xlim(left=0)
axs[0].set_xscale('symlog',linthresh=500)
fig.suptitle('Full-camera normal-operation screen; missing bars mean unmeasured')
fig.savefig(R/'docs/assets/camera-operating-corners.png',dpi=140);plt.close(fig)
(R/'docs/camera-operating-corners-section.html').write_text('<section id="camera-operating-corners"><h2>Load and operating-corner screen</h2><p>Bounded full-camera normal-operation results, including per-condition capacitor validation and matched DC references. Startup and distributed wiring resistance remain open.</p><p><a href="camera-operating-corners.md">Measured results and coverage</a></p><img src="assets/camera-operating-corners.png" alt="Load and operating-corner results" style="max-width:100%"></section>\n')
print('Published',len(labels),'cases and',len(comparisons),'refinement comparisons')
