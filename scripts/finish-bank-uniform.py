"""Audit a bounded uniform-pattern temperature pair without changing prior reports."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--watch-seconds',type=float,default=25200)
    a=p.parse_args();assert a.watch_seconds>0
    a.out.mkdir(parents=True,exist_ok=False)
    cases=read(a.plan)['cases'];done={};failures={};render_failures={};started=time.monotonic()
    spec=importlib.util.spec_from_file_location('monitor',ROOT/'scripts/monitor-bank-full.py')
    monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)
    def execute(command,name):
        with (a.out/(name+'.log')).open('w') as log:
            subprocess.run([sys.executable]+command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
    while True:
        for case in cases:
            name=case['name']
            if name in done or name in failures:continue
            reports=[read(ROOT/case[key]/'result.json') for key in ['coarse','fine']]
            if any(r.get('reference_failure') or r.get('transient',{}).get('timed_out') or r.get('transient',{}).get('errors') for r in reports):
                failures[name]='Simulation failed; retained without an accuracy claim';continue
            if not all(r.get('completed') for r in reports):continue
            try:
                audit=a.out/(name+'-audit');destination=ROOT/'simulations'/case['report']
                assert not destination.exists(),str(destination)
                execute(['scripts/report-bank-full-v3.py','--run',case['coarse'],'--refined',case['fine'],
                         '--out',str(audit),'--temperature',str(case['temperature']),'--pattern',case['pattern']],name+'-audit')
                shutil.copyfile(audit/'result.json',destination)
                done[name]=read(destination)['selected_screen_pass']
            except (AssertionError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:failures[name]=str(error)
            if name in done:
                try:
                    execute(['scripts/render-bank-uniform.py','--plan',str(a.plan)],'render-'+name)
                except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
                    # A plotting failure must not count this case twice or end
                    # the watcher before the other simulation pair finishes.
                    render_failures[name]=str(error)
        expired=time.monotonic()-started>=a.watch_seconds
        state=dict(elapsed_seconds=time.monotonic()-started,
                   progress=[monitor.progress(ROOT/case[key]) for case in cases for key in ['coarse','fine']],
                   audited=done,failures=failures,render_failures=render_failures,watcher_expired=expired,all_pairs_audited=len(done)==len(cases),
                   all_selected_screens_pass=len(done)==len(cases) and all(done.values()))
        for case in cases:
            if case['name'] in done:
                for progress in state['progress']:
                    if progress['run'] in [str(ROOT/case[key]) for key in ['coarse','fine']]:
                        progress.update(phase='independent audit complete',selected_screen_pass=done[case['name']])
        temp=a.out/'status.tmp';temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(a.out/'status.json')
        if len(set(done)|set(failures))==len(cases) or expired:raise SystemExit(bool(failures) or bool(render_failures) or expired)
        time.sleep(30)

if __name__=='__main__':main()
