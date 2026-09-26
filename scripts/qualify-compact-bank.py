"""Audit two-column shared capture, contrast patterns and numerical sensitivity.

This is a bounded development screen, not a repeated-frame/full-bank result.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('trace',ROOT/'scripts/diagnose-capture-transient.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)
PATTERNS=[(0,0),(0,240),(240,0),(80,80),(240,240)]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();layout=a.layout.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    for name in ['qualify-compact-bank.py','simulate-compact-bank.py','diagnose-capture-transient.py']:
        (out/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    meta=json.loads((layout/'verification.json').read_text());assert meta['columns']==2
    assert sha(layout/'bank.gds')==meta['gds_sha256']
    def run(job):
        temp,lights,step,model,only=job
        name=f'{temp}-'+','.join(map(str,lights))+f'-{step}-{model}';d=out/name
        cmd=[sys.executable,str(ROOT/'scripts/simulate-compact-bank.py'),'--layout',str(layout),'--out',str(d),
             '--temperature',str(temp),'--lights-pa',','.join(map(str,lights)),
             '--step-ns',str(step),'--model',model,'--timeout','120']
        if only:cmd.append('--transient-only')
        with (out/(name+'.log')).open('w') as f:
            process=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=900)
        r=json.loads((d/'result.json').read_text()) if (d/'result.json').exists() else dict(completed=False)
        print(name,'complete' if r['completed'] else 'FAILED',flush=True)
        assert process.returncode==0 and r['completed'],d
        ix,data=trace.trace(d/'transient/stream.raw')
        assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
        assert abs(data[-1,0]-.00272)<1e-12 and np.max(np.diff(data[:,0]))<=step*1e-9*1.001
        assert sha(d/'tile.spice')==r['model_sha256']
        deck=(d/'transient/test.spice').read_text()
        assert sha(d/'transient/test.spice')==r['transient']['deck_sha256']
        assert '\nunset klu\n' in deck and 'uic' not in deck.lower()
        assert '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2' in deck
        assert 'Xref ' not in deck and 'Xstorage_ref ' not in deck
        def at(n,t):return 0. if n=='0' else float(np.interp(t,data[:,0],data[:,ix['v('+n.lower()+')']]))
        for n,v in r['capture_state'].items():assert at(n,.0014-1e-9)==v
        assert [(s['slot'],s['column']) for s in r['samples']]==[('first',0),('first',1),('last',0),('last',1)]
        for sample in r['samples']:
            for n,v in sample['values'].items():assert at(n,sample['time_s'])==v
        for c,v in enumerate(r['storage_reset_window_change_V']):
            assert at(f'STORE{c}',.001405)-at(f'STORE{c}',.0014025)==v
        if not only:
            references=[(f'capture{c}-reference',ref) for c,ref in enumerate(r['capture_references'])]
            references += [(f'{s["slot"]}{s["column"]}-output-reference',s['output_reference']) for s in r['samples']]
            for name,ref in references:
                directory=d/name;di,dd=trace.trace(directory/'op.raw')
                assert len(dd)==1 and np.isfinite(dd).all()
                assert sha(directory/'test.spice')==ref['execution']['deck_sha256']
                assert 'PWL(' not in (directory/'test.spice').read_text()
                for n,v in ref['values'].items():assert float(dd[0,di['v('+n.lower()+')']])==v
                assert abs(ref['values']['ADCIN']-ref['values']['HOLD'])<1e-8
            for sample in r['samples']:
                c=sample['column'];v=sample['values'];output=sample['output_reference']['values'];capture=r['capture_references'][c]['values']
                assert v['HOLD']-output['HOLD']==sample['output_tracking_error_V']
                assert v['HOLD']-capture['HOLD']==sample['total_capture_readout_error_V']
                assert v[f'STORE{c}']-capture[f'STORE{c}']==sample['storage_capture_error_V']
        return job,r
    jobs=[(t,l,s,m,False) for t in [27,125] for l in PATTERNS for s in [200,100] for m in ['rc-port','reference']]
    with ThreadPoolExecutor(max_workers=3) as pool:main_results=dict(pool.map(run,jobs))
    variants=['rc-far']+['rc-'+v['net'].lower()+'-far' for v in meta['shunt_approximations']]
    jobs=[(t,l,100,m,True) for t in [27,125] for l in PATTERNS for m in variants]
    with ThreadPoolExecutor(max_workers=3) as pool:placement_results=dict(pool.map(run,jobs))
    def delta(a,b,nodes):
        assert [(s['slot'],s['column'],s['time_s']) for s in a['samples']]==[(s['slot'],s['column'],s['time_s']) for s in b['samples']]
        return max(abs(x['values'][n]-y['values'][n]) for x,y in zip(a['samples'],b['samples']) for n in nodes)
    rows=[]
    for t in [27,125]:
        for lights in PATTERNS:
            coarse,fine=[main_results[t,lights,s,'rc-port',False] for s in [200,100]]
            sc,schematic=[main_results[t,lights,s,'reference',False] for s in [200,100]]
            placed=[r for (tt,ll,ss,m,only),r in placement_results.items() if (tt,ll)==(t,lights)]
            rows.append(dict(temperature_C=t,lights_pA=lights,
                max_total_capture_readout_error_uV=max(r['max_total_capture_readout_error_V'] for r in [coarse,fine])*1e6,
                max_output_tracking_error_uV=max(r['max_output_tracking_error_V'] for r in [coarse,fine])*1e6,
                max_schematic_capture_error_uV=max(r['max_total_capture_readout_error_V'] for r in [sc,schematic])*1e6,
                physical_timestep_difference_uV=delta(coarse,fine,['HOLD'])*1e6,
                schematic_timestep_difference_uV=delta(sc,schematic,['HOLD'])*1e6,
                physical_minus_schematic_magnitude_uV=delta(fine,schematic,['HOLD'])*1e6,
                max_output_placement_difference_uV=max(delta(fine,r,['HOLD']) for r in placed)*1e6,
                max_storage_placement_difference_uV=max(delta(fine,r,['STORE0','STORE1']) for r in placed)*1e6,
                max_storage_reset_window_change_uV=max(map(abs,fine['storage_reset_window_change_V']))*1e6,
                first_outputs_V=[s['values']['HOLD'] for s in fine['samples'] if s['slot']=='first'],
                late_minus_first_output_uV=[(fine['samples'][c+2]['values']['HOLD']-fine['samples'][c]['values']['HOLD'])*1e6 for c in range(2)]))
    checks=dict(capture_readout_pass=all(r['max_total_capture_readout_error_uV']<500 for r in rows),
                output_tracking_pass=all(r['max_output_tracking_error_uV']<500 for r in rows),
                schematic_capture_pass=all(r['max_schematic_capture_error_uV']<500 for r in rows),
                timestep_pass=all(max(r['physical_timestep_difference_uV'],r['schematic_timestep_difference_uV'])<10 for r in rows),
                placement_pass=all(max(r['max_output_placement_difference_uV'],r['max_storage_placement_difference_uV'])<10 for r in rows))
    checks['contrast_order_pass']=all((r['first_outputs_V'][0]>r['first_outputs_V'][1])==(r['lights_pA'][0]<r['lights_pA'][1]) for r in rows if r['lights_pA'][0]!=r['lights_pA'][1])
    checks['brightness_order_pass']=all(all(x>y for x,y in zip(v,v[1:])) for v in
        [[next(r for r in rows if r['temperature_C']==t and r['lights_pA']==(l,l))['first_outputs_V'][c] for l in [0,80,240]] for t in [27,125] for c in range(2)])
    # Neighbor changes include shared analog bias and integrated pixel response;
    # retain them separately from same-state capture/readout accuracy.
    neighbor=[]
    for t in [27,125]:
        for c in range(2):
            for light in [0,240]:
                patterns=[tuple(light if i==c else other for i in range(2)) for other in [0,240]]
                before,after=[main_results[t,l,100,'rc-port',False] for l in patterns]
                changes=[(y['values']['HOLD']-x['values']['HOLD'])*1e6 for x,y in zip(before['samples'],after['samples']) if x['column']==c]
                neighbor.append(dict(temperature_C=t,column=c,light_pA=light,neighbor_0_to_240_pA_output_changes_uV=changes))
    report=dict(scope=__doc__,rows=rows,neighbor_pattern_response=neighbor,checks=checks,all_checks_pass=all(checks.values()),
                main_transients=len(main_results),placement_transients=len(placement_results),dc_references=6*len(main_results),
                placements_tested=['rc-port',*variants],layout=str(layout.relative_to(ROOT)),layout_gds_sha256=meta['gds_sha256'],
                waveform_audit='Every transient and DC trace finite and complete; transient monotonic/max-step checks; capture, sampled values and reference errors independently recomputed.',
                limits='Typical process/nominal wire RC; two columns; five imposed photocurrent patterns; one capture/two reads per column; external bias resistors, behavioral drivers and ADC; no real decoder, repeated frames, full loading or manufacturing qualification.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not report['all_checks_pass']:raise SystemExit(1)


if __name__=='__main__':main()
