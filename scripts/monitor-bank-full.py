"""Read bounded progress from a live SPICE binary trace; never claim accuracy."""
import argparse
import importlib.util
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bank',ROOT/'scripts/simulate-compact-bank-v2.py');bank=importlib.util.module_from_spec(spec);spec.loader.exec_module(bank)


def progress(directory):
    deck=directory/'transient/test.spice';raw=directory/'transient/stream.raw'
    last=bank.saved_progress(raw)
    slots,stop=bank.readout_schedule(64)
    result=dict(run=str(directory),elapsed_minutes=(time.time()-deck.stat().st_mtime)/60 if deck.exists() else None,
                last_saved_ms=last*1000 if last is not None else None,
                observed_sample_instants=sum(t+13.999e-6<=(last or 0) for _,_,t in slots),expected_sample_instants=128,
                phase='initialization' if last is None else 'exposure/capture' if last<.00141 else 'readout' if last<stop-1e-12 else 'transient complete',
                accuracy_claimed=False)
    report=directory/'result.json'
    if report.exists():
        try:r=json.loads(report.read_text())
        except json.JSONDecodeError:r={}
        if 'reference_progress' in r:result['references']=r['reference_progress']
        result['runner_completed']=r.get('completed',False)
        if r.get('completed'):result['phase']='runner complete; independent audit pending'
        elif r.get('transient',{}).get('timed_out'):result['phase']='transient watchdog expired'
    if raw.exists():result['trace_megabytes']=raw.stat().st_size/1e6
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--append',type=Path)
    a=p.parse_args();report=dict(observed_unix_s=time.time(),runs=[progress(x) for x in a.run]);text=json.dumps(report)
    if a.append:
        with a.append.open('a') as f:f.write(text+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
