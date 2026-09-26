"""Extend supervision without restarting a progressing one-case power run.

Only the Python timeout supervisor is paused. ngspice continues unchanged.
An independent bound terminates the child if needed and always resumes its
original supervisor, which reaps it and records the ordinary result.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import signal
import time

p=argparse.ArgumentParser()
p.add_argument('--run-root',type=Path,required=True)
p.add_argument('--original-timeout',type=float,required=True)
p.add_argument('--additional-seconds',type=float,default=1200)
a=p.parse_args()
root=a.run_root.resolve()
assert root.name.startswith('row-power-') and root.is_dir()
assert a.additional_seconds>0
parents=[];children=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        args=[x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
        cwd=(proc/'cwd').resolve()
        if len(args)>1 and Path(args[0]).name=='python3' and Path(args[1]).name=='diagnose-row-power.py' and '--output' in args:
            if (cwd/args[args.index('--output')+1]).resolve()==root:
                parents.append(int(proc.name))
        if args and Path(args[0]).name=='ngspice' and cwd.parent==root:
            children.append(int(proc.name))
    except (OSError,UnicodeDecodeError):
        continue
assert len(parents)==len(children)==1,(parents,children)
parent,child=parents[0],children[0]
file=root/'watchdog-extension.json'
assert not file.exists(), 'Preserve the earlier supervision record'
shutil.copyfile(__file__,root/'watchdog-runner.py')
note={'reason':'Extend wall-clock supervision; no change to circuit, simulator state, integration history or tolerances.',
      'original_timeout_s':a.original_timeout,'additional_supervision_limit_s':a.additional_seconds,
      'parent_pid':parent,'ngspice_pid':child,'start_epoch':time.time(),'external_timeout':False}
file.write_text(json.dumps(note,indent=2)+'\n')
os.kill(parent,signal.SIGSTOP)
try:
    deadline=time.monotonic()+a.additional_seconds
    while True:
        try:
            state=(Path('/proc')/str(child)/'stat').read_text().split(') ',1)[1].split()[0]
        except FileNotFoundError:
            break
        if state=='Z':
            break
        if time.monotonic()>deadline:
            os.kill(child,signal.SIGTERM)
            note['external_timeout']=True
            break
        time.sleep(.5)
finally:
    os.kill(parent,signal.SIGCONT)
    note.update(supervisor_resumed=True,end_epoch=time.time())
    file.write_text(json.dumps(note,indent=2)+'\n')
    print(json.dumps(note),flush=True)
