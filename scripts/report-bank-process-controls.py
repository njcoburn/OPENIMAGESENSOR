"""Review completed controls; distinguish valid test machinery from electrical passes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    baseline=ROOT/'simulations/compact-bank-64-full-hot.json';old=json.loads(baseline.read_text())
    control=json.loads((source/'retained-hot-audit/result.json').read_text())
    # The already completed full-bank audit is retained; ensure its sources and
    # reviewed baseline have not changed. Its raw files are covered by its manifest.
    for path in ['scripts/report-bank-process.py','scripts/simulate-compact-bank-v4.py','scripts/bank-process-common.py']:
        assert sha(ROOT/path)==control['evidence_hashes'][path]
    keys=['checks','rows','refinement','event_refinement_worst','max_total_error_uV','max_tracking_error_uV','max_refinement_uV','selected_screen_pass']
    assert all(control[k]==old[k] for k in keys)
    auditor=module('audit','report-bank-process.py');layout=ROOT/'build/compact-bank-c2-v1-20260926';results=[]
    for corner in ['ss','ff']:
        coarse,cd=auditor.audit_run(source/f'c2-{corner}-100',layout,out/f'generated-{corner}-100')
        fine,fd=auditor.audit_run(source/f'c2-{corner}-50',layout,out/f'generated-{corner}-50')
        assert cd['references']==6 and fd['references']==0 and cd['samples']==fd['samples']==4
        sample=max(abs(s['values'][n]-f['values'][n])*1e6 for s,f in zip(coarse['samples'],fine['samples']) for n in s['values'])
        event=max(abs(c[k]-f[k])*1e6 for ce,fe in zip(cd['events'],fd['events']) for c,f in zip(ce['columns'],fe['columns']) for k in ['upper_V','ground_V','differential_V','store_V'])
        checks=dict(capture_readout=coarse['capture_readout_pass'],output_tracking=coarse['tracking_pass'],refinement=sample<10,event_refinement=event<10,
                    contrast_order=all(coarse['samples'][i+1]['values']['HOLD']>coarse['samples'][i]['values']['HOLD'] for i in [0,2]))
        rows=[dict(scan=s['slot'],column=s['column'],total_error_uV=s['total_capture_readout_error_V']*1e6,tracking_error_uV=s['output_tracking_error_V']*1e6,store_error_uV=s['storage_capture_error_V']*1e6) for s in coarse['samples']]
        droop=[dict(column=c,first_to_late_store_change_uV=(coarse['samples'][c+2]['values'][f'STORE{c}']-coarse['samples'][c]['values'][f'STORE{c}'])*1e6) for c in [0,1]]
        results.append(dict(mos_corner=corner,independent_audit_completed=True,checks=checks,selected_screen_pass=all(checks.values()),
                            max_total_error_uV=coarse['max_total_capture_readout_error_V']*1e6,max_tracking_error_uV=coarse['max_output_tracking_error_V']*1e6,
                            max_sample_refinement_uV=sample,max_event_refinement_uV=event,rows=rows,storage_drift=droop,references=6,samples_per_transient=4))
    implementation_valid=all(r['independent_audit_completed'] and r['checks']['refinement'] and r['checks']['event_refinement'] for r in results)
    sources=['scripts/'+n for n in module('launch','launch-bank-process.py').SOURCES]+['scripts/report-bank-process-controls.py','simulations/compact-bank-64-full-hot.json']
    artifacts=[p for parent in [source,out] for p in parent.rglob('*') if p.is_file()]
    report=dict(scope=__doc__,exact_reproduction=True,compared_fields=keys,control_implementation_valid=implementation_valid,
                all_small_selected_screens_pass=all(r['selected_screen_pass'] for r in results),small_process_controls=results,
                disposition='Retain FF electrical failure; proceed only to bounded current-layout SS/FF measurement, without any corner qualification claim.',
                inference='FF late-scan STORE drift with small output-tracking error is consistent with storage retention sensitivity; root cause is not established.',
                source_hashes={name:sha(ROOT/name) for name in sources},evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in artifacts},
                full_bank_accuracy_qualified=False,full_chip_qualified=False)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['exact_reproduction','control_implementation_valid','all_small_selected_screens_pass','small_process_controls']},indent=2))

if __name__=='__main__':main()
