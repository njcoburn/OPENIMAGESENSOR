"""One-command rerun of the fixed, verified two-column physical candidate.

Run inside the pinned EDA container. This does not rebuild a changed pixel.
Refuse existing output paths and preserve all earlier evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tag',required=True);p.add_argument('--plan-only',action='store_true');a=p.parse_args()
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}',a.tag)
    out=ROOT/'build'/('physical-stack3-rerun-'+a.tag)
    commands=[]
    for suffix,screen,review in [('port','screen-bank-physical-stack3.py','review-bank-physical-stack3.py'),('far','screen-bank-physical-stack3-far.py','review-bank-physical-stack3-far.py')]:
        commands += [[sys.executable,str(ROOT/'scripts'/screen),'--out',str(out/suffix)],
                     [sys.executable,str(ROOT/'scripts'/review),'--source',str(out/suffix),'--out',str(out/(suffix+'-review'))]]
    commands += [[sys.executable,str(ROOT/'scripts/compare-physical-stack3-placement.py'),'--port',str(out/'port'),'--far',str(out/'far'),'--out',str(out/'placement.json')]]
    if a.plan_only:print(json.dumps(dict(output=str(out),commands=commands,transients=12,references=72,launches_simulations=False),indent=2));return
    out.mkdir(exist_ok=False)
    layout=ROOT/'build/compact-bank-c2-stack3-v3-20260930'
    files=[layout/n for n in ['bank.gds','verification.json','rc-port.spice','rc-far.spice']]
    files += [ROOT/'scripts'/n for n in ['rerun-physical-stack3.py','screen-bank-physical-stack3.py','screen-bank-physical-stack3-far.py','review-bank-physical-stack3.py','review-bank-physical-stack3-far.py','compare-physical-stack3-placement.py','simulate-compact-bank-v4.py','bank-process-common.py','diagnose-capture-transient.py','probe-bank-readout.py','report-compact-bank-16.py']]
    hashes={str(f.relative_to(ROOT)):sha(f) for f in files}
    state=dict(completed=False,selected_screen_pass=False,commands=commands,completed_stages=0,evidence_dependencies=hashes,full_bank_accuracy_qualified=False)
    def publish():(out/'status.json').write_text(json.dumps(state,indent=2)+'\n')
    publish()
    try:
        for command in commands:
            for name,digest in hashes.items():assert sha(ROOT/name)==digest,name
            with (out/f'stage-{state["completed_stages"]+1}.log').open('w') as log:
                subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            state['completed_stages']+=1;publish();print('Completed stage '+str(state['completed_stages'])+'/5',flush=True)
        state['completed']=True
        state['selected_screen_pass']=all(c['selected_screen_pass'] for name in ['port-review','far-review'] for c in json.loads((out/name/'result.json').read_text())['cases'])
        publish()
    except Exception as exc:
        state['failure']=str(exc);publish();raise
    assert state['selected_screen_pass'],'Measured electrical screen failure; evidence retained'
if __name__=='__main__':main()
