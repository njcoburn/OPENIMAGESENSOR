"""Audit MOS-process pairs, preserving failures and all prior reports."""
import argparse
import hashlib
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
    plan=read(a.plan)
    def verify_sources():
        for name,digest in plan['evidence_hashes'].items():
            with (ROOT/name).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest,name
    verify_sources()
    cases=plan['cases'];done={};failures={};render_failures={};started=time.monotonic()
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
            runs=[r for r in plan['runs'] if r['path'] in [case['coarse'],case['fine']]]
            exits=[read(ROOT/r['exit_record']) for r in runs]
            if any(e and e.get('returncode')!=0 for e in exits):
                failures[name]='Simulation process exited unsuccessfully; inspect exit record and log';continue
            if any(e and not r.get('completed') for e,r in zip(exits,reports)):
                failures[name]='Process exited without a completed result';continue
            if any(r.get('reference_failure') or r.get('transient',{}).get('timed_out') or r.get('transient',{}).get('errors') for r in reports):
                failures[name]='Simulation failed; retained without an accuracy claim';continue
            if not all(r.get('completed') for r in reports) or len(exits)!=2 or not all(exits):continue
            try:
                verify_sources()
                assert all(r.get('pdk_provenance')==plan['pdk_provenance'] for r in reports)
                audit=a.out/(name+'-audit');destination=ROOT/'simulations'/case['report']
                assert not destination.exists(),str(destination)
                execute(['scripts/report-bank-process.py','--run',case['coarse'],'--refined',case['fine'],
                         '--out',str(audit),'--layout',plan['layout'],'--mos-corner',case['mos_corner'],'--temperature',str(case['temperature']),'--pattern',case['pattern']],name+'-audit')
                shutil.copyfile(audit/'result.json',destination)
                done[name]=read(destination)['selected_screen_pass']
            except (AssertionError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:failures[name]=str(error)
            if name in done:
                try:
                    execute(['scripts/render-bank-process.py','--plan',str(a.plan)],'render-'+name)
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
        if len(set(done)|set(failures))==len(cases) or expired:
            try:execute(['scripts/render-bank-process.py','--plan',str(a.plan)],'render-final')
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired):raise SystemExit(1)
            raise SystemExit(bool(failures) or bool(render_failures) or expired or not all(done.values()))
        time.sleep(30)

if __name__=='__main__':main()
