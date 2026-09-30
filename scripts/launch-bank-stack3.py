"""Launch the authorized gated physical-bank sequence in a detached pinned container."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
IMAGE='hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a'
LAYOUT='build/compact-bank-c64-stack3-grid-20260930'
SOURCES=['simulate-compact-bank-v5.py','report-bank-stack3.py','bank-process-common.py','probe-bank-readout.py','diagnose-capture-transient.py','report-compact-bank-16.py','continue-bank-stack3.py','render-bank-stack3-progress.py','launch-bank-stack3.py','test-bank-stack3.py','test-bank-stack3-continuation.py','audit-stack3-full-layout.py','update-overview-sections.py','update-verification-journal.py']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def build_plan(tag):
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,40}',tag)
    specs=[('hot-primary',[(c,125,'inverse') for c in ['typical','ss','ff']]),('hot-mixed',[(c,125,'inverse') for c in ['fs','sf']]),('room-primary',[(c,27,'inverse') for c in ['typical','ss','ff']]),('room-mixed',[(c,27,'inverse') for c in ['fs','sf']])]
    specs += [('typical-'+pattern,[('typical',t,pattern) for t in [27,125]]) for pattern in ['alternating','dark','middle','bright']]
    stages=[]
    for stage_name,items in specs:
        stage=dict(name=stage_name,cases=[],runs=[])
        for corner,temp,pattern in items:
            name=f'{corner}-{pattern}{temp}';pair=[];names=[]
            lights=([240,0]*32 if pattern=='inverse' else [0,240]*32 if pattern=='alternating' else [dict(dark=0,middle=80,bright=240)[pattern]]*64)
            for step in [100,50]:
                path=f'build/stack3-{name}-{step}-{tag}';run_name=f'{name}-{step}';pair.append(path);names.append(run_name)
                command=['python3','scripts/simulate-compact-bank-v5.py','--layout',LAYOUT,'--out',path,'--mos-corner',corner,'--lights-pa',','.join(map(str,lights)),'--temperature',str(temp),'--step-ns',str(step),'--solver','klu','--acquisition-us','12.5','--timeout','14400','--reference-timeout','1800','--reference-workers','2','--save-mim-terminals']
                if step==50:command+=['--transient-only']
                stage['runs'].append(dict(name=run_name,path=path,command=command,exit_record=f'build/stack3-sequence-{tag}/exits/{run_name}.json'))
            stage['cases'].append(dict(name=name,corner=corner,temperature=temp,pattern=pattern,coarse=pair[0],fine=pair[1],run_names=names,report=f'simulations/stack3-{name}-{tag}.json'))
        stages.append(stage)
    return dict(created_at_utc=datetime.now(timezone.utc).isoformat(),scope='Gated candidate sequence: all five MOS corners at 125/27 C inverse, then remaining typical-process patterns. Diode/MIM typical; nominal supply/wire; no full-chip claim.',layout=LAYOUT,image=IMAGE,container='ois-stack3-sequence-'+tag,output='build/stack3-sequence-'+tag,stages=stages,job_timeout_seconds=25200,sequence_timeout_seconds=129600,minimum_free_bytes=80*1024**3,planned_transients=36,planned_references=3456)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tag',required=True);p.add_argument('--controls',type=Path,required=True);p.add_argument('--prepare-only',action='store_true');p.add_argument('--continuation-tests',type=Path,required=True);a=p.parse_args();plan=build_plan(a.tag)
    gates=json.loads(a.continuation_tests.read_text());assert gates['passed'] and gates['full_bank_decks_checked']==10
    for name,digest in gates['source_hashes'].items():assert sha(ROOT/name)==digest,name
    controls=json.loads(a.controls.read_text());assert controls['passed'] and controls['fresh_transients']==6
    for name,digest in controls['source_hashes'].items():assert sha(ROOT/name)==digest,name
    layout=ROOT/LAYOUT;physical=json.loads((layout/'physical-audit.json').read_text());assert physical['physical_checks_pass']
    for name,digest in physical['evidence_hashes'].items():assert sha(ROOT/name)==digest,name
    for stage in plan['stages']:
        for run in stage['runs']:assert not (ROOT/run['path']).exists()
        for case in stage['cases']:assert not (ROOT/case['report']).exists()
    assert not (ROOT/plan['output']).exists()
    files=[a.controls.resolve(),a.continuation_tests.resolve(),layout/'physical-audit.json',layout/'verification.json',layout/'bank.gds',layout/'rc-port.spice']+[ROOT/'scripts'/n for n in SOURCES]
    plan['evidence_hashes']={str(p.relative_to(ROOT)):sha(p) for p in files}
    dest=ROOT/f'build/stack3-sequence-plan-{a.tag}.json';assert not dest.exists();dest.write_text(json.dumps(plan,indent=2)+'\n')
    if a.prepare_only:print(dest);return
    names=subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines();assert plan['container'] not in names
    command=['docker','run','-d','--name',plan['container'],'--user',f'{os.getuid()}:{os.getgid()}','-v',f'{ROOT}:/foss/designs','-w','/foss/designs','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','PDK=gf180mcuD','-e','PDK_ROOT=/foss/pdks','-e','PDKPATH=/foss/pdks/gf180mcuD','--entrypoint','/bin/bash',IMAGE,'-lc','exec "$@"','bash','python3','scripts/continue-bank-stack3.py','--plan',str(dest.relative_to(ROOT))]
    cid=subprocess.check_output(command,text=True).strip()
    record=dict(container=plan['container'],container_id=cid,plan=str(dest.relative_to(ROOT)),status=plan['output']+'/status.json',started_at_utc=datetime.now(timezone.utc).isoformat())
    (ROOT/f'simulations/stack3-sequence-start-{a.tag}.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
