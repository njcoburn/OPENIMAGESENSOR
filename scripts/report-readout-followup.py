"""Report timing and explicitly terminated-unused-pad follow-ups separately."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('runs',nargs='+');a=p.parse_args()
batches=[]
for name in a.runs:
 root=R/'build/camera-operating-corners'/name
 data=json.loads((root/'summary.json').read_text());assert len(data['cases'])==len(data['planned_cases'])
 for case,result in data['cases'].items():
  result['op_log_checks']={}
  caps=root/case/'frozen-caps.json'
  if caps.exists():
   bias=json.loads(caps.read_text())['stock_op'];result['initial_dc_supply_current_A']=-bias['i(Vsource)'];result['initial_dc_source_power_W']=result['initial_dc_supply_current_A']*result['configuration']['supply_V']
  if result.get('samples'):result['sample_hold_range_V']=[min(x['HOLD'] for x in result['samples']),max(x['HOLD'] for x in result['samples'])]
  for phase in ['stock-op','frozen-op']:
   path=root/case/phase/'ngspice.log'
   if path.exists():
    txt=path.read_text();result['op_log_checks'][phase]=dict(singular_warning='singular matrix' in txt,transient_op_fallback='Transient op started' in txt)
 batches.append(dict(run=name,summary_sha256=hashlib.sha256((root/'summary.json').read_bytes()).hexdigest(),**data))
nominal=json.loads((R/'simulations/three-frames.json').read_text())
comparisons=[]
for b in batches:
 for c in b['cases'].values():
  if c.get('completed') and c['name']=='warm-terminated':
   ref=nominal['samples'][:9];first=c['samples'][:9]
   c['warm_sample_difference_from_unterminated_nominal_V']=max(abs(x['HOLD']-y['HOLD']) for x,y in zip(ref,first))
for fine in batches:
 for coarse in batches:
  if fine['frames']>coarse['frames'] or fine['step_ns']>=coarse['step_ns']:continue
  for name,x in fine['cases'].items():
   y=coarse['cases'].get(name)
   if not y or x.get('configuration')!=y.get('configuration'):continue
   comp=dict(case=name,coarse=coarse['run'],fine=fine['run'],limit_V=10e-6,pass_screen=False,compared_frames=fine['frames'])
   if x.get('completed') and y.get('completed'):
    xx={(s['frame'],s['row'],s['column']):s for s in x['samples']};yy={(s['frame'],s['row'],s['column']):s for s in y['samples']};assert xx.keys()<=yy.keys()
    comp['max_sample_difference_V']=max(abs(xx[k]['HOLD']-yy[k]['HOLD']) for k in xx);comp['pass_screen']=comp['max_sample_difference_V']<10e-6
   comparisons.append(comp)
summary=dict(scope='Proposed readout timing and explicit external unused-pad terminations on the unchanged chip records. Conditional normal-operation evidence only, not startup, full distributed RC, final interface or tapeout qualification.',batches=batches,refinements=comparisons)
(R/'simulations/readout-followup.json').write_text(json.dumps(summary,indent=2)+'\n')
text='''# Readout timing and cold unused-pad follow-up — 24 September 2026

These tests address two specific results from the [load/corner screen](camera-operating-corners.md): insufficient acquisition time under larger capacitive loads, and a cold DC convergence problem at unconnected protected pads. They preserve the chip's extracted records and use explicit testbench/interface changes. A passing terminated-pad result applies to that changed interface; it does not retroactively qualify the unconnected-pad circuit or the existing carrier.

## Results

| Batch / case | Samples | Max matched DC error (µV) | Frame 2→3 (µV) | Selected screen |
|---|---:|---:|---:|---|
'''
labels=[];errors=[]
for b in batches:
 for name in b['planned_cases']:
  c=b['cases'][name];err=c.get('max_tracking_error_V');drift=c.get('frame_2_to_3_max_V')
  e=f'{err*1e6:.3f}' if err is not None else '—';d=f'{drift*1e6:.3f}' if drift is not None else '—';status='PASS' if c.get('screen_pass') else 'screen fail' if c.get('completed') else 'incomplete'
  text+=f"| {b['run']} / {name} | {len(c.get('samples',[]))}/{b['frames']*9} | {e} | {d} | {status} |\n"
  labels.append(name+f" ({b['frames']}f/{b['step_ns']:g}ns)");errors.append(err*1e6 if err is not None else np.nan)
text+='''
Screens retain <500 µV HOLD/ADCIN tracking error against matched DC charge-state references, correct brightness ordering and control states, sampled bias agreement within 1%, and the 0.1% in-trajectory MOS-capacitance approximation bound. Three-frame cases additionally require <50 µV frame-two/three change. Single-frame completion is not repeated-frame qualification.

## Slower acquisition proposal

The [combined heavy-load interface proposal](readout-interface-proposal.md) records the resistor, pad and controller changes needed for physical adoption. The proposed timing uses 50 µs column slots and 30 µs acquisition instead of 18 µs / 5 µs. Row selection starts at 2.060 ms (then every 1 ms), and the first acquisition runs from 2.075 to 2.105 ms. Three columns finish before row selection ends at about 2.220 ms, ahead of the next row reset at 2.250 ms. Reset and illumination history remain unchanged; readout occurs earlier, so this is a different exposure schedule. Each DC reference uses the actual captured nine-pixel charge state, not the old schedule's output voltages. The wider column spacing increases intra-row exposure skew, which matters for larger arrays.

This generic sample/hold proposal is not an ADS1115 conversion sequence or a validated large-array frame rate.

## Explicit unused-pad termination proposal

Four added external 100 kΩ resistors connect NC_P10, NC_P11, NC_P12 and NC_P15 to ground. They are present in the stock DC calculation, capacitor recalculation, frozen DC calculation, imaging transient and matched DC references. All original semiconductor records remain. This is a physical boundary condition with a straightforward DC path, not a relaxed simulator tolerance or an invisible numerical resistor.

The [physical termination proposal](unused-pad-termination-proposal.md) maps each resistor to its die pad. The current carrier leaves these pads unconnected. Adopting this condition requires a reviewed bond/board or on-chip termination implementation, followed by the affected electrical/physical checks. The original cold failures remain preserved. This does not qualify nonlinear power-up/protection.

'''
for b in batches:
 for name,c in b['cases'].items():
  text+=f"- {b['run']} / {name}: stock/frozen DC diagnostics {c.get('op_log_checks')}.\n"
  if 'warm_sample_difference_from_unterminated_nominal_V' in c:text+=f"  Maximum first-frame sample difference from the original warm unterminated camera: {c['warm_sample_difference_from_unterminated_nominal_V']*1e6:.3f} µV.\n"
  if c.get('error'):text+=f"  Recorded error: {c['error']}\n"
text+='\n## External bias and power tradeoff\n\nThe stronger-drive candidates change only the external PREF resistor from 49.9 kΩ to 24.9 kΩ 16.5 kΩ or 12.4 kΩ, in addition to the slower timing. These increase reference/output current and alter the buffer transfer curve. Matched DC references account for the changed transfer curve; this does not establish a reused optical/ADC calibration. Supply figures below are initial DC values, not peak or average frame power, and exclude external controller/ADC consumption.\n\n'
text+='| Case | PREF resistor (kΩ) | Initial supply (µA) | Initial source power (mW) | Sample HOLD range (V) |\n|---|---:|---:|---:|---|\n'
seen=set()
for b in batches:
 for name,c in b['cases'].items():
  if name in seen or 'initial_dc_supply_current_A' not in c:continue
  seen.add(name);r=c.get('sample_hold_range_V');vr=f'{r[0]:.6f}–{r[1]:.6f}' if r else '—'
  text+=f"| {name} | {c['configuration'].get('pref_ohm',49900)/1000:g} | {c['initial_dc_supply_current_A']*1e6:.3f} | {c['initial_dc_source_power_W']*1000:.6f} | {vr} |\n"
text+='\n## Numerical refinement\n\n'
for c in comparisons:text+=f"- {c['case']}: {c['coarse']} → {c['fine']}: {c.get('max_sample_difference_V',float('nan'))*1e6:.3f} µV maximum sample difference; frames compared: {c['compared_frames']}; <10 µV screen: {c['pass_screen']}.\n"
if not comparisons:text+='No new matched timestep refinement is included yet.\n'
text+='''
The settled-bias MOS-capacitor approximation is recomputed and checked at each condition; distributed wiring resistance, nonlinear startup and a full corner cross-product remain unqualified. See [tapeout readiness and scaling](tapeout-readiness.md) for the separate larger-array and manufacturing gates.

[Machine-readable results](../simulations/readout-followup.json) contain each configuration, sample, reference and approximation bound. Exact models, decks, full waveforms, operating points, logs and executed runner snapshots remain in the named `build/camera-operating-corners/` directories.

![Follow-up readout errors](assets/readout-followup.png)
'''
(R/'docs/readout-followup.md').write_text(text)
fig,ax=plt.subplots(figsize=(11,max(4,len(labels)*.42)),layout='constrained');y=np.arange(len(labels))
ax.barh(y,errors,color=['#318a65' if np.isfinite(x) and x<500 else '#b85b41' for x in errors]);ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xscale('symlog',linthresh=500);ax.set_xlim(left=0);ax.axvline(500,color='black',linestyle='--',label='500 µV screen');ax.set_xlabel('Maximum matched DC tracking error (µV)');ax.set_title('Proposed timing / explicit unused-pad termination');ax.legend();ax.grid(axis='x',alpha=.2)
fig.savefig(R/'docs/assets/readout-followup.png',dpi=140);plt.close(fig)
(R/'docs/readout-followup-section.html').write_text('<section id="readout-followup"><h2>Timing and cold-pad follow-up</h2><p><a href="readout-followup.md">Conditional results for proposed timing and unused-pad terminations</a>. <a href="tapeout-readiness.md">Tapeout readiness and array scaling</a>. Startup and distributed RC remain open.</p><img src="assets/readout-followup.png" alt="Follow-up readout errors" style="max-width:100%"></section>\n')
print('Published',len(labels),'follow-up cases')
