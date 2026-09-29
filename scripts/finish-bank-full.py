"""Watch the retained full-bank runs and audit/render each completed pair.

This does not create accuracy claims from partial traces or stop simulations.
Run inside the pinned tool container. Completed evidence is never overwritten.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
CASES=[dict(name='nominal',temperature=27,pattern='alternating',coarse='compact-bank-c64-grid-full100-20260927',fine='compact-bank-c64-grid-full50-20260927',report='compact-bank-64-full.json'),
       dict(name='hot-inverse',temperature=125,pattern='inverse',coarse='compact-bank-c64-grid-hot-inverse100-20260927',fine='compact-bank-c64-grid-hot-inverse50-20260927',report='compact-bank-64-full-hot.json')]


def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--watch-seconds',type=float,default=18000);p.add_argument('--poll-seconds',type=float,default=30);a=p.parse_args()
    assert a.watch_seconds>0 and 1<=a.poll_seconds<=60
    a.out.mkdir(parents=True,exist_ok=False);start=time.monotonic();done=set();failures={}
    spec=importlib.util.spec_from_file_location('monitor',ROOT/'scripts/monitor-bank-full.py');monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)
    def run(command,name):
        with (a.out/(name+'.log')).open('w') as log:
            subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
    while time.monotonic()-start<a.watch_seconds:
        progress=[monitor.progress(ROOT/'build'/case[key]) for case in CASES for key in ['coarse','fine']]
        state=dict(elapsed_seconds=time.monotonic()-start,progress=progress,audited=sorted(done),failures=failures,all_pairs_audited=len(done)==len(CASES))
        temp=a.out/'status.tmp';temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(a.out/'status.json')
        print(json.dumps(dict(elapsed_minutes=state['elapsed_seconds']/60,progress=[dict(run=x['run'],phase=x['phase'],samples=x['observed_sample_instants'],references=x.get('references')) for x in progress],audited=sorted(done))),flush=True)
        for case in CASES:
            if case['name'] in done or case['name'] in failures:continue
            coarse=ROOT/'build'/case['coarse'];fine=ROOT/'build'/case['fine'];reports=[read(d/'result.json') for d in [coarse,fine]]
            if any(r.get('reference_failure') or r.get('transient',{}).get('timed_out') or r.get('transient',{}).get('errors') for r in reports):
                failures[case['name']]='Simulation failure; raw evidence retained, no accuracy audit';continue
            if not all(r.get('completed') for r in reports):continue
            destination=ROOT/'simulations'/case['report'];assert not destination.exists(),str(destination)
            audit=a.out/(case['name']+'-audit')
            try:
                run([sys.executable,'scripts/report-bank-full.py','--run',str(coarse),'--refined',str(fine),'--out',str(audit),'--temperature',str(case['temperature']),'--pattern',case['pattern']],case['name']+'-audit')
                shutil.copyfile(audit/'result.json',destination);done.add(case['name'])
                if (ROOT/'simulations/compact-bank-64-full.json').exists():
                    run([sys.executable,'scripts/render-bank-full.py'],'render-'+case['name'])
                    run([sys.executable,'scripts/update-overview-sections.py'],'overview-'+case['name'])
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
                failures[case['name']]=str(error)
        if len(done)+len(failures)==len(CASES):
            state.update(audited=sorted(done),failures=failures,all_pairs_audited=len(done)==len(CASES));(a.out/'status.json').write_text(json.dumps(state,indent=2)+'\n')
            raise SystemExit(bool(failures))
        time.sleep(a.poll_seconds)
    raise SystemExit('Watcher deadline reached; simulation processes were not stopped.')


if __name__=='__main__':main()
