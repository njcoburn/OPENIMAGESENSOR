"""Analyze consecutive full-camera frames without changing the simulation model."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--reference');a=p.parse_args();D=R/'build/shared-circuit'/a.run
read=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
meta=json.loads((D/'result.json').read_text());names,d=read(D/'stream.raw');assert np.isfinite(d).all()
reference=R/'build/shared-circuit/staged-full-reset-norton-1us-20260921'
assert (D/'model.spice').read_bytes()==(reference/'model.spice').read_bytes()
assert (D/'test.spice').read_text()==(reference/'test.spice').read_text().replace('.tran 1000.0n 0.00425 0 1000.0n','.tran 1000.0n 0.01025 0 1000.0n')
n0,d0=read(reference/'stream.raw');pixels=json.loads((R/'simulations/final-chip-pixel-map.json').read_text())['pixels']
def value(node,t):
 assert t<=d[-1,0]
 return float(np.interp(t,d[:,0],d[:,names.index('v('+node.lower()+')')]))
samples=[];resets=[];frames=[]
for frame in range(3):
 f=[]
 for pixel in pixels:
  r,c=pixel['row'],pixel['column'];t=.002185+r*.001+c*18e-6+frame*.003
  rt=.001270009+r*.001+frame*.003
  if rt<=d[-1,0]:
   row={'frame':frame+1,'row':r,'column':c,'time_s':rt,'sense_V':value(pixel['sense'],rt),'reset_reference_V':value('sensor_3x3_0.VRESET',rt),'gate_V':value(pixel['reset_gate'],rt)}
   row['sense_minus_reference_V']=row['sense_V']-row['reset_reference_V'];resets.append(row)
  if t>d[-1,0]:continue
  s={'frame':frame+1,'row':r,'column':c,'time_s':t,'photocurrent_pA':[0,80,240][(c+2*r)%3]}
  s.update({n:value(n,t) for n in ['VDD','PAD_BIAS','PAD_PREF','HOLD','ADCIN','PAD_BUF','sensor_3x3_0.OUT']})
  s['controls_valid']=all(abs(value('CTL_'+kind+str(i),t)-(1 if (kind=='ROW' and i==r) or (kind=='SEL' and i==c) else 0))<1e-8 for kind in ['ROW','SEL','RST'] for i in range(3)) and abs(value('ACQ',t)-3.3)<1e-8 and abs(value('RSTADC',t))<1e-8
  s['sense_V']=value(pixel['sense'],t);s['acquisition_error_V']=s['HOLD']-s['ADCIN'];samples.append(s);f.append(s)
 frames.append({'frame':frame+1,'sample_count':len(f),'brightness_order_correct':len(f)==9 and all(x['HOLD']>y['HOLD'] for x in f for y in f if x['row']==y['row'] and x['photocurrent_pA']<y['photocurrent_pA'])})
changes=[]
for frame in [1,2]:
 previous=[s for s in samples if s['frame']==frame];current=[s for s in samples if s['frame']==frame+1]
 if len(previous)==len(current)==9:
  changes.append({'from_frame':frame,'to_frame':frame+1,'pixel_differences_V':[y['HOLD']-x['HOLD'] for x,y in zip(previous,current)],'max_abs_difference_V':max(abs(y['HOLD']-x['HOLD']) for x,y in zip(previous,current))})
reset_changes=[]
for frame in [1,2]:
 previous=[s for s in resets if s['frame']==frame];current=[s for s in resets if s['frame']==frame+1]
 if len(previous)==len(current)==9:reset_changes.append({'from_frame':frame,'to_frame':frame+1,'max_abs_sense_difference_V':max(abs(y['sense_V']-x['sense_V']) for x,y in zip(previous,current))})
common=[abs(s['HOLD']-float(np.interp(s['time_s'],d0[:,0],d0[:,n0.index('v(hold)')]))) for s in samples if s['frame']==1]
pairs=sorted({tuple(l.split()[1:3]) for l in (D/'model.spice').read_text().splitlines() if l.startswith('Cfreeze')})
def vector(n):return np.zeros(len(d)) if n.upper() in ['GND','0'] else d[:,names.index('v('+n.lower()+')')]
ranges=[{'a':x,'b':y,'min_V':float(np.min(vector(x)-vector(y))),'max_V':float(np.max(vector(x)-vector(y)))} for x,y in pairs]
result={'run':a.run,'execution':meta,'scope':'Three-frame normal-operation candidate, unchanged full extracted capacitance model with bias-frozen MOS caps; no startup, distributed-R, corner or fabrication qualification.','frames':frames,'samples':samples,'reset_checkpoints':resets,'frame_changes':changes,'reset_changes':reset_changes,'first_frame_max_difference_from_reference_V':max(common) if common else None,'max_acquisition_error_V':max(abs(s['acquisition_error_V']) for s in samples) if samples else None,'max_reset_sense_to_reference_error_V':max(abs(s['sense_minus_reference_V']) for s in resets) if resets else None,'frozen_cap_bias_ranges':ranges,'all_27_samples_present':len(samples)==27,'all_acquisition_controls_valid':len(samples)==27 and all(x['controls_valid'] for x in samples),'all_frames_brightness_order_correct':all(f['brightness_order_correct'] for f in frames),'model_sha256':hashlib.sha256((D/'model.spice').read_bytes()).hexdigest(),'frame_repeatability_limit_V':50e-6,'frame_repeatability_pass':len(changes)==2 and changes[-1]['max_abs_difference_V']<50e-6,'stability_note':'Existing COMPLETION_PLAN.md screen: frame 2-to-3 difference below 50 microvolts; this is an engineering screen, not a measured ADC specification.'}
prior_path=R/'build/shared-circuit/three-frame-reset-norton-20260923/result.json'
if a.run!='three-frame-reset-norton-20260923' and prior_path.exists():
 result['prior_watchdog_attempt']=json.loads(prior_path.read_text())
 assert (prior_path.parent/'test.spice').read_bytes()==(D/'test.spice').read_bytes()
if (D/'timeout-prefix-check.json').exists():result['retry_prefix_check']=json.loads((D/'timeout-prefix-check.json').read_text())
reference_result=None
if a.reference:
 refpath=R/'build/functional-dc-reference'/a.reference/'result.json';reference_result=json.loads(refpath.read_text())
 assert reference_result['source']==a.run and reference_result['model_sha256']==result['model_sha256']
 assert reference_result['source_raw_sha256']==hashlib.sha256((D/'stream.raw').read_bytes()).hexdigest()
 matches={(s['frame'],s['row'],s['column']):s for s in samples}
 for entry in reference_result['samples']:
  if not entry['completed']:continue
  sample=matches[entry['frame'],entry['row'],entry['column']]
  assert abs(sample['HOLD']-entry['transient_hold_V'])<1e-12
  sample['dc_hold_V']=entry['dc']['v(HOLD)'];sample['hold_minus_dc_V']=entry['hold_minus_dc_mV']/1000
  sample['adc_minus_dc_V']=entry['adc_minus_dc_mV']/1000
  sample['dc_bias_relative_errors']={n:abs(sample[n]-entry['dc']['v('+n+')'])/abs(entry['dc']['v('+n+')']) for n in ['VDD','PAD_BIAS','PAD_PREF']}
 good=[s for s in samples if 'dc_hold_V' in s]
 result['dc_reference']={'run':a.reference,'completed':reference_result['completed'],'sample_count':len(good),'max_hold_minus_dc_V':max(abs(s['hold_minus_dc_V']) for s in good) if good else None,'max_adc_minus_dc_V':max(abs(s['adc_minus_dc_V']) for s in good) if good else None,'limit_V':.0005,'tracking_screen_pass':len(good)==27 and all(max(abs(s['hold_minus_dc_V']),abs(s['adc_minus_dc_V']))<.0005 for s in good),'max_bias_relative_error':max(max(s['dc_bias_relative_errors'].values()) for s in good) if good else None,'bias_1percent_screen_pass':len(good)==27 and all(max(s['dc_bias_relative_errors'].values())<.01 for s in good)}
(R/'simulations/three-frames.json').write_text(json.dumps(result,indent=2)+'\n')
rows=[]
for pixel in pixels:
 r,c=pixel['row'],pixel['column'];ss=[s for s in samples if s['row']==r and s['column']==c];vs=[f"{s['HOLD']:.9f}" for s in ss]+['—']*(3-len(ss));delta=f"{(ss[2]['HOLD']-ss[1]['HOLD'])*1e6:.3f}" if len(ss)==3 else '—';rows.append(f"| R{r}C{c} | "+' | '.join(vs)+f' | {delta} |')
completed=meta['completed'] and len(samples)==27
text=f'''# Three consecutive full-camera frames — 2026-09-24

**{'All three frames complete, with 27/27 samples.' if completed else 'The run did not complete all three frames; retained samples are partial evidence.'}** Expected brightness ordering: {result['all_frames_brightness_order_correct']}. Valid reset/row/column/acquisition control states at all sample times: {result['all_acquisition_controls_valid']}. Last simulated time: {d[-1,0]*1000:.9f} ms. Runtime: {meta['seconds']:.1f} s. Watchdog timeout: {meta['timed_out']}.

The full extracted 3×3 camera model is byte-identical to the successful single-frame reference. The only deck change is extending the transient stop from 4.25 to 10.25 ms; the original stimulus already contains all three frame cycles. It retains all fifteen clamp domains, the equivalent 2 V / 1 Ω reset source, the original 2 Ω supply and control timing, KLU/Trap settings and 1 µs maximum timestep. No simulator tolerance was relaxed.

| Pixel | Frame 1 HOLD (V) | Frame 2 HOLD (V) | Frame 3 HOLD (V) | Frame 3 − 2 (µV) |
|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'\n\n'
for change in changes:text+=f"Maximum absolute frame {change['from_frame']}→{change['to_frame']} change: **{change['max_abs_difference_V']*1e6:.3f} µV**.\n\n"
text+=f"Frame-two/three repeatability screen (<50 µV): **{result['frame_repeatability_pass']}**.\n\n"
text+=f"First-frame agreement with the saved 1 µs reference: {result['first_frame_max_difference_from_reference_V']*1e6 if common else 'unavailable'} µV maximum difference. Acquisition-end HOLD versus ADCIN error: {result['max_acquisition_error_V']*1e6 if samples else 'unavailable'} µV maximum. This checks tracking at the selected instant, not settling against a separately established DC transfer target.\n\n"
text+='## Reset and approximation checks\n\n'
text+=f"Reset sense voltages are sampled 1 ns before each reset falling edge starts, after the reset pulse plateau. Maximum sense-to-reset-reference difference: {result['max_reset_sense_to_reference_error_V']*1e6 if resets else 'unavailable'} µV. This checks reset consistency; it does not simulate reset noise or prove absence of image lag under changing illumination.\n\n"
for change in reset_changes:text+=f"Maximum reset sense difference, frame {change['from_frame']}→{change['to_frame']}: {change['max_abs_sense_difference_V']*1e6:.6f} µV.\n\n"
text+=f"All sixteen frozen-capacitor voltage pairs remain between {min(x['min_V'] for x in ranges):.6f} and {max(x['max_V'] for x in ranges):.6f} V. The high-bias capacitance approximation remains in its settled operating range; this is not nonlinear startup qualification.\n\n"
text+='''## Scope and remaining work

These are electrical simulations with full-layout extracted wiring capacitance and the existing bias-frozen MOS-capacitor approximation. Distributed wiring resistance, nonlinear startup, process/voltage/temperature corners and optical/noise calibration remain unqualified. Constant illumination repeats across frames; changing-scene response is not tested here. The external load is the existing fast regression sample/hold fixture: 18 µs column slots, 5 µs acquisition, 100 pF board capacitance and 20 pF sampling capacitance. It is not an ADS1115 conversion model.

The retained engineering screen in [COMPLETION_PLAN.md](../COMPLETION_PLAN.md) requires frame-two/three differences below 50 µV and sample refinement below 10 µV. The earlier 5 µs-to-1 µs refinement differed by 2.778 µV. ADC tracking must also be compared against the matched DC transfer reference with its 0.5 mV screen; HOLD versus ADCIN alone does not establish that result.

[Machine-readable results](../simulations/three-frames.json) include every reset and acquisition checkpoint. Exact decks, full waveforms, logs and hashes are retained in the named build directory and under `checkpoints/three-frames/`.
'''
if reference_result:
 dc=result['dc_reference']
 text+='\n## Matched static transfer reference\n\n'
 text+=f"Completed DC references: {dc['sample_count']}/27. Tracking screen (<0.5 mV): **{dc['tracking_screen_pass']}**. Maximum HOLD versus DC error: {dc['max_hold_minus_dc_V']*1e6 if dc['sample_count'] else 'unavailable'} µV; maximum ADCIN versus DC error: {dc['max_adc_minus_dc_V']*1e6 if dc['sample_count'] else 'unavailable'} µV. Bias agreement within 1%: **{dc['bias_1percent_screen_pass']}**, maximum relative error {dc['max_bias_relative_error']}.\n\n"
 text+='Each reference pins all nine pixel sense voltages to their captured charge-state voltages and holds the control inputs at that acquisition instant, then solves DC with the unchanged chip and external load. These added voltage sources exist only in the reference calculation. They are not inserted into the imaging transient and do not represent a physical design change. Bias agreement at sample times does not qualify a supply-ramp startup.\n'
if 'prior_watchdog_attempt' in result:
 old=result['prior_watchdog_attempt']
 text+=f"\n## Preserved watchdog attempt\n\nThe first attempt was stopped by its {old['timeout_s']:.0f} s watchdog at {old['end_s']*1000:.9f} ms with 21 samples and no solver error. The identical deck was rerun with a {meta['timeout_s']:.0f} s allowance. No circuit, timestep, tolerance or illumination change accompanied the retry. Both outcomes and their exact evidence are retained.\n"
if result.get('retry_prefix_check',{}).get('binary_prefix_identical'):
 text+='\nThe rerun reproduces the entire saved binary trajectory of the watchdog attempt byte for byte, including every captured time point and internal vector through the earlier cutoff.\n'
text+='\n![Consecutive-frame voltages and differences](assets/three-frames.png)\n'
(R/'docs/three-frames.md').write_text(text)
fig,axes=plt.subplots(3,1,figsize=(10,9),layout='constrained')
for frame in range(1,4):
 ss=[s for s in samples if s['frame']==frame];axes[0].plot([s['row']*3+s['column'] for s in ss],[s['HOLD'] for s in ss],marker='o',label=f'Frame {frame}')
for i,c in enumerate(changes):axes[i+1].plot(range(9),np.array(c['pixel_differences_V'])*1e6,marker='o',label=f"Frame {c['to_frame']} − {c['from_frame']}")
axes[2].axhline(50,color='gray',linestyle='--',label='±50 µV repeatability screen');axes[2].axhline(-50,color='gray',linestyle='--')
for ax in axes:ax.set_xticks(range(9),[f'R{r}C{c}' for r in range(3) for c in range(3)]);ax.grid(alpha=.2);ax.legend()
axes[0].set(ylabel='Sampled voltage (V)',title='Full extracted camera: consecutive frames');axes[1].set(ylabel='Frame difference (µV)');axes[2].set(ylabel='Frame difference (µV)',xlabel='Pixel in readout order')
fig.savefig(R/'docs/assets/three-frames.png',dpi=150);plt.close(fig)
print(json.dumps({k:result[k] for k in ['all_27_samples_present','all_frames_brightness_order_correct','frame_changes','frame_repeatability_pass','reset_changes','max_acquisition_error_V','dc_reference'] if k in result},indent=2))
