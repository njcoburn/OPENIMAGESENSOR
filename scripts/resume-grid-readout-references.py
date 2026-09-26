"""Resume preserved nominal grid references using an audited, wider worker pool."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,required=True)
a=p.parse_args();root=a.runs.resolve()
command=json.loads((root/'27-100-matched-parallel-command.json').read_text())
assert command[command.index('--dc-workers')+1]=='12'
out=Path(command[command.index('--output')+1]);assert not out.exists()
original=json.loads((root/'nominal-reference-restart.json').read_text())['original_command']
expected=original.copy();expected[expected.index('--output')+1]=str(out)
expected[expected.index('--dc-workers')+1]='12'
expected+=['--reuse-dc',str(root/'27-100-matched')]
assert command==expected
shutil.copyfile(__file__,root/'scripts/resume-grid-readout-references.py')
started=time.monotonic();env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
with (root/'27-100-matched-parallel.log').open('w') as f:
    subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/analyze-strip-recovery.py'),
                    '--source',command[command.index('--source')+1],str(out)],
                   env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
r=json.loads((out/'r1c64-rc-port/result.json').read_text())
assert r['completed'] and len(r['samples'])==64
reused=[s['column'] for s in r['samples'] if s['dc_execution'].get('reused_dc_from')]
result={'completed':True,'seconds':time.monotonic()-started,'dc_workers':12,
        'max_output_error_V':r['max_tracking_error_V'],
        'tracking_screen_pass':r['tracking_screen_pass'],'reused_reference_columns':reused,
        'command':command,'original_attempt_preserved':str(root/'27-100-matched')}
(root/'27-100-matched-parallel-status.json').write_text(json.dumps(result,indent=2)+'\n')
manifest=json.loads((root/'manifest.json').read_text())
manifest['selected_matched_runs']={'27':out.name,'125':'125-100-matched'}
manifest['reference_retry']=result
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
