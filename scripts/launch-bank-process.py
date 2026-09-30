"""Launch a bounded two-corner MOS screen on the retained 64-column layout."""
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
LAYOUT='build/compact-bank-c64-ground-grid-20260927'
SOURCES=['simulate-compact-bank-v4.py','report-bank-process.py','bank-process-common.py','test-bank-process.py','test-bank-process-watcher.py','run-bank-process-job.py','launch-bank-process.py','finish-bank-process.py','render-bank-process.py','update-verification-journal.py','verify-bank-process-control.py','report-bank-process-controls.py']

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def build_plan(tag):
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]*',tag), 'Use a fresh lowercase tag'
    runs=[];cases=[]
    for corner in ['ss','ff']:
        name=f'{corner}-inverse125';pair=[]
        for step in [100,50]:
            path=f'build/compact-bank-process-{name}-{step}-{tag}';pair.append(path)
            command=['python3','scripts/simulate-compact-bank-v4.py','--layout',LAYOUT,'--out',path,
                     '--mos-corner',corner,'--lights-pa',','.join(map(str,[240,0]*32)),
                     '--temperature','125','--step-ns',str(step),'--solver','klu','--acquisition-us','12',
                     '--timeout','14400','--reference-timeout','1800','--reference-workers','4','--save-mim-terminals']
            if step==50:command+=['--transient-only']
            runs.append(dict(name=f'{name}-{step}',path=path,container=f'ois-bank-process-{name}-{step}-{tag}',command=command,
                             exit_record=f'build/compact-bank-process-exits-{tag}/{name}-{step}.json',corner=corner,step_ns=step))
        cases.append(dict(name=name,mos_corner=corner,temperature=125,pattern='inverse',coarse=pair[0],fine=pair[1],
                          report=f'compact-bank-process-{name}-{tag}.json',baseline_report='simulations/compact-bank-64-full-hot.json'))
    return dict(created_at_utc=datetime.now(timezone.utc).isoformat(),image=IMAGE,layout=LAYOUT,runs=runs,cases=cases,
                completed=False,accuracy_qualified=False,scope='SS and FF MOS-only corners, 125 C inverse, nominal 3.3 V source/wire and typical diode/MIM. Four fresh 100/50 ns transients and 384 matched references. No subsequent batch auto-started.')

def preflight(plan,tests,control,pdk):
    baseline=ROOT/'simulations/compact-bank-64-full-hot.json';report=json.loads(baseline.read_text())
    assert report['selected_screen_pass'] and report['full_bank_readout_completed']
    inherited=['scripts/simulate-compact-bank-v3.py','scripts/report-bank-full-v2.py',f'{LAYOUT}/verification.json',f'{LAYOUT}/bank.gds',f'{LAYOUT}/rc-port.spice']
    for name in inherited:assert sha(ROOT/name)==report['evidence_hashes'][name],name
    assert json.loads(tests.read_text())['passed'] is True
    assert json.loads(control.read_text())['exact_reproduction'] is True
    for record in [tests,control]:
        for name,digest in json.loads(record.read_text())['source_hashes'].items():assert sha(ROOT/name)==digest,name
    control_review=json.loads(control.read_text())
    assert control_review['control_implementation_valid'] is True
    assert {c['mos_corner'] for c in control_review['small_process_controls']}=={'ss','ff'}
    for c in control_review['small_process_controls']:
        assert c['independent_audit_completed'] and c['checks']['refinement'] and c['checks']['event_refinement']
        assert c['selected_screen_pass']==all(c['checks'].values())
    # A measured electrical failure is retained; it cannot become a test-tool failure or a pass.
    plan['small_control_electrical_results']=[dict(mos_corner=c['mos_corner'],selected_screen_pass=c['selected_screen_pass']) for c in control_review['small_process_controls']]
    assert set(json.loads(pdk.read_text())['mos_corners'])=={'typical','ss','ff','fs','sf'}
    for run in plan['runs']:
        assert not (ROOT/run['path']).exists() and not (ROOT/run['exit_record']).exists()
    for case in plan['cases']:assert not (ROOT/'simulations'/case['report']).exists()
    files=[baseline,tests,control,pdk]+[ROOT/name for name in inherited]+[ROOT/'scripts'/s for s in SOURCES]
    return {str(p.resolve().relative_to(ROOT)):sha(p) for p in files}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tag',required=True)
    p.add_argument('--tests',type=Path,required=True);p.add_argument('--control',type=Path,required=True);p.add_argument('--pdk',type=Path,required=True)
    a=p.parse_args();plan=build_plan(a.tag)
    dest=ROOT/'build'/f'compact-bank-process-plan-{a.tag}.json';watch=f'build/compact-bank-process-watch-{a.tag}'
    assert not dest.exists() and not (ROOT/watch).exists()
    plan['evidence_hashes']=preflight(plan,a.tests,a.control,a.pdk)
    plan['pdk_provenance']=json.loads(a.pdk.read_text())
    names={r['container'] for r in plan['runs']}|{f'ois-bank-process-watcher-{a.tag}'}
    assert not names&set(subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines())
    def publish():
        tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(plan,indent=2)+'\n');tmp.replace(dest)
    publish()
    common=['docker','run','-d','--user',f'{os.getuid()}:{os.getgid()}','-v',f'{ROOT}:/foss/designs','-w','/foss/designs',
            '-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','PDK=gf180mcuD','-e','PDK_ROOT=/foss/pdks','-e','PDKPATH=/foss/pdks/gf180mcuD','--entrypoint','/bin/bash']
    def launch(name,command):return subprocess.check_output(common+['--name',name,IMAGE,'-lc','exec "$@"','bash']+command,text=True).strip()
    try:
        for run in plan['runs']:
            run['container_id']=launch(run['container'],['python3','scripts/run-bank-process-job.py','--exit-record',run['exit_record']]+run['command']);publish();print(run['name'],run['container_id'],flush=True)
        watcher=f'ois-bank-process-watcher-{a.tag}'
        plan['watcher']=dict(container=watcher,path=watch)
        publish()
        plan['watcher']['container_id']=launch(watcher,['python3','scripts/finish-bank-process.py','--plan',str(dest.relative_to(ROOT)),'--out',watch]);publish()
    except Exception as error:
        plan['launch_failure']=str(error);publish();raise
    print('Plan:',dest)

if __name__=='__main__':main()
