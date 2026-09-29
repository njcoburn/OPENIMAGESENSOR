"""Run the remaining five-pattern bank screens with bounded independent jobs.

Alternating dark/bright is supplied by the separate thermal/refinement controls.
This batch adds its inverse and uniform dark, middle and bright illumination.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--workers',type=int,choices=range(1,5),default=3)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    for name in ['screen-bank-patterns.py','simulate-compact-bank.py','diagnose-capture-transient.py']:
        (a.out/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    meta=json.loads((a.layout/'verification.json').read_text());assert meta['columns']==16
    patterns={'inverse':[240,0]*8,'dark':[0]*16,'middle':[80]*16,'bright':[240]*16}
    jobs=[(temp,name,lights) for name,lights in patterns.items() for temp in [27,125]]
    def run(job):
        temp,name,lights=job;directory=a.out/f'{name}-{temp}';start=time.monotonic();expired=False
        command=[sys.executable,str(a.out/'simulate-compact-bank.py'),'--layout',str(a.layout),
                 '--out',str(directory),'--lights-pa',','.join(map(str,lights)),
                 '--temperature',str(temp),'--step-ns','100','--solver','klu','--timeout','1200','--reference-workers','2']
        # The simulator snapshots its own source, but resolves shared helpers
        # against ROOT. Execute the repo entrypoint; retain this batch snapshot.
        command[1]=str(ROOT/'scripts/simulate-compact-bank.py')
        with (a.out/f'{name}-{temp}.log').open('w') as log:
            with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True) as process:
                try:code=process.wait(timeout=2400)
                except subprocess.TimeoutExpired:
                    expired=True;os.killpg(process.pid,signal.SIGKILL);code=process.wait()
        result=json.loads((directory/'result.json').read_text()) if (directory/'result.json').exists() else {}
        report=dict(run=str(directory),temperature_C=temp,pattern=name,seconds=time.monotonic()-start,
                    completed=bool(result.get('completed')) and code==0,returncode=code,overall_timeout=expired,
                    capture_readout_pass=result.get('capture_readout_pass'),tracking_pass=result.get('tracking_pass'))
        print(json.dumps(report),flush=True);return report
    results=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(run,job) for job in jobs]
        for future in as_completed(futures):
            results.append(future.result())
            (a.out/'batch.json').write_text(json.dumps(dict(scope=__doc__,expected=8,runs=results),indent=2)+'\n')
    if not all(r['completed'] and r['capture_readout_pass'] and r['tracking_pass'] for r in results):raise SystemExit(1)


if __name__=='__main__':main()
