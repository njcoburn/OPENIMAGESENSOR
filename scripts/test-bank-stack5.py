"""Fresh extracted port/far controls, independent raw audits and timing guards.

Twelve transients and 72 fresh references; no model-only geometry substitution.
Run inside the pinned EDA container. Existing output paths are never reused.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bank=load('simulate-compact-bank-v6.py');audit=load('report-bank-stack5.py');common=load('bank-process-common.py')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    assert bank.acquisition_timing(13)==(15e-6,15.01e-6,14.999e-6)
    assert bank.acquisition_timing(12.5)==(14.5e-6,14.51e-6,14.499e-6)
    for value in [0,13.5,15]:
        try:bank.acquisition_timing(value)
        except ValueError:pass
        else:raise AssertionError('Unsafe timing accepted')
    for n in [2,64]:
        for _,_,start in bank.readout_schedule(n)[0]:
            assert start+14.999e-6 < start+15e-6 < start+15.01e-6 < start+15.5e-6 < start+15.51e-6 < start+16e-6
    layout=ROOT/'build/compact-bank-c2-stack5-v1-20260930'
    def one(model,corner,step):
        name=f'{model}-{corner}-{step}';dest=out/name
        command=[sys.executable,str(ROOT/'scripts/simulate-compact-bank-v6.py'),'--layout',str(layout),'--out',str(dest),'--model',model,'--lights-pa','240,0','--temperature','125','--step-ns',str(step),'--solver','klu','--mos-corner',corner,'--acquisition-us','13','--save-mim-terminals','--timeout','600','--reference-workers','2']
        with (out/(name+'.log')).open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
        run,detail=audit.audit_run(dest,layout,out/('audit-'+name))
        assert detail['references']==6 and detail['mim_terminals_saved']
        assert len(detail['private_events'][0]['values'])==8
        print('Fresh raw control audited: '+name,flush=True)
        return (model,corner,step),run,detail
    jobs=[(m,c,s) for m in ['rc-port','rc-far'] for c in ['typical','ss','ff'] for s in [100,50]]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda job:one(*job),jobs))
    runs={key:(run,detail) for key,run,detail in results};cases=[]
    for model in ['rc-port','rc-far']:
        typical=(out/f'{model}-typical-100/transient/test.spice').read_text()
        for corner in ['typical','ss','ff']:
            common.compare_process_only(typical,(out/f'{model}-{corner}-100/transient/test.spice').read_text(),corner)
            coarse,cd=runs[model,corner,100];fine,fd=runs[model,corner,50]
            total=max(r['max_total_capture_readout_error_V']*1e6 for r in [coarse,fine])
            tracking=max(r['max_output_tracking_error_V']*1e6 for r in [coarse,fine])
            sample=max(abs(s['values'][n]-f['values'][n])*1e6 for s,f in zip(coarse['samples'],fine['samples']) for n in s['values'])
            events=max(abs(s['values'][n]-f['values'][n])*1e6 for s,f in zip(cd['private_events'],fd['private_events']) for n in s['values'])
            mim=max(abs(s[k]-f[k])*1e6 for ce,fe in zip(cd['events'],fd['events']) for s,f in zip(ce['columns'],fe['columns']) for k in ['upper_V','ground_V','differential_V','store_V'])
            contrast=all(r['samples'][i+1]['values']['HOLD']>r['samples'][i]['values']['HOLD'] for r in [coarse,fine] for i in [0,2])
            checks=dict(total=total<500,tracking=tracking<500,sample=sample<10,private_events=events<10,mim_events=mim<10,contrast=contrast)
            cases.append(dict(model=model,corner=corner,total_uV=total,tracking_uV=tracking,sample_refinement_uV=sample,private_event_refinement_uV=events,mim_event_refinement_uV=mim,checks=checks,selected_screen_pass=all(checks.values())))
    placement=max(abs(runs['rc-port',c,s][0]['samples'][i]['values'][n]-runs['rc-far',c,s][0]['samples'][i]['values'][n])*1e6 for c in ['typical','ss','ff'] for s in [100,50] for i in range(4) for n in ['HOLD','STORE0','STORE1'])
    base=dict(columns=64,acquisition_us=13,temperature_C=125,lights_pA=[240,0]*32,mos_corner='ss')
    coarse=dict(base,step_ns=100,references_requested=True);fine=dict(base,step_ns=50,references_requested=False)
    audit.validate_pair(coarse,fine,125,'inverse')
    for key,value in [('mos_corner','ff'),('acquisition_us',12.5),('columns',2)]:
        try:audit.validate_pair(coarse,dict(fine,**{key:value}),125,'inverse')
        except AssertionError:pass
        else:raise AssertionError('Mismatched pair accepted')
    for corrupted in [typical.replace('Vsource RAW 0 3.3','Vsource RAW 0 3.0'),typical.replace('mimcap_typical','mimcap_ff'),typical.replace('.tran 100n','.tran 200n')]:
        try:common.compare_process_only(typical,corrupted,'typical')
        except AssertionError:pass
        else:raise AssertionError('Changed fixture accepted')
    files=[p for p in out.rglob('*') if p.is_file()]+[ROOT/'scripts'/n for n in ['test-bank-stack5.py','simulate-compact-bank-v6.py','report-bank-stack5.py','bank-process-common.py']]
    result=dict(passed=all(c['selected_screen_pass'] for c in cases) and placement<10,fresh_transients=12,fresh_references=72,cases=cases,max_port_far_hold_store_difference_uV=placement,full_bank_accuracy_qualified=False,source_hashes={str(p.relative_to(ROOT)):audit.sha(p) for p in files})
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'},indent=2));assert result['passed']
if __name__=='__main__':main()
