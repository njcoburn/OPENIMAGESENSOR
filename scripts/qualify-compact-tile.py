"""Run and independently audit the small joined-tile electrical matrix.

Two temperatures, three imposed photocurrents, two timesteps, physical and
schematic models; selected single-net and simultaneous shunt placements.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('trace',ROOT/'scripts/diagnose-capture-transient.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();layout=a.layout.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    for name in ['qualify-compact-tile.py','simulate-compact-tile.py','diagnose-capture-transient.py']:
        (out/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    meta=json.loads((layout/'verification.json').read_text())
    def run(job):
        temp,light,step,model,transient_only=job
        name=f'{temp}-{light}-{step}-{model}';d=out/name
        cmd=[sys.executable,str(ROOT/'scripts/simulate-compact-tile.py'),'--layout',str(layout),'--out',str(d),
             '--temperature',str(temp),'--light-pa',str(light),'--step-ns',str(step),'--model',model,'--timeout','120']
        if transient_only:cmd.append('--transient-only')
        with (out/(name+'.log')).open('w') as f:
            process=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=520)
        result=json.loads((d/'result.json').read_text()) if (d/'result.json').exists() else dict(completed=False)
        print(name, 'complete' if result['completed'] else 'FAILED',flush=True)
        assert process.returncode==0 and result['completed'],d
        ix,data=trace.trace(d/'transient/stream.raw')
        assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
        assert abs(data[-1,0]-.0027)<1e-12 and np.max(np.diff(data[:,0]))<=step*1e-9*1.001
        deck=(d/'transient/test.spice').read_text()
        assert hashlib.sha256(deck.encode()).hexdigest()==result['transient']['deck_sha256']
        assert '\nunset klu\n' in deck and 'uic' not in deck.lower()
        assert '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2' in deck
        assert hashlib.sha256((d/'tile.spice').read_bytes()).hexdigest()==result['model_sha256']
        def at(n,t):return 0. if n=='0' else float(np.interp(t,data[:,0],data[:,ix['v('+n.lower()+')']]))
        for sample in result['samples']:
            for n,value in sample['values'].items():assert at(n,sample['time_s'])==value,(d,n)
        for n,value in result['capture_state'].items():assert at(n,.0014-1e-9)==value,(d,n)
        if not transient_only:
            for key in ['first','last']:
                reference=next(s for s in result['samples'] if s['slot']==key)['output_reference']
                assert abs(reference['values']['ADCIN']-reference['values']['HOLD'])<1e-8
            for ref in d.glob('*reference/test.spice'):
                assert 'PWL(' not in ref.read_text()
        return job,result
    main_jobs=[(t,l,s,m,False) for t in [27,125] for l in [0,80,240] for s in [200,100] for m in ['rc-port','reference']]
    with ThreadPoolExecutor(max_workers=3) as pool:main_results=dict(pool.map(run,main_jobs))
    variants=['rc-far']+['rc-'+v['net'].lower()+'-far' for v in meta['shunt_approximations']]
    placement_jobs=[(t,l,100,m,True) for t in [27,125] for l in [0,80,240] for m in variants]
    with ThreadPoolExecutor(max_workers=3) as pool:placement_results=dict(pool.map(run,placement_jobs))
    def delta(a,b,node):
        assert [(s['slot'],s['time_s']) for s in a['samples']]==[(s['slot'],s['time_s']) for s in b['samples']]
        return max(abs(x['values'][node]-y['values'][node]) for x,y in zip(a['samples'],b['samples']))
    rows=[]
    for t in [27,125]:
        for light in [0,80,240]:
            coarse,fine=[main_results[t,light,s,'rc-port',False] for s in [200,100]]
            schematic=main_results[t,light,100,'reference',False]
            variants_for_condition=[r for (tt,ll,ss,m,only),r in placement_results.items() if (tt,ll)==(t,light)]
            rows.append(dict(temperature_C=t,light_pA=light,
                max_total_capture_readout_error_uV=max(r['max_total_capture_readout_error_V'] for r in [coarse,fine])*1e6,
                max_output_tracking_error_uV=max(r['max_output_tracking_error_V'] for r in [coarse,fine])*1e6,
                max_schematic_capture_error_uV=max(main_results[t,light,s,'reference',False]['max_total_capture_readout_error_V'] for s in [200,100])*1e6,
                physical_timestep_difference_uV=delta(coarse,fine,'HOLD')*1e6,
                schematic_timestep_difference_uV=delta(main_results[t,light,200,'reference',False],schematic,'HOLD')*1e6,
                physical_minus_schematic_magnitude_uV=delta(fine,schematic,'HOLD')*1e6,
                max_output_placement_difference_uV=max(delta(fine,r,'HOLD') for r in variants_for_condition)*1e6,
                max_storage_placement_difference_uV=max(delta(fine,r,'STORE0') for r in variants_for_condition)*1e6,
                storage_reset_window_change_uV=fine['storage_reset_coupling_V']*1e6,
                first_output_V=fine['samples'][0]['values']['HOLD'],
                late_minus_first_output_uV=(fine['samples'][1]['values']['HOLD']-fine['samples'][0]['values']['HOLD'])*1e6,
                captured_column_V=fine['capture_state']['COL0']))
    checks=dict(capture_readout_pass=all(r['max_total_capture_readout_error_uV']<500 for r in rows),
                output_tracking_pass=all(r['max_output_tracking_error_uV']<500 for r in rows),
                schematic_capture_pass=all(r['max_schematic_capture_error_uV']<500 for r in rows),
                timestep_pass=all(max(r['physical_timestep_difference_uV'],r['schematic_timestep_difference_uV'])<10 for r in rows),
                placement_pass=all(max(r['max_output_placement_difference_uV'],r['max_storage_placement_difference_uV'])<10 for r in rows),
                brightness_order_pass=all(all(x>y for x,y in zip(values,values[1:])) for values in
                    [[r['first_output_V'] for r in rows if r['temperature_C']==t] for t in [27,125]]))
    report=dict(scope=__doc__,rows=rows,checks=checks,all_checks_pass=all(checks.values()),
                main_transients=len(main_results),placement_transients=len(placement_results),dc_references=3*len(main_results),
                placements_tested=['rc-port',*variants],
                layout=str(layout.relative_to(ROOT)),layout_gds_sha256=meta['gds_sha256'],
                waveform_audit='All traces complete, finite, monotonic, max-step checked; samples and capture state independently recomputed.',
                limits='Typical process and nominal wire RC; imposed photocurrents; schematic references/drivers/ADC; single capture and two output reads; no real decoder, full-column loading, repeated captures, optical or manufacturing qualification.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
