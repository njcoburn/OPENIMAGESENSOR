"""Reproduce the retained hot audit and exercise small SS/FF circuits before scale-up."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    baseline_path=ROOT/'simulations/compact-bank-64-full-hot.json';baseline=json.loads(baseline_path.read_text())
    def execute(command,log,timeout=1800):
        with (out/log).open('w') as handle:subprocess.run([sys.executable]+command,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,check=True,timeout=timeout)
    execute(['scripts/report-bank-process.py','--layout',baseline['layout'],'--run',baseline['runs'][0]['run'],
             '--refined',baseline['runs'][1]['run'],'--temperature','125','--pattern','inverse','--mos-corner','typical','--out',str(out/'retained-hot-audit')],'retained-hot-audit.log')
    control=json.loads((out/'retained-hot-audit/result.json').read_text())
    keys=['checks','rows','refinement','event_refinement_worst','max_total_error_uV','max_tracking_error_uV','max_refinement_uV','selected_screen_pass']
    assert all(control[k]==baseline[k] for k in keys), 'Typical control changed'
    print('Full-bank typical hot audit exactly reproduced.',flush=True)
    small_layout=ROOT/'build/compact-bank-c2-v1-20260926'
    def small(corner,step):
        dest=out/f'c2-{corner}-{step}'
        command=['scripts/simulate-compact-bank-v4.py','--layout',str(small_layout),'--out',str(dest),
                 '--mos-corner',corner,'--lights-pa','240,0','--temperature','125','--step-ns',str(step),
                 '--solver','klu','--acquisition-us','12','--timeout','300','--reference-timeout','120','--reference-workers','2','--save-mim-terminals']
        if step==50:command+=['--transient-only']
        execute(command,f'c2-{corner}-{step}.log',timeout=1200)
        return dest
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs={key:pool.submit(small,*key) for key in [(c,s) for c in ['ss','ff'] for s in [100,50]]}
        runs={key:f.result() for key,f in jobs.items()}
    auditor=module('audit','report-bank-process.py');small_results=[]
    for corner in ['ss','ff']:
        coarse,cd=auditor.audit_run(runs[(corner,100)],small_layout,out/f'generated-{corner}-100')
        fine,fd=auditor.audit_run(runs[(corner,50)],small_layout,out/f'generated-{corner}-50')
        assert cd['references']==6 and fd['references']==0 and cd['samples']==fd['samples']==4
        sample=max(abs(s['values'][n]-f['values'][n])*1e6 for s,f in zip(coarse['samples'],fine['samples']) for n in s['values'])
        event=max(abs(c[k]-f[k])*1e6 for ce,fe in zip(cd['events'],fd['events']) for c,f in zip(ce['columns'],fe['columns']) for k in ['upper_V','ground_V','differential_V','store_V'])
        assert sample<10 and event<10 and coarse['capture_readout_pass'] and coarse['tracking_pass']
        small_results.append(dict(mos_corner=corner,references=6,samples_per_transient=4,max_sample_refinement_uV=sample,max_event_refinement_uV=event,max_total_error_uV=coarse['max_total_capture_readout_error_V']*1e6,passed=True))
    sources=['scripts/'+n for n in module('launch','launch-bank-process.py').SOURCES]+['scripts/verify-bank-process-control.py','simulations/compact-bank-64-full-hot.json']
    artifacts=[p for p in out.rglob('*') if p.is_file()]
    result=dict(exact_reproduction=True,compared_fields=keys,typical_baseline=str(baseline_path.relative_to(ROOT)),small_process_controls=small_results,
                source_hashes={name:sha(ROOT/name) for name in sources},evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in artifacts},
                full_bank_accuracy_qualified=False,full_chip_qualified=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(small_results,indent=2))

if __name__=='__main__':main()
