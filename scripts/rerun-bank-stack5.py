"""One-command replay of controls and the gated queue for this fixed physical candidate.

Run on the host; Docker is required. A changed pixel/layout needs a new verified
physical source and a versioned profile first. --plan-only launches nothing.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tag',required=True);p.add_argument('--plan-only',action='store_true');a=p.parse_args()
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,40}',a.tag)
    control=f'build/stack5-controls-{a.tag}';guards=f'build/stack5-guards-{a.tag}'
    commands=[['bash','scripts/run-tools.sh','python3','scripts/test-bank-stack5.py','--out',control],
              ['bash','scripts/run-tools.sh','python3','scripts/test-bank-stack5-continuation.py','--out',guards],
              [sys.executable,'scripts/launch-bank-stack5.py','--tag',a.tag,'--controls',control+'/result.json','--continuation-tests',guards+'/result.json']]
    if a.plan_only:
        print(json.dumps(dict(scope=__doc__,commands=commands,control_transients=12,control_references=72,queued_transients=36,queued_references=3456,launches_simulations=False),indent=2));return
    for path in [control,guards,f'build/stack5-sequence-{a.tag}',f'build/stack5-sequence-plan-{a.tag}.json']:assert not (ROOT/path).exists(),path
    active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
    assert not any(n.startswith(('ois-stack3-sequence-','ois-stack5-sequence-')) for n in active),'Review the active sequence first'
    for command in commands:subprocess.run(command,cwd=ROOT,check=True)
    print('Detached verification started; status: build/stack5-sequence-'+a.tag+'/status.json')
if __name__=='__main__':main()
