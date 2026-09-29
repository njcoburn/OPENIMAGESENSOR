"""Audit the revised 16-column thermal, pattern and selected sensitivity screens."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={'alternating':[0,240]*8,'inverse':[240,0]*8,'dark':[0]*16,'middle':[80]*16,'bright':[240]*16}


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True)
    p.add_argument('--run',type=Path,action='append',required=True)
    p.add_argument('--batch',type=Path,required=True)
    a=p.parse_args();layout=a.layout.resolve();meta=json.loads((layout/'verification.json').read_text())
    assert meta['columns']==16 and meta['ground_bus_width_um']==8
    assert len(meta['shunt_approximations'])==19
    assert meta['direct_and_resistor_collapsed_lvs'] and meta['magic_drc_errors']==meta['klayout_main_drc_errors']==0
    assert sha(layout/'bank.gds')==meta['gds_sha256']
    reader=module('reader','diagnose-capture-transient.py');bank=module('bank','simulate-compact-bank.py')
    reference=module('reference','report-compact-bank-16.py')
    batch=json.loads((a.batch/'batch.json').read_text())
    assert batch['expected']==len(batch['runs'])==8 and all(r['completed'] for r in batch['runs'])
    directories=a.run+[ROOT/r['run'] for r in batch['runs']]
    records={};rows=[];evidence={layout/'verification.json',layout/'bank.gds',Path(__file__).resolve()}
    evidence.update(ROOT/'scripts'/name for name in ['simulate-compact-bank.py','diagnose-capture-transient.py',
                    'report-compact-bank-16.py','test-compact-bank-sampling.py','plot-bank-16-screen.py','run-tools.sh'])
    evidence.update(f for f in a.batch.rglob('*') if f.is_file())
    for directory in directories:
        r=json.loads((directory/'result.json').read_text())
        assert r['completed'] and r['phase']=='full' and r['columns']==16
        assert r['solver']=='klu' and r['method']=='trap' and r['driver_form']=='current'
        assert r['layout_gds_sha256']==meta['gds_sha256']
        assert r['model'] in ['rc-port','rc-far']
        assert r['references_requested']==(r['model']=='rc-port'), 'Accuracy cases require all independent references'
        assert sha(directory/'tile.spice')==r['model_sha256']==meta['hashes'][r['model']+'.spice']
        assert sha(layout/(r['model']+'.spice'))==r['model_sha256']
        evidence.add(layout/(r['model']+'.spice'))
        assert r['transient']==json.loads((directory/'transient/execution.json').read_text())
        assert r['transient']['completed'] and r['transient']['returncode']==0 and not r['transient']['timed_out'] and not r['transient']['errors']
        assert sha(directory/'transient/test.spice')==r['transient']['deck_sha256']
        deck=(directory/'transient/test.spice').read_text()
        assert '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2' in deck
        assert '\nset klu\n' in deck and 'uic' not in deck.lower()
        ix,data=reader.trace(directory/'transient/stream.raw')
        assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
        assert abs(data[0,0])<1e-15 and abs(data[-1,0]-.003)<1e-12 and len(data)==r['transient']['points']
        assert np.max(np.diff(data[:,0]))<=r['step_ns']*1e-9*1.001
        at=bank.trace_sampler(ix,data)
        for name,value in r['capture_state'].items():assert at(name,.0014-1e-9)==value
        assert [(s['slot'],s['column']) for s in r['samples']]==[(slot,c) for slot in ['first','last'] for c in range(16)]
        slots,stop=bank.readout_schedule(16);assert stop==r['stop_s']
        for sample,(slot,column,start) in zip(r['samples'],slots):
            assert sample['time_s']==start+11.999e-6
            for name,value in sample['values'].items():assert at(name,sample['time_s'])==value
            v=sample['values']
            assert v['SC']<.01 and v['SCB']>3 and v['ROW0']<.01 and v['RST0']>3
            assert v[f'SEL{column}']>3 and v[f'SELB{column}']<.01
            assert all(v[f'SEL{c}']<.01 and v[f'SELB{c}']>3 for c in range(16) if c!=column)
        def check_reference(d,ref):
            ex=ref['execution'];assert ex['completed'] and not ex['errors'] and not ex['timed_out'] and ex['returncode']==0
            assert ex==json.loads((d/'execution.json').read_text())
            assert sha(d/'test.spice')==ex['deck_sha256']
            values=reference.dc_values(d/'op.raw')
            for n,v in ref['values'].items():assert values[f'v({n.lower()})']==v
            assert abs(ref['values']['ADCIN']-ref['values']['HOLD'])<1e-8
        if r['references_requested']:
            assert r['reference_progress']==dict(completed=48,expected=48)
            for c,ref in enumerate(r['capture_references']):check_reference(directory/f'capture{c}-reference',ref)
            for s in r['samples']:
                check_reference(directory/f'{s["slot"]}{s["column"]}-output-reference',s['output_reference'])
                assert s['total_capture_readout_error_V']==s['values']['HOLD']-r['capture_references'][s['column']]['values']['HOLD']
                assert s['output_tracking_error_V']==s['values']['HOLD']-s['output_reference']['values']['HOLD']
            for kind in ['total_capture_readout','output_tracking']:
                assert r['max_'+kind+'_error_V']==max(abs(s[kind+'_error_V']) for s in r['samples'])
            assert r['capture_readout_pass']==(r['max_total_capture_readout_error_V']<500e-6)
            assert r['tracking_pass']==(r['max_output_tracking_error_V']<500e-6)
        name,=[name for name,lights in PATTERNS.items() if lights==r['lights_pA']]
        key=(r['temperature_C'],name,r['step_ns'],r['model']);assert key not in records
        records[key]=r
        worst_sample=max(r['samples'],key=lambda s:abs(s['total_capture_readout_error_V'])) if r['references_requested'] else None
        rows.append(dict(run=str(directory.resolve().relative_to(ROOT)),temperature_C=key[0],pattern=name,step_ns=key[2],model=key[3],
            references=48 if r['references_requested'] else 0,
            transient_seconds=r['transient']['seconds'],
            worst_capture_readout_sample=dict(column=worst_sample['column'],scan=worst_sample['slot']) if worst_sample else None,
            port_voltage_ranges_V={n:[float(np.min(data[:,ix[f'v({n.lower()})']])),float(np.max(data[:,ix[f'v({n.lower()})']]))] for n in ['VDD','BIAS','PREF']},
            max_capture_readout_error_uV=r.get('max_total_capture_readout_error_V',0)*1e6 if r['references_requested'] else None,
            max_output_tracking_error_uV=r.get('max_output_tracking_error_V',0)*1e6 if r['references_requested'] else None))
        evidence.update(f for f in directory.rglob('*') if f.is_file())
        del at,data
    expected={(t,p,100,'rc-port') for t in [27,125] for p in PATTERNS}
    expected|={(t,'alternating',50,'rc-port') for t in [27,125]}
    expected|={(t,'alternating',100,'rc-far') for t in [27,125]}
    assert set(records)==expected, 'Missing or unexpected matrix cases'
    assert sum(r['references'] for r in rows)==576
    rows.sort(key=lambda r:(r['temperature_C'],list(PATTERNS).index(r['pattern']),r['model'],-r['step_ns']))
    def delta(old,new,nodes=None):
        changes=[]
        for x,y in zip(old['samples'],new['samples']):
            assert (x['slot'],x['column'],x['time_s'])==(y['slot'],y['column'],y['time_s'])
            names=nodes if nodes is not None else x['values'].keys()&y['values'].keys()
            changes.extend((abs(x['values'][n]-y['values'][n])*1e6,n,x['slot'],x['column']) for n in names)
        value,node,scan,column=max(changes)
        return dict(max_uV=value,node=node,scan=scan,column=column)
    sensitivity=[]
    for t in [27,125]:
        base=records[t,'alternating',100,'rc-port'];fine=records[t,'alternating',50,'rc-port'];far=records[t,'alternating',100,'rc-far']
        sensitivity.append(dict(temperature_C=t,timestep=delta(base,fine),timestep_hold=delta(base,fine,['HOLD']),
            joint_far_hold=delta(base,far,['HOLD']),joint_far_store=delta(base,far,[f'STORE{c}' for c in range(16)])))
    contrast=all(s['values']['HOLD']>r['samples'][(s['column']^1)+(16 if s['slot']=='last' else 0)]['values']['HOLD']
                 for (t,p,step,model),r in records.items() if p in ['alternating','inverse'] and step==100 and model=='rc-port'
                 for s in r['samples'] if r['lights_pA'][s['column']]==0)
    brightness=all(all(x>y for x,y in zip(values,values[1:])) for values in
        [[records[t,p,100,'rc-port']['samples'][i]['values']['HOLD'] for p in ['dark','middle','bright']] for t in [27,125] for i in range(32)])
    neighbor=[]
    for t in [27,125]:
        for pattern in ['alternating','inverse']:
            mixed=records[t,pattern,100,'rc-port']
            for i,sample in enumerate(mixed['samples']):
                uniform=records[t,'dark' if mixed['lights_pA'][sample['column']]==0 else 'bright',100,'rc-port']
                neighbor.append(dict(temperature_C=t,pattern=pattern,column=sample['column'],scan=sample['slot'],
                    mixed_minus_uniform_output_uV=(sample['values']['HOLD']-uniform['samples'][i]['values']['HOLD'])*1e6))
    checks=dict(capture_readout=all(r['max_total_capture_readout_error_V']<500e-6 for r in records.values() if r['references_requested']),
                output_tracking=all(r['max_output_tracking_error_V']<500e-6 for r in records.values() if r['references_requested']),
                alternating_timestep=all(s['timestep']['max_uV']<10 for s in sensitivity),
                alternating_joint_far_placement=all(max(s['joint_far_hold']['max_uV'],s['joint_far_store']['max_uV'])<10 for s in sensitivity),
                contrast_order=contrast,brightness_order=brightness)
    report=dict(scope=__doc__,rows=rows,sensitivity=sensitivity,neighbor_pattern_response=neighbor,checks=checks,selected_screen_pass=all(checks.values()),
        layout=str(layout.relative_to(ROOT)),layout_gds_sha256=meta['gds_sha256'],references=sum(r['references'] for r in rows),
        full_16_column_qualification=False,full_64_column_qualification=False,
        runtime_scope='Transient wall times include the concurrent simulation workload; no single-job speed comparison is implied.',
        limits=['Typical process and nominal wire RC only; 27/125 C, five imposed photocurrent patterns',
                '100→50 ns refinement and joint far-shunt placement only for alternating 0/240 pA',
                'Individual shunt placements, other-pattern refinement and physical/schematic comparisons remain open',
                'One capture and two reads; external bias resistors, finite behavioral drivers and external ADC',
                'No repeated rows, real decoding/drivers, revised 64-column bank, full chip or manufacturing qualification'],
        evidence_hashes={str(f.relative_to(ROOT)):sha(f) for f in sorted({f.resolve() for f in evidence})})
    (ROOT/'simulations/compact-bank-16-screen.json').write_text(json.dumps(report,indent=2)+'\n')
    table=''.join(f'<tr><td>{r["temperature_C"]:g}</td><td>{r["pattern"]}</td><td>{r["step_ns"]:g}</td><td>{r["max_capture_readout_error_uV"]:.3f}</td><td>{r["max_output_tracking_error_uV"]:.3f}</td></tr>' for r in rows if r['references'])
    st=''.join(f'<tr><td>{s["temperature_C"]}</td><td>{s["timestep"]["max_uV"]:.3f}</td><td>{s["joint_far_hold"]["max_uV"]:.3f}</td><td>{s["joint_far_store"]["max_uV"]:.3f}</td></tr>' for s in sensitivity)
    outcome='passes' if report['selected_screen_pass'] else 'fails'
    worst=max(r['max_capture_readout_error_uV'] for r in rows if r['references'])
    neighbor_worst=max(abs(n['mixed_minus_uniform_output_uV']) for n in neighbor)
    ordering='pass' if contrast and brightness else 'fail'
    html=f'''<section id="compact-bank-16-screen"><h2>16-column follow-up: temperature, patterns and selected sensitivities</h2>
<p><strong>The revised 8 µm ground-bus bank {outcome} this selected development screen.</strong> Fourteen complete transients include the retained nominal control, twelve sets of 48 independent references ({report['references']} references total), and two joint far-placement controls. Worst total capture/readout error is <strong>{worst:.3f} µV</strong> against 500 µV. The physical layout is unchanged from the verified ground-bus revision.</p>
<figure><img src="assets/compact-bank-16-screen.png" alt="Worst capture/readout and output tracking errors for five patterns at 27 and 125 degrees Celsius" style="max-width:100%"><figcaption>Bars show the 100 ns cases. The detailed table also includes the additional alternating-pattern 50 ns controls.</figcaption></figure>
<details><summary>Accuracy by temperature, pattern and timestep</summary><table><thead><tr><th>Temperature, °C</th><th>Pattern</th><th>Step, ns</th><th>Total error, µV</th><th>Output tracking, µV</th></tr></thead><tbody>{table}</tbody></table></details>
<p>Alternating and inverse patterns repeat 0/240 and 240/0 pA across all 16 columns. Uniform dark, middle and bright patterns use 0, 80 and 240 pA. Contrast and brightness ordering checks {ordering}. Each trace captures once and reads every column twice over 3 ms.</p>
<p>Changing the other pixels from uniform to mixed illumination while holding the selected pixel's imposed photocurrent fixed changes its sampled output by up to {neighbor_worst:.3f} µV. This includes shared bias and integrated pixel-response changes; it is reported separately from same-state capture/readout accuracy and has no assigned pass threshold. Port VDD/BIAS/PREF ranges are retained in the JSON report; these do not substitute for all local supply/reference-drop checks.</p>
<table><thead><tr><th>Temperature, °C</th><th>100→50 ns: worst saved terminal, µV</th><th>Joint far: HOLD change, µV</th><th>Joint far: STORE change, µV</th></tr></thead><tbody>{st}</tbody></table>
<p>The sensitivity table covers the alternating pattern only, with a 10 µV comparison limit. Joint far placement moves all 19 audited shunt totals together; it does not replace individual-net placement checks. Sampling acceleration reproduces every archived capture/readout value exactly and leaves the decks and circuit unchanged. Saved transient samples and DC references are independently re-read and their errors recomputed.</p>
<p><strong>Remaining scope:</strong> individual shunt placements, refinement of the other patterns, physical/schematic response comparisons, process/wire/supply corners and the remaining supply/reference-drop checks. Real decoding/drivers, repeated rows, the revised 64-column bank and assembled 64×64 manufacturing qualification remain ahead. This is not a full-bank or tapeout pass.</p>
<p><a href="../simulations/compact-bank-16-screen.json">Results, limits and evidence hashes</a> · <a href="compact-bank-16-screen.md">Reproduction and next steps</a> · <a href="#compact-bank-16">Original failure and physical ground-bus correction</a></p></section>'''
    (ROOT/'docs/compact-bank-16-screen-section.html').write_text(html+'\n')
    print(json.dumps(dict(checks=checks,worst_total_error_uV=worst,references=report['references']),indent=2))
    if not report['selected_screen_pass']:raise SystemExit(1)


if __name__=='__main__':main()
