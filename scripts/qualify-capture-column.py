"""Independent single-model capture-column matrix using SPARSE.

Separates transient/reference accuracy, schematic-to-layout shift, timestep
refinement and COL-capacitance-placement sensitivity. No full row is included.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import re
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('diagnostic',ROOT/'scripts/diagnose-capture-transient.py')
diag=importlib.util.module_from_spec(spec);spec.loader.exec_module(diag)


def reference(directory,name,level,duration):
    d=directory/f'reference-{duration}us';d.mkdir()
    source=(directory/'test.spice').read_text()
    source=source.split('.save ',1)[0]
    replacements={'Vcol':f'Vcol COL 0 {level:g}','Vsc':'Vsc CTLSC 0 1',
        'Vsel':'Vsel CTLSEL 0 1','Vacq':'Vacq ACQ 0 3.3','Vreset':'Vreset RSTADC 0 0'}
    for key,value in replacements.items():
        source,count=re.subn(r'(?m)^'+key+r' .*$',value,source);assert count==1
    source+='\n.save '+ ' '.join(f'v({node}_{name})' for node in ['hold','store','buf','cbuf'])+f'\n.control\nunset klu\nset num_threads=1\nset filetype=binary\noptran 1 1 1 100n {duration}u 0\nop\nwrite op.raw\nquit\n.endc\n.end\n'
    (d/'test.spice').write_text(source)
    result=subprocess.run(['ngspice','-b','test.spice'],cwd=d,capture_output=True,text=True,timeout=60)
    (d/'ngspice.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0 and 'simulation(s) aborted' not in result.stdout+result.stderr
    ix,data=diag.trace(d/'op.raw');assert data is not None and len(data)==1 and np.isfinite(data).all()
    values={node:float(data[0,ix[f'v({node}_{name})']]) for node in ['hold','store','buf','cbuf']}
    (d/'result.json').write_text(json.dumps(values,indent=2)+'\n')
    return values


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--extraction',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--temperatures',type=int,nargs='+',default=[27,125]);p.add_argument('--levels',type=float,nargs='+',default=[1.2,1.6,2.0])
    p.add_argument('--steps',type=int,nargs='+',default=[100,50]);p.add_argument('--timeout',type=float,default=60)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    for script in [Path(__file__),ROOT/'scripts/diagnose-capture-transient.py']:(out/script.name).write_bytes(script.read_bytes())
    for name,file,sub in [('rc','rc-port.spice','flat'),('rcfar','rc-far.spice','flat'),('physical','reference.spice','reference')]:
        text=(a.extraction/file).read_text().replace('.subckt '+sub+' ','.subckt '+name+' ').replace('.ends '+sub,'.ends '+name)
        (out/(name+'.spice')).write_text(text)
    text=(out/'physical.spice').read_text().replace('.subckt physical ','.subckt ideal ').replace('.ends physical','.ends ideal')
    lines=[line for line in text.splitlines() if not line.startswith('Xplate')]
    lines.insert(-1,'Cstore STORE GND 40p');(out/'ideal.spice').write_text('\n'.join(lines)+'\n')
    base=(ROOT/'build/capture-column-screen-v2-singlethread-20260925/27-1.6-100/test.spice').read_text()
    for name in diag.NAMES:
        base,count=re.subn(r'(?m)^\.include .*/'+name+r'\.spice$',f'.include {out}/{name}.spice',base);assert count==1
    jobs=[]
    for temp in a.temperatures:
        for level in a.levels:
            d=out/f'{temp}-{level:g}';d.mkdir()
            source=re.sub(r'(?m)^\.temp .*',f'.temp {temp}',base)
            source=re.sub(r'(?m)^Vcol .*',f'Vcol COL 0 PWL(0 2 1.2m 2 1.21m {level:g} 2.7m {level:g})',source)
            for name in diag.NAMES:
                for step in a.steps:jobs.append((d,source,name,step,temp,level))
    def run(job):
        d,source,name,step,temp,level=job
        r=diag.run_case(d,source,name,step,a.timeout,'sparse','trap','full')
        r.update(temperature_C=temp,input_V=level)
        if r['complete']:
            for values in r['samples'].values():
                assert values['sc']<.01 and values['scb']>3.29 and values['sel']>3.29 and values['selb']<.01
        return r
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,jobs))
    complete=all(r['complete'] for r in results)
    (out/'transients.json').write_text(json.dumps(results,indent=2)+'\n')
    assert complete,'Incomplete transient matrix; retained in transients.json'
    lookup={(r['temperature_C'],r['input_V'],r['model'],r['step_ns']):r for r in results}
    best=min(a.steps)
    refjobs=[(temp,level,name) for temp in a.temperatures for level in a.levels for name in ['rc','physical','ideal']]
    def run_reference(job):
        temp,level,name=job;d=out/f'{temp}-{level:g}'/f'{name}-{best}'
        values={str(duration):reference(d,name,level,duration) for duration in [200,400]}
        return job,values
    with ThreadPoolExecutor(max_workers=4) as pool:refs=dict(pool.map(run_reference,refjobs))
    comparisons=[]
    for temp in a.temperatures:
        for level in a.levels:
            for slot in ['first','last']:
                values={name:lookup[temp,level,name,best]['samples'][slot] for name in diag.NAMES}
                comparisons.append(dict(temperature_C=temp,input_V=level,slot=slot,
                    rc_minus_ideal_V=values['rc']['hold']-values['ideal']['hold'],
                    rc_minus_physical_V=values['rc']['hold']-values['physical']['hold'],
                    rc_tracking_error_V=values['rc']['hold']-refs[temp,level,'rc']['400']['hold'],
                    placement_difference_V=values['rcfar']['hold']-values['rc']['hold'],
                    max_timestep_difference_V=max(abs(lookup[temp,level,name,step]['samples'][slot]['hold']-values[name]['hold']) for step in a.steps for name in diag.NAMES),
                    reference_duration_difference_V=max(abs(refs[temp,level,name]['200']['hold']-refs[temp,level,name]['400']['hold']) for name in ['rc','physical','ideal'])))
    keys=['rc_minus_ideal_V','rc_minus_physical_V','rc_tracking_error_V','placement_difference_V','max_timestep_difference_V','reference_duration_difference_V']
    maxima={key:max(abs(r[key]) for r in comparisons) for key in keys}
    report=dict(scope=__doc__,complete=complete,conditions=len(a.temperatures)*len(a.levels),transient_runs=len(results),comparisons=comparisons,maxima=maxima,
        limits=dict(accuracy_V=500e-6,timestep_V=10e-6,reference_duration_V=10e-9),
        tracking_pass=maxima['rc_tracking_error_V']<500e-6,
        schematic_shift_under_500uV=maxima['rc_minus_ideal_V']<500e-6,
        timestep_pass=len(a.steps)>1 and maxima['max_timestep_difference_V']<10e-6,
        placement_pass=maxima['placement_difference_V']<10e-6,
        reference_duration_pass=maxima['reference_duration_difference_V']<10e-9,
        reference_results=[dict(temperature_C=t,input_V=l,model=n,values=v) for (t,l,n),v in refs.items()],
        model_sha256={name:hashlib.sha256((out/(name+'.spice')).read_bytes()).hexdigest() for name in diag.NAMES})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(maxima,indent=2),flush=True)


if __name__=='__main__':main()
