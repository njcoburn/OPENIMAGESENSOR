"""Launch joint full-bank shunt placement at nominal alternating and hot inverse."""
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

def build_plan(tag):
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]*',tag), 'Use a nonempty lowercase tag'
    runs=[];cases=[]
    for temp,pattern,lights,baseline in [(27,'alternating',[0,240],'compact-bank-64-full.json'),(125,'inverse',[240,0],'compact-bank-64-full-hot.json')]:
        name=f'{pattern}{temp}'
        pair=[]
        for step in [100,50]:
            path=f'build/compact-bank-c64-placement-{name}-{step}-{tag}';pair.append(path)
            command=['python3','scripts/simulate-compact-bank-v3.py','--layout','build/compact-bank-c64-ground-grid-20260927',
                     '--out',path,'--model','rc-far','--lights-pa',','.join(map(str,lights*32)),'--temperature',str(temp),'--step-ns',str(step),
                     '--solver','klu','--acquisition-us','12','--timeout','14400','--reference-timeout','1800',
                     '--reference-workers','4','--save-mim-terminals']
            if step==50:command.append('--transient-only')
            runs.append(dict(name=f'{name}-{step}',path=path,container=f'ois-bank-placement-{name}-{step}-{tag}',
                             command=command,temperature=temp,pattern=pattern,step_ns=step))
        cases.append(dict(name=name,temperature=temp,pattern=pattern,coarse=pair[0],fine=pair[1],report=f'compact-bank-64-placement-{name}.json',baseline_report='simulations/'+baseline))
    return dict(created_at_utc=datetime.now(timezone.utc).isoformat(),image=IMAGE,runs=runs,cases=cases,
                completed=False,accuracy_qualified=False,scope='Four fresh transients and 384 references for joint far-node shunt placement at nominal alternating and hot inverse; 100/50 ns refinement and matched baseline sensitivity checks.')

def preflight(plan):
    """Check inherited fixture identity and refuse any existing evidence outputs."""
    baseline=ROOT/'simulations/compact-bank-64-full.json'
    report=json.loads(baseline.read_text());assert report['selected_screen_pass'] and report['full_bank_readout_completed']
    inherited=['scripts/simulate-compact-bank-v3.py','scripts/report-bank-full-v2.py',
               'build/compact-bank-c64-ground-grid-20260927/verification.json',
               'build/compact-bank-c64-ground-grid-20260927/bank.gds',
               'build/compact-bank-c64-ground-grid-20260927/rc-port.spice','build/compact-bank-c64-ground-grid-20260927/rc-far.spice']
    for name in inherited:
        expected=(json.loads((ROOT/'build/compact-bank-c64-ground-grid-20260927/verification.json').read_text())['hashes']['rc-far.spice'] if name.endswith('/rc-far.spice') else report['evidence_hashes'][name])
        assert sha(ROOT/name)==expected,name
    for run in plan['runs']:assert not (ROOT/run['path']).exists(),run['path']
    for case in plan['cases']:assert not (ROOT/'simulations'/case['report']).exists(),case['report']
    paths=[baseline]+[ROOT/name for name in inherited]
    paths += [ROOT/'scripts'/name for name in ['launch-bank-placement.py','finish-bank-placement.py','render-bank-placement.py','test-bank-placement.py','test-bank-placement-watcher.py','report-bank-placement.py','bank-placement-common.py','update-overview-sections.py']]
    paths += [ROOT/c['baseline_report'] for c in plan['cases']]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tag',required=True);a=p.parse_args()
    plan=build_plan(a.tag)
    plan_path=ROOT/'build'/f'compact-bank-placement-plan-{a.tag}.json'
    watch_path=f'build/compact-bank-placement-watch-{a.tag}'
    assert not plan_path.exists() and not (ROOT/watch_path).exists()
    plan['evidence_hashes']=preflight(plan)
    names={r['container'] for r in plan['runs']}|{f'ois-bank-placement-watcher-{a.tag}'}
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
    watcher=f'ois-bank-placement-watcher-{a.tag}'
    command=['python3','scripts/finish-bank-placement.py','--plan',str(plan_path.relative_to(ROOT)),'--out',watch_path]
    plan['watcher']=dict(container=watcher,path=watch_path,container_id=launch(watcher,command))
    publish();print('Plan:',plan_path)

if __name__=='__main__':main()
