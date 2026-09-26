"""Complete nominal/hot readout and refinement on the extracted row power grid.

Run inside the tools container. Existing evidence is never overwritten. Four
transients run concurrently; each 100 ns case then gets all 64 independent
output references. Every subprocess keeps its exact command and log.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--source',type=Path,default=ROOT/'build/row-power-grid-20260924')
    p.add_argument('--timeout',type=float,default=7200)
    p.add_argument('--dc-workers',type=int,default=3,
                   help='Independent reference solves per temperature; size for available CPU and RAM')
    a=p.parse_args()
    assert a.dc_workers>0
    out=a.output.resolve();source=a.source.resolve()
    out.mkdir(parents=True,exist_ok=False)
    scripts=['qualify-grid-readout.py','simulate-array-strips.py','finish-column-capture.py',
             'check-column-capture-reference.py','analyze-strip-recovery.py','diagnose-functional-camera.py']
    snapshots=out/'scripts';snapshots.mkdir()
    for name in scripts:shutil.copyfile(ROOT/'scripts'/name,snapshots/name)
    model=source/'r1c64/rc-port.spice'
    manifest={'source':str(source),'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
              'output_error_limit_V':500e-6,'refinement_limit_V':10e-6,
              'scope':'Typical-process 64-column row, extracted pixel/row wire R+C, schematic storage/periphery. Fixed nominal interconnect at both device temperatures.',
              'dc_workers_per_temperature':a.dc_workers,'runs':{}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    def command(label,args):
        cmd=[sys.executable,str(ROOT/'scripts'/args[0]),*args[1:]]
        (out/(label+'-command.json')).write_text(json.dumps(cmd,indent=2)+'\n')
        with (out/(label+'.log')).open('w') as f:
            proc=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
        assert proc.returncode==0,(label,proc.returncode)
    def case(temp,step):
        name=f'{temp}-{step}';started=time.monotonic();run=out/name
        status={'temperature_C':temp,'step_ns':step,'transient_completed':False,'matched_completed':False}
        statusfile=out/(name+'-status.json')
        def save():statusfile.write_text(json.dumps(status,indent=2)+'\n')
        save()
        try:
            command(name,['simulate-array-strips.py','--source',str(source),'--output',str(run),
                '--cases','r1c64','--modes','rc-port','--fixture','imaging','--transient-only',
                '--column-storage-pf','40','--reset-after-capture','--bias-ohm','500000',
                '--pref-ohm','12400','--acquisition-us','10','--slot-us','20',
                '--reltol','1e-6','--solver','sparse','--temperature',str(temp),
                '--step-ns',str(step),'--timeout',str(a.timeout)])
            result=json.loads((run/'r1c64-rc-port/result.json').read_text())
            assert result['completed'] and len(result['samples'])==64,result.get('execution')
            assert result['model_sha256']==manifest['model_sha256']
            status['transient_completed']=True;save()
            print(json.dumps({'case':name,'event':'transient complete','seconds':time.monotonic()-started}),flush=True)
            if step==100:
                matched=out/(name+'-matched')
                command(name+'-matched',['finish-column-capture.py','--source',str(source),
                    '--run',str(run/'r1c64-rc-port'),'--output',str(matched),
                    '--dc-workers',str(a.dc_workers),'--dc-timeout','600'])
                r=json.loads((matched/'r1c64-rc-port/result.json').read_text())
                assert r['completed'] and len(r['samples'])==64
                status.update(matched_completed=True,tracking_screen_pass=r['tracking_screen_pass'],
                              max_output_error_V=r['max_tracking_error_V'])
            else:
                command(name+'-analysis',['analyze-strip-recovery.py','--source',str(source),str(run)])
        except Exception as e:
            status['error']=repr(e)
        status['seconds']=time.monotonic()-started;save()
        print(json.dumps({'case':name,**status}),flush=True)
        return name,status
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs=[pool.submit(case,t,s) for t in [27,125] for s in [200,100]]
        for future in as_completed(jobs):
            name,status=future.result();manifest['runs'][name]=status
            (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert all('error' not in r for r in manifest['runs'].values()),'See preserved run logs/status'

if __name__=='__main__':main()
