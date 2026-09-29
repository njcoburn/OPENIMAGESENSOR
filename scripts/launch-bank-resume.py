"""Launch fresh, bounded complete-bank attempts; retain all previous evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
IMAGE='hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tag',required=True);p.add_argument('--snapshot',type=Path,required=True)
    a=p.parse_args()
    assert all(c.isalnum() or c=='-' for c in a.tag)
    snapshot=a.snapshot.resolve().relative_to(ROOT)
    plan_path=ROOT/'build'/f'compact-bank-resume-plan-{a.tag}.json'
    assert not plan_path.exists()
    runs=[]
    for name,temp,step,pattern in [('nominal100',27,100,[0,240]),('nominal50',27,50,[0,240]),('hot-inverse100',125,100,[240,0]),('hot-inverse50',125,50,[240,0])]:
        path=f'build/compact-bank-c64-resume-{name}-{a.tag}'
        assert not (ROOT/path).exists(),path
        cmd=['python3','scripts/simulate-compact-bank-v3.py','--layout','build/compact-bank-c64-ground-grid-20260927',
             '--out',path,'--lights-pa',','.join(map(str,pattern*32)),'--temperature',str(temp),'--step-ns',str(step),
             '--solver','klu','--acquisition-us','12','--timeout','14400','--reference-timeout','1800',
             '--reference-workers','4','--save-mim-terminals']
        if step==50:cmd+=['--transient-only']
        if name=='nominal100':cmd+=['--reuse-transient','build/compact-bank-c64-grid-full100-20260927','--reuse-manifest',str(snapshot),'--reuse-references']
        runs.append(dict(name=name,path=path,container=f'ois-bank-{name}-{a.tag}',command=cmd,temperature=temp,step_ns=step))
    cases=[dict(name='nominal',temperature=27,pattern='alternating',coarse=runs[0]['path'],fine=runs[1]['path'],report='compact-bank-64-full.json'),
           dict(name='hot-inverse',temperature=125,pattern='inverse',coarse=runs[2]['path'],fine=runs[3]['path'],report='compact-bank-64-full-hot.json')]
    plan=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),snapshot=str(snapshot),runs=runs,cases=cases,
              completed=False,accuracy_qualified=False,scope='Three fresh transients, one audited transient reuse; 64 reusable DC references and 320 new planned references.')
    def publish():plan_path.write_text(json.dumps(plan,indent=2)+'\n')
    publish()
    common=['docker','run','-d','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/foss/designs','-w','/foss/designs','-e','OMP_NUM_THREADS=1',
            '-e','OPENBLAS_NUM_THREADS=1','-e','PDK=gf180mcuD','-e','PDK_ROOT=/foss/pdks',
            '-e','PDKPATH=/foss/pdks/gf180mcuD','--entrypoint','/bin/bash']
    for run in runs:
        run['container_id']=subprocess.check_output(common+['--name',run['container'],IMAGE,'-lc','exec "$@"','bash']+run['command'],text=True).strip()
        publish();print(run['name'],run['container_id'],flush=True)
    watcher=f'ois-bank-watcher-{a.tag}'
    out=f'build/compact-bank-resume-watch-{a.tag}'
    command=['python3','scripts/finish-bank-resume.py','--plan',str(plan_path.relative_to(ROOT)),'--out',out]
    plan['watcher']=dict(container=watcher,path=out,container_id=subprocess.check_output(common+['--name',watcher,IMAGE,'-lc','exec "$@"','bash']+command,text=True).strip())
    publish();print('Plan:',plan_path)

if __name__=='__main__':main()
