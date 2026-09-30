"""Bounded unattended physical-bank verification; advance only after audited passes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
def read(p):
    try:return json.loads(p.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def atomic(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');tmp.replace(p)
def stage_pass(reports,expected,failures):
    return not failures and len(reports)==expected and all(r.get('selected_screen_pass') is True for r in reports)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);a=p.parse_args();plan=read(a.plan)
    out=ROOT/plan['output'];out.mkdir(parents=True,exist_ok=False)
    state=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),phase='starting',finished=False,completed=False,completed_stages=[],audited={},failures={},render_failures={},active_runs=[],planned_stages=len(plan['stages']),planned_cases=sum(len(s['cases']) for s in plan['stages']),all_selected_screens_pass=False,all_pairs_audited=False,watcher_expired=False)
    started=time.monotonic()
    def publish():
        state.update(updated_at_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-started);atomic(out/'status.json',state)
    def verify():
        for name,digest in plan['evidence_hashes'].items():assert sha(ROOT/name)==digest,name
    spec=importlib.util.spec_from_file_location('bank',ROOT/'scripts/simulate-compact-bank-v6.py');bank=importlib.util.module_from_spec(spec);spec.loader.exec_module(bank)
    def job(run):
        logpath=out/(run['name']+'.log');begin=time.monotonic();timed_out=False
        with logpath.open('w') as log:
            proc=subprocess.Popen(run['command'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=proc.wait(timeout=plan['job_timeout_seconds'])
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(proc.pid,signal.SIGKILL);proc.wait();code=124
        result=dict(returncode=code,timed_out=timed_out,elapsed_seconds=time.monotonic()-begin,finished_at_utc=datetime.now(timezone.utc).isoformat())
        atomic(ROOT/run['exit_record'],result);return result
    def render():
        with (out/'render.log').open('a') as log:subprocess.run([sys.executable,'scripts/render-bank-stack5-progress.py','--plan',str(a.plan)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    publish()
    try:
        verify()
        for stage in plan['stages']:
            if time.monotonic()-started>plan['sequence_timeout_seconds']:
                state['watcher_expired']=True;raise RuntimeError('Sequence deadline reached; no next stage launched')
            free=shutil.disk_usage(ROOT).free;assert free>plan['minimum_free_bytes'],'Disk reserve reached; no next stage launched'
            verify();state.update(phase='simulating',stage=stage['name'],active_runs=[r['name'] for r in stage['runs']]);publish();render()
            exits={};audited_this={};failed_this={}
            with ThreadPoolExecutor(max_workers=plan['max_workers']) as pool:
                futures={r['name']:pool.submit(job,r) for r in stage['runs']}
                while True:
                    for run in stage['runs']:
                        name=run['name']
                        if name not in exits and futures[name].done():
                            exits[name]=futures[name].result()
                            if exits[name]['returncode']!=0:failed_this[name]='Simulation exited unsuccessfully; inspect exit record'
                    for case in stage['cases']:
                        name=case['name']
                        if name in audited_this or name in failed_this:continue
                        if not all(n in exits for n in case['run_names']):continue
                        if any(exits[n]['returncode']!=0 for n in case['run_names']):failed_this[name]='A simulation failed';continue
                        try:
                            verify();assert all(read(ROOT/r/'result.json').get('completed') for r in [case['coarse'],case['fine']])
                            audit=out/(name+'-audit');dest=ROOT/case['report'];assert not dest.exists()
                            command=[sys.executable,'scripts/report-bank-stack5.py','--layout',plan['layout'],'--run',case['coarse'],'--refined',case['fine'],'--out',str(audit),'--mos-corner',case['corner'],'--temperature',str(case['temperature']),'--pattern',case['pattern']]
                            with (out/(name+'-audit.log')).open('w') as log:subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
                            report=read(audit/'result.json');assert isinstance(report.get('selected_screen_pass'),bool)
                            shutil.copyfile(audit/'result.json',dest);audited_this[name]=report;state['audited'][name]=report['selected_screen_pass']
                            if not report['selected_screen_pass']:failed_this[name]='Measured electrical/refinement failure; later stages will not launch'
                        except Exception as exc:failed_this[name]=str(exc)
                        publish();render()
                    progress=[]
                    for run in stage['runs']:
                        directory=ROOT/run['path'];last=bank.saved_progress(directory/'transient/stream.raw');r=read(directory/'result.json')
                        progress.append(dict(name=run['name'],last_saved_ms=None if last is None else last*1000,runner_completed=r.get('completed',False),references=r.get('reference_progress'),exit=exits.get(run['name'])))
                    state.update(progress=progress,active_runs=[n for n,f in futures.items() if f.running()],queued_runs=[n for n,f in futures.items() if not f.running() and not f.done()]);state['failures'].update(failed_this);publish()
                    if len(exits)==len(futures):break
                    time.sleep(20)
            if not stage_pass(list(audited_this.values()),len(stage['cases']),failed_this):raise RuntimeError('Stage did not pass all required independent audits')
            state['completed_stages'].append(stage['name']);state['phase']='stage_complete';publish();render()
        state.update(completed=True,all_pairs_audited=True,all_selected_screens_pass=True,phase='complete')
    except Exception as exc:
        state['failures']['sequence']=str(exc);state['phase']='stopped_for_review'
    finally:
        state['finished']=True;state['active_runs']=[];publish()
        try:render()
        except Exception as exc:state['render_failures']['final']=str(exc);publish()
    raise SystemExit(not state['completed'] or bool(state['render_failures']))
if __name__=='__main__':main()
