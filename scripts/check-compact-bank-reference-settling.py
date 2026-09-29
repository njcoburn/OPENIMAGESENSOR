"""Extend selected reference fallback endpoints without changing the circuit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    import numpy as np
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--references',nargs='+',required=True)
    p.add_argument('--timeout',type=float,default=180)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'runner.py').write_bytes(Path(__file__).read_bytes())
    spec=importlib.util.spec_from_file_location('reader',ROOT/'scripts/diagnose-capture-transient.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    evidence=[a.run/'tile.spice',a.run/'.spiceinit',a.out/'runner.py',ROOT/'scripts/diagnose-capture-transient.py']
    def check(name):
        source=a.run/name;out=a.out/name;out.mkdir()
        old=(source/'test.spice').read_text()
        new,count=re.subn(r'(?m)^optran 1 1 1 100n 400u 0$', 'optran 1 1 1 100n 1m 0',old)
        assert count==1
        (out/'test.spice').write_text(new)
        start=time.monotonic();expired=False;code=None
        with (out/'ngspice.log').open('w') as log:
            try:
                code=subprocess.run(['ngspice','-b','test.spice'],cwd=out,stdout=log,stderr=subprocess.STDOUT,
                    timeout=a.timeout,env={**os.environ,'SPICE_USERINIT_DIR':str(a.run.resolve()),'OMP_NUM_THREADS':'1'}).returncode
            except subprocess.TimeoutExpired:expired=True
        log=(out/'ngspice.log').read_text()
        errors=[line for line in log.splitlines() if re.search(r'timestep too small|aborted|^Error|no such command',line,re.I)]
        ix,data=reader.trace(out/'op.raw');oi,od=reader.trace(source/'op.raw')
        complete=code==0 and not expired and not errors and data is not None and len(data)==1 and bool(np.isfinite(data).all())
        report=dict(name=name,completed=complete,seconds=time.monotonic()-start,returncode=code,timed_out=expired,
                    errors=errors,transient_fallback='Transient op started' in log)
        if complete:
            assert ix==oi and len(od)==1
            changes={n:float(data[0,j]-od[0,j])*1e6 for n,j in ix.items() if n.startswith('v(')}
            report.update(changes_uV=changes,max_saved_voltage_change_uV=max(map(abs,changes.values())),hold_change_uV=changes['v(hold)'])
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    with ThreadPoolExecutor(max_workers=3) as pool:reports=list(pool.map(check,a.references))
    for name in a.references:
        evidence.extend(a.run/name/f for f in ['test.spice','op.raw','execution.json'])
    evidence.extend(f for f in a.out.rglob('*') if f.is_file())
    hashes={str(f.resolve().relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(set(evidence))}
    report=dict(scope=__doc__,source=str(a.run),original_endpoint_s=.0004,extended_endpoint_s=.001,
                references=reports,evidence_hashes=hashes,all_completed=all(r['completed'] for r in reports))
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='changes_uV'} for r in reports],indent=2))
    if not report['all_completed']:raise SystemExit(1)


if __name__=='__main__':main()
