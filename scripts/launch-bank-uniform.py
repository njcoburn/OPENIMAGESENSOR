"""Launch one uniform illumination pattern at 27/125 C as a bounded batch."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
IMAGE='hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def build_plan(tag, pattern="dark"):
    assert pattern in ("dark", "middle", "bright")
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]*',tag), 'Use a nonempty lowercase tag'
    runs=[];cases=[]
    for temp in [27,125]:
        name=f'{pattern}{temp}'; lights=[{'dark':0,'middle':80,'bright':240}[pattern]]*2
        pair=[]
        for step in [100,50]:
            path=f'build/compact-bank-c64-uniform-{name}-{step}-{tag}';pair.append(path)
            command=['python3','scripts/simulate-compact-bank-v3.py','--layout','build/compact-bank-c64-ground-grid-20260927',
                     '--out',path,'--lights-pa',','.join(map(str,lights*32)),'--temperature',str(temp),'--step-ns',str(step),
                     '--solver','klu','--acquisition-us','12','--timeout','14400','--reference-timeout','1800',
                     '--reference-workers','4','--save-mim-terminals']
            if step==50:command.append('--transient-only')
            runs.append(dict(name=f'{name}-{step}',path=path,container=f'ois-bank-uniform-{name}-{step}-{tag}',
                             command=command,temperature=temp,pattern=pattern,step_ns=step))
        cases.append(dict(name=name,temperature=temp,pattern=pattern,coarse=pair[0],fine=pair[1],report=f'compact-bank-64-uniform-{name}.json'))
    return dict(created_at_utc=datetime.now(timezone.utc).isoformat(),image=IMAGE,runs=runs,cases=cases,
                completed=False,accuracy_qualified=False,scope='Four fresh transients and 384 independent references for one uniform illumination pattern at both temperatures. No other uniform patterns are launched in this batch.')

def preflight(plan):
    """Check inherited fixture identity and refuse any existing evidence outputs."""
    baseline=ROOT/'simulations/compact-bank-64-full.json'
    report=json.loads(baseline.read_text());assert report['selected_screen_pass'] and report['full_bank_readout_completed']
    inherited=['scripts/simulate-compact-bank-v3.py','scripts/report-bank-full-v2.py',
               'build/compact-bank-c64-ground-grid-20260927/verification.json',
               'build/compact-bank-c64-ground-grid-20260927/bank.gds',
               'build/compact-bank-c64-ground-grid-20260927/rc-port.spice']
    for name in inherited:assert sha(ROOT/name)==report['evidence_hashes'][name],name
    for run in plan['runs']:assert not (ROOT/run['path']).exists(),run['path']
    for case in plan['cases']:assert not (ROOT/'simulations'/case['report']).exists(),case['report']
    paths=[baseline]+[ROOT/name for name in inherited]
    paths += [ROOT/'scripts'/name for name in ['launch-bank-uniform.py','finish-bank-uniform.py','render-bank-uniform.py','test-bank-uniform.py','test-bank-uniform-watcher.py','report-bank-full-v3.py','update-overview-sections.py']]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tag',required=True);p.add_argument('--pattern',choices=['dark','middle','bright'],default='dark');a=p.parse_args()
    plan=build_plan(a.tag,a.pattern)
    plan_path=ROOT/'build'/f'compact-bank-uniform-plan-{a.tag}.json'
    watch_path=f'build/compact-bank-uniform-watch-{a.tag}'
    assert not plan_path.exists() and not (ROOT/watch_path).exists()
    plan['evidence_hashes']=preflight(plan)
    names={r['container'] for r in plan['runs']}|{f'ois-bank-uniform-watcher-{a.tag}'}
    existing=set(subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines())
    assert not names&existing, 'Container names must be fresh'
    def publish():
        tmp=plan_path.with_suffix('.tmp');tmp.write_text(json.dumps(plan,indent=2)+'\n');tmp.replace(plan_path)
    publish()
    common=['docker','run','-d','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/foss/designs','-w','/foss/designs','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1',
            '-e','PDK=gf180mcuD','-e','PDK_ROOT=/foss/pdks','-e','PDKPATH=/foss/pdks/gf180mcuD','--entrypoint','/bin/bash']
    def launch(name,command):
        return subprocess.check_output(common+['--name',name,IMAGE,'-lc','exec "$@"','bash']+command,text=True).strip()
    for run in plan['runs']:
        run['container_id']=launch(run['container'],run['command']);publish();print(run['name'],run['container_id'],flush=True)
    watcher=f'ois-bank-uniform-watcher-{a.tag}'
    command=['python3','scripts/finish-bank-uniform.py','--plan',str(plan_path.relative_to(ROOT)),'--out',watch_path]
    plan['watcher']=dict(container=watcher,path=watch_path,container_id=launch(watcher,command))
    publish();print('Plan:',plan_path)

if __name__=='__main__':main()
