"""Validate extended timing, immutable extraction, corner isolation and fresh small controls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bank=load('simulate-compact-bank-v5.py');audit=load('report-bank-stack3.py');common=load('bank-process-common.py')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    assert bank.acquisition_timing(12.5)==(14.5e-6,14.51e-6,14.499e-6)
    assert bank.acquisition_timing(12)==(14e-6,14.01e-6,13.999e-6)
    for value in [0,13,15]:
        try:bank.acquisition_timing(value)
        except ValueError:pass
        else:raise AssertionError('Unsafe/unsupported timing accepted')
    for n in [2,64]:
        slots,stop=bank.readout_schedule(n);assert len(slots)==2*n
        for _,_,start in slots:assert start+14.499e-6 < start+14.5e-6 < start+14.51e-6 < start+15e-6 < start+16e-6
    layout=ROOT/'build/compact-bank-c2-stack3-v3-20260930'
    def one(corner,step):
        dest=out/f'{corner}-{step}'
        command=[sys.executable,str(ROOT/'scripts/simulate-compact-bank-v5.py'),'--layout',str(layout),'--out',str(dest),'--lights-pa','240,0','--temperature','125','--step-ns',str(step),'--solver','klu','--mos-corner',corner,'--acquisition-us','12.5','--save-mim-terminals','--timeout','300','--reference-workers','2']
        if step==50:command+=['--transient-only']
        with (out/f'{corner}-{step}.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
        run,detail=audit.audit_run(dest,layout,out/f'audit-{corner}-{step}')
        retained=ROOT/f'build/compact-bank-physical-cycles-20260930/stack3-{corner}-acq12.5-{step}'
        old=json.loads((retained/'candidate-result.json').read_text())
        newdeck=(dest/'transient/test.spice').read_text();olddeck=(retained/'transient/test.spice').read_text()
        def normalized(deck):
            return '\n'.join('.save '+' '.join(sorted(line.split()[1:])) if line.startswith('.save ') else line for line in audit.normalize(deck).splitlines())
        assert normalized(newdeck)==normalized(olddeck)
        delta=max(abs(s['values']['HOLD']-r['values']['v(hold)'])*1e6 for s,r in zip(run['samples'],old['samples']));assert delta<.001
        if step==100:
            for s,r in zip(run['samples'],old['samples']):assert abs(s['total_capture_readout_error_V']*1e6-r['total_error_uV'])<.001
        assert detail['references']==(6 if step==100 else 0)
        print(f'Fresh {corner}/{step} control audited; HOLD delta {delta:.6g} uV',flush=True)
        return dict(corner=corner,step_ns=step,max_hold_difference_uV=delta,references=detail['references'])
    with ThreadPoolExecutor(max_workers=2) as pool:controls=list(pool.map(lambda job:one(*job),[(c,s) for c in ['typical','ss','ff'] for s in [100,50]]))
    typical=(out/'typical-100/transient/test.spice').read_text()
    for corner in ['ss','ff']:
        deck=(out/f'{corner}-100/transient/test.spice').read_text();common.compare_process_only(typical,deck,corner)
    for corrupted in [typical.replace('Vsource RAW 0 3.3','Vsource RAW 0 3.0'),typical.replace('mimcap_typical','mimcap_ff'),typical.replace('.tran 100n','.tran 200n')]:
        try:common.compare_process_only(typical,corrupted,'typical')
        except AssertionError:pass
        else:raise AssertionError('Changed fixture accepted')
    base=dict(columns=64,acquisition_us=12.5,temperature_C=125,lights_pA=[240,0]*32,mos_corner='ss')
    coarse=dict(base,step_ns=100,references_requested=True);fine=dict(base,step_ns=50,references_requested=False)
    audit.validate_pair(coarse,fine,125,'inverse')
    for key,value in [('mos_corner','ff'),('acquisition_us',12),('columns',2)]:
        changed=dict(fine,**{key:value})
        try:audit.validate_pair(coarse,changed,125,'inverse')
        except AssertionError:pass
        else:raise AssertionError('Mismatched pair accepted')
    files=[p for p in out.rglob('*') if p.is_file()]+[ROOT/'scripts'/n for n in ['test-bank-stack3.py','simulate-compact-bank-v5.py','report-bank-stack3.py','bank-process-common.py']]
    report=dict(passed=True,fresh_transients=6,fresh_references=18,controls=controls,source_hashes={str(p.relative_to(ROOT)):audit.sha(p) for p in files})
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
