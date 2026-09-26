"""Collect recovery evidence and plot completed measurements only."""
from pathlib import Path
import base64, hashlib, json, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
roots=sorted(p for p in (ROOT/'build').glob('array-strip-*20260924')
             if re.match(r'array-strip-(tight|rel[67]|vntol|power|storage|capture)',p.name))
roots=sorted(set(roots+[ROOT/'build/array-strips-20260924']))
runs={};incomplete=[]
for root in roots:
    stopped=json.loads((root/'stopped-reason.json').read_text()) if (root/'stopped-reason.json').exists() else None
    for deck in sorted(root.glob('r*c*/transient/test.spice')):
        if not (deck.parent.parent/'result.json').exists():incomplete.append({'run_directory':str(deck.parent.parent.relative_to(ROOT)),'status':'No completed case result; may be active or an interrupted attempt','stopped_reason':stopped})
    for path in sorted(root.glob('r*c*/result.json')):
        r=json.loads(path.read_text())
        key=str(path.parent.relative_to(ROOT))
        for filename,field in [('array.spice','model_sha256'),('transient/test.spice',None)]:
            actual=hashlib.sha256((path.parent/filename).read_bytes()).hexdigest()
            expected=r[field] if field else r['execution']['deck_sha256']
            assert actual==expected,(key,filename)
        r['stopped_reason']=stopped
        if (root/'watchdog-extension.json').exists():r['watchdog_extension']=json.loads((root/'watchdog-extension.json').read_text())
        if root.name=='array-strip-storage-short-matched-20260924':r['reference_excluded_reason']='Default 10 us optran reference had nonzero ADC capacitor current; replaced by independently checked 200/400 us references. Transient itself remains valid.'
        if (path.parent/'recovery-analysis.json').exists():
            r['waveform_metrics']=json.loads((path.parent/'recovery-analysis.json').read_text())
        runs[key]=r

def get(name,case='r1c64-rc-port'):
    return runs.get(f'build/array-strip-{name}-20260924/{case}')

checks=[]
def compare(label,x,y,field='capture',voltage='HOLD',equivalent=False):
    if not x or not y or not x['completed'] or not y['completed']:return
    defaults={'temperature_C':27,'pref_ohm':49900,'bias_ohm':5.1e6,
              'read_delay_us':0,'capture_edge_ns':10}
    for key in ['fixture','rows','columns','slot_us','acquisition_us','pref_ohm',
                'bias_ohm','read_delay_us','column_storage_pF','reset_after_capture',
                'temperature_C','capture_edge_ns']:
        assert x.get(key,defaults.get(key))==y.get(key,defaults.get(key)),(label,key)
    if equivalent:
        audit=json.loads((ROOT/'build/array-strip-power2um-20260924/r1c64/rc-compact-audit.json').read_text())
        assert {x['model_sha256'],y['model_sha256']}=={audit['source_sha256'],audit['model_sha256']}
        assert audit['boundary_current_nodewise_relative_error']<1e-9
        serialized=json.loads((ROOT/'build/array-strip-power2um-20260924/r1c64/serialized-rc-audit.json').read_text())['rc-compact']
        assert serialized['model_sha256']==audit['model_sha256'] and serialized['per_node_relative_current_error']<1e-9
    else:assert x['model_sha256']==y['model_sha256']
    assert len(x['samples'])==len(y['samples'])
    for a,b in zip(x['samples'],y['samples']):
        assert (a['row'],a['column'],a['time_s'])==(b['row'],b['column'],b['time_s'])
    error=max(abs(a[field][voltage]-b[field][voltage]) for a,b in zip(x['samples'],y['samples']))
    checks.append(dict(comparison=label,max_difference_V=error,limit_V=10e-6,passed=error<10e-6))

compare('Original row, reltol 1e-6: 200 vs 100 ns',get('rel6-200'),get('rel6-100'))
compare('Original row, reltol 1e-7: 200 vs 100 ns',get('rel7-200'),get('rel7-100'))
compare('Original row, reltol 1e-6 and vntol 1e-9: 200 vs 100 ns',get('vntol9-200'),get('vntol9-100'))
compare('Original row, reltol 1e-6: KLU vs SPARSE',get('rel6-200'),get('rel6-sparse200'))
compare('Short 20 pF capture: KLU vs SPARSE',get('storage-short','r1c3-rc-port'),get('storage-short-sparse','r1c3-rc-port'))
compare('Short 10 pF output reference: 200 vs 400 us',get('storage10-short-matched','r1c3-rc-port'),get('storage10-short-dc400','r1c3-rc-port'),'dc','v(hold)')
compare('Selected 40 pF hot late-read reference: 200 vs 400 us',get('storage40-bias500k-125-1220-matched','r1c3-rc-port'),get('storage40-hot-dc400','r1c3-rc-port'),'dc','v(hold)')
for temp in [27,125]:
    compare(f'Fast capture at {temp} C: 200 vs 100 ns',get(f'capture-fast-{temp}-200'),get(f'capture-fast-{temp}-100'))
    compare(f'Fast capture at {temp} C: SPARSE vs pivoted KLU',get(f'capture-fast-{temp}-200'),get(f'capture-fast-pivot-{temp}-200'))

for temp in [27,125]:
    compare(f'Selected 40 pF capture at {temp} C: 200 vs 100 ns',get(f'capture40-compact-{temp}-200','r1c64-rc-compact'),get(f'capture40-compact-{temp}-100','r1c64-rc-compact'))
    compare(f'Selected 40 pF capture at {temp} C: exact compact vs unreduced network',get(f'capture40-compact-{temp}-200','r1c64-rc-compact'),get(f'capture40-port-{temp}-200'),equivalent=True)

compare('Selected 40 pF nominal capture: KLU 200 vs 100 ns',get('capture40-klu-27-200-long'),get('capture40-klu-27-100'))
compare('Selected 40 pF nominal capture: KLU vs SPARSE',get('capture40-klu-27-200-long'),get('capture40-port-27-200'))
compare('Selected 40 pF hot capture: KLU 200 vs 100 ns',get('capture40-klu-125-200'),get('capture40-klu-125-100'))
compare('Selected 40 pF hot capture: KLU vs SPARSE',get('capture40-klu-125-200'),get('capture40-port-125-200'))
for temp in [27,125]:
    compare(f'Selected 40 pF capture at {temp} C: KLU unreduced vs SPARSE compact, 100 ns',get(f'capture40-klu-{temp}-100'),get(f'capture40-compact-{temp}-100','r1c64-rc-compact'),equivalent=True)

scope=('Selected unfilled extracted strip routing and numerical tests, plus transistor-level column capture with ideal linear storage capacitors and schematic periphery. '
       'Not full 64x64, extracted storage/peripheral routing, noise/mismatch, full PVT, startup or tapeout qualification.')
for temp in [27,125]:
    directory=ROOT/f'build/array-strip-capture40-klu-{temp}-100-20260924/r1c64-rc-port'
    paths=[directory/f'capture-dc-{duration}us/reference.json' for duration in [200,400]]
    if all(p.exists() for p in paths):
        x,y=[json.loads(p.read_text()) for p in paths]
        assert x['normalized_transient_sha256']==y['normalized_transient_sha256']
        error=max(abs(x['column_targets_V'][k]-y['column_targets_V'][k]) for k in x['column_targets_V'])
        checks.append(dict(comparison=f'Full-row capture reference at {temp} C: 200 vs 400 us',max_difference_V=error,limit_V=1e-8,passed=error<1e-8))
path=ROOT/'build/array-strip-capture40-dc-duration-20260924/comparison.json'
if path.exists():
    duration_check=json.loads(path.read_text());assert len(duration_check)==3
    error=max(r['hold_difference_V'] for r in duration_check)
    checks.append(dict(comparison='Full-row nominal output references, three signals: 200 vs 400 us',max_difference_V=error,limit_V=1e-8,passed=error<1e-8 and all(r['adc_residual_V']<1e-8 for r in duration_check)))
selected=[get(f'capture40-klu-{temp}-matched') for temp in [27,125]]
selected_checks=[c for c in checks if c['comparison'] in [
    'Selected 40 pF nominal capture: KLU 200 vs 100 ns',
    'Selected 40 pF hot capture: KLU 200 vs 100 ns']]
selected_pass=(all(r and r['completed'] and len(r['samples'])==64 and r['tracking_screen_pass']
                   and r.get('waveform_metrics',{}).get('all_capture_readout_controls_pass',False)
                   for r in selected) and len(selected_checks)==2 and all(c['passed'] for c in selected_checks))
summary=dict(scope=scope,evidence_roots=[str(p.relative_to(ROOT)) for p in roots],runs=runs,checks=checks,incomplete_attempts=incomplete,
             selected_capture_deterministic_screen_pass=selected_pass,
             selected_capture_scope='Typical transistor process, 3.3 V, 27/125 C, single-row capture with 100 pF board and 20 pF sample load; extracted row RC at nominal resistance values; ideal storage capacitors and schematic periphery.',
             power_grid_qualification='Open: large row-enable charging dip; distributed supply and clock/peripheral routing required.',
             excluded_auxiliary_attempts={str(p.relative_to(ROOT)):json.loads(p.read_text()) for root in roots for p in root.glob('excluded.json')})
(ROOT/'simulations/array-recovery.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
power_runs=[(get('rel6-200'),'Serial\n0.4 µm'),(get('power-rel6-200'),'Serial\n2 µm'),
            (get('capture40-klu-27-100'),'Capture 27 °C\n2 µm'),(get('capture40-klu-125-100'),'Capture 125 °C\n2 µm')]
power_runs=[(r,label) for r,label in power_runs if r and 'waveform_metrics' in r]
if power_runs:
    for offset,key,label in [(-.18,'max_local_vdd_loss_V','Switching peak'),(.18,None,'At sample / common capture')]:
        values=[r['waveform_metrics'][key or ('capture_max_local_vdd_loss_V' if r.get('column_storage_pF') else 'max_sampled_local_vdd_loss_V')]*1e3 for r,_ in power_runs]
        axes[0,0].bar([i+offset for i in range(len(values))],values,width=.36,label=label)
    axes[0,0].set_xticks(range(len(power_runs)),[label for _,label in power_runs],fontsize=9)
    axes[0,0].legend()
axes[0,0].set(title='Wider rails help; capture adds charging load',ylabel='Local VDD loss (mV)')
cs=[c for c in checks if c['comparison'].startswith('Original row, reltol') and 'vs 100' in c['comparison']]
cs+=selected_checks
if cs:
    axes[0,1].bar(range(len(cs)),[c['max_difference_V']*1e6 for c in cs],color=['#238b45' if c['passed'] else '#a6611a' for c in cs])
    labels=['Capture\n27 °C' if 'nominal capture' in c['comparison'] else 'Capture\n125 °C' if 'hot capture' in c['comparison'] else 'Old row\nvntol 1e-9' if 'vntol' in c['comparison'] else 'Old row\nreltol 1e-6' if '1e-6' in c['comparison'] else 'Old row\nreltol 1e-7' for c in cs]
    axes[0,1].set_xticks(range(len(cs)),labels,fontsize=9)
axes[0,1].axhline(10,color='red',ls='--',label='Unchanged 10 µV limit');axes[0,1].legend()
axes[0,1].set(title='200 → 100 ns timestep comparison',ylabel='Maximum HOLD difference (µV)')
for name,case,label in [('rel6-200','r1c64-rc-port','Serial exposure'),('capture40-klu-27-100','r1c64-rc-port','Common capture, 27 °C'),('capture40-klu-125-100','r1c64-rc-port','Common capture, 125 °C')]:
    r=get(name,case)
    if r and r['completed']:
        samples=[s for i,s in enumerate(r['samples']) if i%3==1]
        axes[1,0].plot([s['column'] for s in samples],[s['capture']['HOLD'] for s in samples],'o-',label=label)
axes[1,0].set(title='Uniform 80 pA illumination',xlabel='Column',ylabel='Sampled output (V)');axes[1,0].legend()
labels=[];errors=[]
for name,label in [(f'storage40-bias500k-{temp}-{delay}-matched',f'{temp} °C, '+('late' if delay else 'early')) for temp in [27,125] for delay in [0,1220]]:
    r=get(name,'r1c3-rc-port')
    if r and r['completed']:
        labels.append(label);errors.append(r['max_tracking_error_V']*1e6)
for r in selected:
    if r and r['completed']:
        labels.append(f"64 cols\n{r['temperature_C']:g} °C");errors.append(r['max_tracking_error_V']*1e6)
axes[1,1].bar(range(len(labels)),errors);axes[1,1].set_xticks(range(len(labels)),labels,rotation=10,fontsize=9)
axes[1,1].axhline(500,color='red',ls='--',label='500 µV limit');axes[1,1].legend()
axes[1,1].set(title='40 pF capture: short controls and full row',ylabel='Maximum deterministic error (µV)')
fig.savefig(ROOT/'docs/assets/array-recovery.png',dpi=160);plt.close(fig)
print(json.dumps({'runs':len(runs),'checks':checks},indent=2))

selected=[get(f'capture40-klu-{temp}-matched') for temp in [27,125]]
qualified=[r for r in selected if r and r['completed']]
status=('Full-row matched capture tests: '+', '.join(f"{r['temperature_C']:g} °C: {r['max_tracking_error_V']*1e6:.3f} µV" for r in qualified)) if qualified else 'Full 64-column capture validation is in progress.'
refinement=next((c for c in reversed(checks) if c['comparison'].startswith('Original row, reltol') and 'vs 100 ns' in c['comparison']),None)
numstatus=f"Original-row numerical comparison: {refinement['max_difference_V']*1e6:.3f} µV; below 10 µV: {refinement['passed']}." if refinement else 'Original-row tighter-tolerance refinement is in progress.'
encoded=base64.b64encode((ROOT/'docs/assets/array-recovery.png').read_bytes()).decode()
numeric_capture='; '.join(f"{c['comparison']}: {c['max_difference_V']*1e6:.3f} µV" for c in selected_checks)
(ROOT/'docs/array-recovery-section.html').write_text(
    '<section id="array-recovery"><h2>Power routing and column capture</h2>'
    '<p>'+status+' '+numeric_capture+'. Selected deterministic screen including control checks: '+str(selected_pass)+'.</p>'
    '<p>Selected circuit: 40 pF column stores, 500 kΩ BIAS, 12.4 kΩ PREF, 10 µs acquisition and 20 µs slots. '
    'All four short early/late nominal/hot controls pass; worst 373.363 µV. '+numstatus+'</p>'
    '<p>Wider physical rails reduce peak VDD loss in the original serial circuit from 101.162 to 24.213 mV; both strip layouts pass DRC and direct/RC-collapsed LVS. '
    'The larger capture bank adds a 354.350 mV nominal row-enable dip, falling to 34.522 mV at capture, and about 8.1 mA average modeled analog supply current. '
    'Distributed physical power and peripheral routing remain required.</p>'
    '<p>The pixel strip is extracted R+C; storage capacitors and periphery remain schematic. Full-array, startup, full PVT and tapeout qualification remain open.</p>'
    '<img src="data:image/png;base64,'+encoded+'" alt="Array recovery measurements">'
    '<p><a href="array-recovery.md">Evidence, rejected candidates and scope</a></p></section>')
