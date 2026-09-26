"""Independently vary COL and BIAS shunt placement against the accepted matrix.

Uses the same single-column fixtures and compares both output and stored charge.
Run after qualify-capture-column.py, inside the pinned tools container.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import re
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('diag',ROOT/'scripts/diagnose-capture-transient.py')
diag=importlib.util.module_from_spec(spec);spec.loader.exec_module(diag)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--extraction',type=Path,required=True)
    p.add_argument('--matrix',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'diagnose-capture-transient.py').write_bytes((ROOT/'scripts/diagnose-capture-transient.py').read_bytes())
    jobs=[]
    for net in ['col','bias']:
        d=out/net;d.mkdir()
        text=(a.extraction/f'rc-{net}-far.spice').read_text()
        text=text.replace('.subckt flat ','.subckt rc ').replace('.ends flat','.ends rc')
        (d/'rc.spice').write_text(text)
        for temp in [27,125]:
            for level in [1.2,1.6,2.0]:
                base=a.matrix/f'{temp}-{level:g}'/'rc-50'
                source=(base/'test.spice').read_text()
                source,count=re.subn(r'(?m)^\.include .*/rc\.spice$',f'.include {d}/rc.spice',source)
                assert count==1
                case=d/f'{temp}-{level:g}';case.mkdir()
                jobs.append((net,temp,level,case,source,base))
    def run(job):
        net,temp,level,case,source,base=job
        result=diag.run_case(case,source,'rc',50,60,'sparse','trap','full')
        assert result['complete'],case
        original=json.loads((base/'result.json').read_text())
        assert original['complete']
        # Check the emitted fixture; only the model include path may change.
        def normalized(path):
            return re.sub(r'(?m)^\.include .*/rc\.spice$','.include /MODEL',path.read_text())
        assert normalized(base/'test.spice')==normalized(case/'rc-50/test.spice')
        ix,data=diag.trace(case/'rc-50/stream.raw')
        assert np.max(np.diff(data[:,0]))<=50e-9*1.001
        differences={node:max(abs(result['samples'][slot][node]-original['samples'][slot][node])
                             for slot in ['first','last']) for node in ['hold','store','cbuf','buf']}
        for sample in result['samples'].values():
            assert sample['sc']<.01 and sample['scb']>3.29 and sample['sel']>3.29 and sample['selb']<.01
        assert max(differences.values())<10e-6
        return dict(far_net=net,temperature_C=temp,input_V=level,differences_V=differences,
                    result_sha256=hashlib.sha256((case/'rc-50/result.json').read_bytes()).hexdigest())
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,jobs))
    report=dict(passed=True,runs=results,transient_runs=len(results),limit_V=10e-6,
                max_output_difference_uV=max(r['differences_V']['hold'] for r in results)*1e6,
                max_any_observed_difference_uV=max(max(r['differences_V'].values()) for r in results)*1e6,
                scope=__doc__)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
