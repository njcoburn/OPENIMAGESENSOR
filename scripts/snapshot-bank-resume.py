"""Record stopped artifacts before reuse, without claiming historical hashes or accuracy.

The original plan's existing hashes are checked first. Newly recorded hashes
protect subsequent reuse; they cannot retrospectively prove the stopped bytes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();source=a.source.resolve()
    assert not a.out.exists(), 'Never overwrite a resume snapshot'
    plan=ROOT/'build/compact-bank-c64-full-plan-20260927.json'
    for name,digest in json.loads(plan.read_text())['evidence_hashes'].items():
        assert sha(ROOT/name)==digest, name
    stop=ROOT/'build/compact-bank-full-stopped-progress-20260927.json'
    stopped=json.loads(stop.read_text())
    record,=[r for r in stopped['runs'] if ROOT/r['run']==source]
    assert record['phase']=='transient complete'
    result=json.loads((source/'result.json').read_text())
    execution=json.loads((source/'transient/execution.json').read_text())
    assert result['transient']==execution and execution['completed'] and not execution['timed_out']
    assert execution['returncode']==0 and not execution['errors'] and result['phase']=='full'
    assert execution['deck_sha256']==sha(source/'transient/test.spice')
    helper=ROOT/'scripts/compact-bank-reuse-v2.py'
    spec=importlib.util.spec_from_file_location('reuse',helper)
    reuse=importlib.util.module_from_spec(spec);spec.loader.exec_module(reuse)
    files={source/name for name in reuse.ARTIFACTS}|{plan,stop,Path(__file__).resolve()}
    references=[]
    for d in sorted(source.glob('*-reference')):
        path=d/'execution.json'
        if not path.exists():continue
        ex=json.loads(path.read_text())
        if not ex['completed']:continue
        assert ex['returncode']==0 and not ex['timed_out'] and not ex['errors']
        assert ex['deck_sha256']==sha(d/'test.spice')
        references.append(d.name)
        files.update(d/name for name in ['test.spice','execution.json','ngspice.log','op.raw'])
    report=dict(scope=__doc__,recorded_at_utc=datetime.now(timezone.utc).isoformat(),
                source=str(source.relative_to(ROOT)),source_run_completed=result['completed'],
                transient_execution_completed=True,completed_references=references,
                prior_plan_hashes_verified=True,accuracy_qualified=False,
                evidence_hashes={str(f.relative_to(ROOT)):sha(f) for f in sorted(files)})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(snapshot=str(a.out),hashes=len(report['evidence_hashes']),references=len(references))))

if __name__=='__main__':main()
