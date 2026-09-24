"""Summarize staged runs and their bounded full-camera follow-up."""
from pathlib import Path
import hashlib,json,re,runpy
import numpy as np
R=Path(__file__).resolve().parents[1]
read_raw=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
paths=[]
for directory in ['staged-readout-20260921','staged-protection-20260921','staged-protection-controls-20260921']:
 paths+=sorted((R/'build'/directory).glob('*/result.json'))
cases=[]
for p in paths:
 x=json.loads(p.read_text());x['path']=str(p.parent.relative_to(R));log=(p.parent/'ngspice.log').read_text();x['solver']='SPARSE 1.3' if 'Using SPARSE 1.3' in log else 'KLU';x['compatibility']='none' if 'No compatibility mode selected!' in log else 'see log';x['included_files_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.parent.glob('*.spice')};cases.append(x)
fullpath=R/'build/shared-circuit/staged-full-reset-norton-20260921';full=json.loads((fullpath/'result.json').read_text());names,data=read_raw(fullpath/'stream.raw')
full['samples']=[]
for r in range(3):
 for c in range(3):
  t=.002185+r*.001+c*18e-6
  if t>data[-1,0]:continue
  v={n:float(np.interp(t,data[:,0],data[:,names.index('v('+n.lower()+')')])) for n in ['VDD','ADCIN','HOLD']};full['samples'].append(dict(row=r,column=c,time_s=t,photocurrent_pA=[0,80,240][(c+2*r)%3],**v))
full['brightness_order_correct']=len(full['samples'])==9 and all(x['HOLD']>y['HOLD'] for x in full['samples'] for y in full['samples'] if x['row']==y['row'] and x['photocurrent_pA']<y['photocurrent_pA'])
full['max_acquisition_error_V']=max(abs(x['HOLD']-x['ADCIN']) for x in full['samples']) if full['samples'] else None
pairs=sorted({tuple(l.split()[1:3]) for l in (fullpath/'model.spice').read_text().splitlines() if l.startswith('Cfreeze')})
def node_values(node):
 return np.zeros(len(data)) if node.upper() in ['GND','0'] else data[:,names.index('v('+node.lower()+')')]
full['frozen_cap_bias_ranges']=[{'a':aa,'b':bb,'min_V':float(np.min(node_values(aa)-node_values(bb))),'max_V':float(np.max(node_values(aa)-node_values(bb)))} for aa,bb in pairs]
refpath=R/'build/shared-circuit/staged-full-reset-norton-1us-20260921'
refinement=json.loads((refpath/'result.json').read_text())
rnames,rd=read_raw(refpath/'stream.raw');refinement['samples']=[]
for sample in full['samples']:
 t=sample['time_s']
 if t>rd[-1,0]:continue
 value=float(np.interp(t,rd[:,0],rd[:,rnames.index('v(hold)')]))
 refinement['samples'].append({**{k:sample[k] for k in ['row','column','photocurrent_pA','time_s']},'HOLD':value,'difference_from_5us_V':value-sample['HOLD']})
refinement['max_sample_difference_V']=max(abs(x['difference_from_5us_V']) for x in refinement['samples']) if refinement['samples'] else None
refinement['brightness_order_correct']=len(refinement['samples'])==9 and all(x['HOLD']>y['HOLD'] for x in refinement['samples'] for y in refinement['samples'] if x['row']==y['row'] and x['photocurrent_pA']<y['photocurrent_pA'])
assert (refpath/'model.spice').read_bytes()==(fullpath/'model.spice').read_bytes()
assert (refpath/'test.spice').read_text()==(fullpath/'test.spice').read_text().replace('.tran 5000n 0.00425 0 5000n','.tran 1000.0n 0.00425 0 1000.0n') or (refpath/'test.spice').read_text()==(fullpath/'test.spice').read_text().replace('.tran 5000.0n 0.00425 0 5000.0n','.tran 1000.0n 0.00425 0 1000.0n')
oldnames,old=read_raw(R/'build/functional-camera-diagnostic/reset-edge-internal-20260920/stream.raw')
shared=[]
for s in full['samples']:
 if s['time_s']<=old[-1,0]:shared.append(abs(s['HOLD']-float(np.interp(s['time_s'],old[:,0],old[:,oldnames.index('v(hold)')]))))
full['shared_original_sample_count']=len(shared);full['max_original_sample_difference_V']=max(shared) if shared else None
assert (fullpath/'model.spice').read_bytes()==(R/'build/functional-camera-diagnostic/reset-edge-internal-20260920/model.spice').read_bytes()
audit=json.loads((fullpath/'partition.json').read_text());assert audit['reset_driver_form']=='norton' and audit['driver_form']=='thevenin' and audit['supply_control']=='original' and not audit['omitted_devices']
stage5=next(x for x in cases if x['path'].endswith('/stage5'));fixed=next(x for x in cases if x['path'].endswith('/stage6-reset-norton'))
delta=max(abs(x['HOLD']-y['HOLD']) for x,y in zip(stage5['samples'],fixed['samples']))
result={'scope':'Staged C-only unfilled array plus schematic readout and extracted protection devices; then original full-layout candidate with only reset-reference source representation changed. No fabrication/startup/RC qualification.','cases':cases,'full_camera_followup':full,'timestep_refinement':refinement,'stage5_vs_stage6_norton_max_sample_difference_V':delta,'original_full_camera_model_unchanged':True}
(R/'simulations/staged-integration.json').write_text(json.dumps(result,indent=2)+'\n')
labels={0:'Array control with camera scan timing',1:'Shared column bias and multiplexer',2:'Output buffer',3:'ADC acquisition load',4:'2 Ω supply / 1 Ω reset reference',5:'Extracted signal-pad protection',6:'Unused pads and rail diodes',7:'All fifteen clamp domains + frozen MOS caps'}
rows=[]
for x in cases:
 variant=x.get('variant','');label=labels[x['stage']]
 if variant=='6-rails':label='Signal pads + rail diodes only'
 if variant=='6-unused':label='Signal pads + unused pads only'
 if variant=='6-reset-norton':label='Stage 6 with equivalent reset-source equation'
 status='Frame complete' if x['completed'] else 'Watchdog timeout' if x['timed_out'] else 'Solver abort'
 size=f"{x.get('rows',3)}×{x.get('columns',3)}"
 rows.append(f"| {size} | {label} | {status} | {x.get('end_s',0)*1000:.6f} | {len(x.get('samples',[]))} |")
status='completed a full frame' if full['completed'] else ('hit its 300 s watchdog' if full['timed_out'] else 'aborted in the solver')
text='''# Staged camera integration — 2026-09-21

**The original full extracted 3×3 camera now completes its first full frame after an electrically equivalent reset-source rewrite.** All nine pixels have the expected brightness ordering; the first six agree with the original failure trace within 0.060 µV. The chip model is byte-identical. This is a normal-operation candidate with bias-frozen MOS capacitors, not full electrical or fabrication qualification.

The preceding shared readout, output buffer, ADC sampling and finite supply stages also complete frames on both 3×3 and 4×4 arrays. Adding the extracted signal-pad devices completes a 3×3 frame.

The first explicit failure in this staged series appears after adding rail diodes. The smaller paired control completes after replacing the reset source with its identical terminal-current equation. That result led to the same controlled source rewrite on the original full camera. The successful frame supports a numerical workaround; it does not show a physical pixel-wiring defect or fully explain the solver's internal failure.

| Array | Cumulative stage / control | Outcome | Last simulated time (ms) | Pixel samples |
|---|---|---|---:|---:|
'''+ '\n'.join(rows)+f'''

The ADC sampling-capacitor error against its input at acquisition end is below 1 µV in the completed readout/protection cases. Adding unused pads and rail diodes with the equivalent source changes the nine sampled voltages relative to the signal-pad-only stage by at most **{delta*1e6:.4f} µV**. That amplitude agreement supports the small-control numerical diagnosis; it is not a tolerance or accuracy qualification.

## What was restored

Stages 0–4 use the previously verified unfilled array-core C-only extraction, with its exact extracted devices and all wire capacitances. Stage 0 reruns that array under the camera's initial reset and sequential column schedule. Stage 1 replaces independent column resistor loads with the shared bias mirror and column mux, with a fixed 1 pF / 1 TΩ output measurement load. Stage 2 adds the schematic PMOS buffer and a 1 MΩ / 1 pF load; stage 3 replaces that buffer load with the existing bondwire, board and ADC sample/reset-switch model. Stage 4 restores the 2 Ω supply and 1 Ω reset-reference impedance. Control drivers are 100 Ω throughout, with the existing 100 kΩ pulls.

The 4×4 run uses the complete stage-4 chain and a 78 µs row-select window to fit four column samples. Each run covers one frame, with startup reset released at 1.22 ms, then sequential row resets and acquisitions. This does not establish multiframe steady state or corner behavior.

Stage 5 adds all 143 extracted signal-pad device/resistor records, preserving their dimensions and connectivity. Stage 6 adds the remaining 128 non-clamp records: 96 rail diodes and 32 diodes on four unused pads. Separate controls distinguish those additions. Stage 7 restores all 2,040 clamp-device records and the same 1,680 frozen MOS capacitors used by the normal-operation candidate. It times out before completing a frame; this is not an explicit timestep abort.

These staged coupons omit pad, clamp and shared-readout **wiring** PEX and density-fill capacitance. The added protection devices retain their intrinsic model capacitance. The clamp MOS capacitors remain bias-frozen approximations. None of these is a newly routed full-camera layout or distributed-R extraction.

## Equivalent reset-source control

The original source/resistor pair is `Vreset RESETDRV 0 2` followed by `Rreset RESETDRV PAD_VRESET 1`. Its external terminal current is exactly `I=(V(PAD_VRESET)-2)/1`; the Norton form uses that equation directly. No device, voltage, resistance, timing or tolerance changes in the stage-6 paired test. The internal `RESETDRV` node has no other connections. The stage-6 model file is byte-identical between failed and completed cases.

Stage 6 aborts at about 2.180003 ms, during the **first ADC acquisition edge**. The rail-only control also aborts there; the unused-pad-only control completes. Both failed logs name `vreset#branch`, but an error-node name alone is not a causal diagnosis.

## Original full-layout follow-up

The follow-up retains the full original model byte for byte, all fifteen clamp domains, original 2 Ω supply, nine original control drivers, original timing and tolerances. Only the 2 V / 1 Ω reset reference is written in Norton form. The stop target is extended to 4.25 ms so all nine samples can be checked.

This run **{status}**, reaching **{full.get('end_s',0)*1000:.9f} ms**, with **{len(full['samples'])}/9 samples**. It retains {full['shared_original_sample_count']} samples in common with the original failure trace; maximum difference is {full['max_original_sample_difference_V'] if shared else 'unavailable'} V. The full run crosses the original 3.27002 ms failure and reaches the final row's readout. No protection domain or wire capacitor was removed. Acquisition-end HOLD versus ADCIN error is {full['max_acquisition_error_V']*1e6:.3f} µV maximum. The frozen-capacitor plate voltages remain between {min(x['min_V'] for x in full['frozen_cap_bias_ranges']):.6f} and {max(x['max_V'] for x in full['frozen_cap_bias_ranges']):.6f} V over the captured frame; this is the settled high-bias range of the approximation, not a startup validation.

A **1 µs maximum-step refinement** {'completes the frame' if refinement['completed'] else 'does not complete the frame'}, retaining {len(refinement['samples'])}/9 samples. Maximum held-voltage difference from the 5 µs run is {refinement['max_sample_difference_V']*1e6 if refinement['samples'] else 'unavailable'} µV. The refinement changes only the transient step settings; its full chip model and all other deck lines are identical.

The staged coupons use Gear integration, a 200 ns maximum step, SPARSE 1.3 and default compatibility. The full-layout follow-up deliberately retains the original Trap settings, 5 µs maximum step, KLU and hsa compatibility. It is a controlled comparison against the archived **full-layout** run, not a one-factor comparison against stage 7.

## Remaining gates

Run repeated full-chip frames and check stability, establish the DC transfer/settling reference, then test load and process/voltage/temperature variation. Startup with nonlinear MOS capacitors and distributed wiring resistance remains unqualified. The 4×4 success uses array-core PEX plus schematic readout; a larger full camera still needs its own routed/extracted layout.

## Evidence and reproduction

[Machine-readable results](../simulations/staged-integration.json) retain sampled voltages, outcomes, source/deck/include hashes, errors and timeouts. Exact decks, layouts' extracted models, traces and logs are archived under `checkpoints/staged-integration/`.

Run inside the tools container, using fresh output paths:

```sh
python scripts/stage-array-readout.py --output /foss/designs/build/<new-readout-run>
python scripts/stage-array-protection.py --output /foss/designs/build/<new-protection-run>
python scripts/stage-array-protection.py --output /foss/designs/build/<new-controls-run> --cases 6-rails 6-unused 6-reset-norton
python scripts/diagnose-shared-circuit.py <new-full-run> --all-clamps --reset-driver norton --stop-ms 4.25 --timeout 300
```

The protection script intentionally uses the archived named stage-4 baseline; the report script consolidates the named runs from this investigation. Existing results are never overwritten by a simulation runner.
'''
(R/'docs/staged-integration.md').write_text(text)
print(json.dumps({'cases':len(cases),'completed':sum(x['completed'] for x in cases),'full_completed':full['completed'],'full_end_s':full.get('end_s'),'full_samples':len(full['samples']),'refinement_completed':refinement['completed'],'refinement_max_difference_V':refinement['max_sample_difference_V']},indent=2))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,sharey=True,layout='constrained')
for r,ax in enumerate(axes):
 start=.00217+r*.001;mask=(data[:,0]>=start)&(data[:,0]<=start+65e-6)
 for node,label,color in [('adcin','ADC input','#2563eb'),('hold','Sampling capacitor','#b45309')]:
  ax.plot((data[mask,0]-start)*1e6,data[mask,names.index('v('+node+')')],label=label,color=color,lw=1.2)
 for s in [s for s in full['samples'] if s['row']==r]:
  t=(s['time_s']-start)*1e6;ax.scatter(t,s['HOLD'],color='#111827',s=20,zorder=5);ax.annotate(f"C{s['column']} · {s['photocurrent_pA']} pA\n{s['HOLD']:.6f} V",(t,s['HOLD']),xytext=(0,12),textcoords='offset points',ha='center',fontsize=8)
 ax.set(title=f'Row {r}',ylabel='Voltage (V)',ylim=(-.05,2.85));ax.grid(alpha=.2)
axes[0].legend(loc='lower right');axes[-1].set(xlabel='Time after row-select rise (µs)',xlim=(0,65))
fig.suptitle('Full extracted 3×3 camera: nine completed samples\nEquivalent reset source; normal-operation candidate with bias-frozen MOS capacitors',fontsize=12)
fig.savefig(R/'docs/assets/staged-integration.png',dpi=150);plt.close(fig)
p=R/'docs/staged-integration.md';s=p.read_text();s=s.replace('## Evidence and reproduction','![All three rows of the completed full-camera frame](assets/staged-integration.png)\n\n## Evidence and reproduction');p.write_text(s)
