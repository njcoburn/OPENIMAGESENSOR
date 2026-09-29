"""Independently audit reused 16-column evidence and compare every prior sample/reference."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/report-bank-full-v2.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    source=ROOT/'build/compact-bank-c16-ground8-nominal-20260927'
    run=ROOT/'build/compact-bank-resume-control-20260928'
    old=json.loads((source/'result.json').read_text())
    new,detail=audit.audit_run(run,ROOT/'build/compact-bank-c16-ground8-20260927',a.out/'generated')
    assert len(new['reference_reuse'])==48 and detail['references']==48 and detail['samples']==32
    keys=['max_output_tracking_error_V','max_total_capture_readout_error_V','tracking_pass','capture_readout_pass','capture_state','storage_reset_window_change_V']
    for key in keys:assert old[key]==new[key],key
    for left,right in zip(old['samples'],new['samples']):
        for key,value in left.items():
            if key=='output_reference':
                assert value['values']==right[key]['values'] and value['execution']==right[key]['execution']
            else:assert value==right[key],key
    for left,right in zip(old['capture_references'],new['capture_references']):
        assert left['values']==right['values'] and left['execution']==right['execution']
    paths={f for f in run.rglob('*') if f.is_file()}
    paths.update(ROOT/'scripts'/name for name in ['simulate-compact-bank-v3.py','compact-bank-reuse-v2.py',
                 'report-bank-full-v2.py','verify-bank-resume-control.py','test-bank-resume.py','test-bank-resume-audit.py'])
    result=dict(scope=__doc__,passed=True,samples=32,reused_references=48,
                maximum_sample_and_reference_difference_V=0,independent_audit=detail,
                full_bank_accuracy_qualified=False,full_chip_qualified=False,
                evidence_hashes={str(f.relative_to(ROOT)):audit.sha(f) for f in sorted(paths)})
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['evidence_hashes','independent_audit']},indent=2))

if __name__=='__main__':main()
