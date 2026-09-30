"""Audit completed coarse evidence and only the available prefix of timed-out refinements.

Incomplete refined traces never establish a complete case or permit continuation.
"""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import re
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);plan=json.loads(a.plan.read_text())
    audit=load('report-bank-stack3.py');reader=load('diagnose-capture-transient.py');bank=load('simulate-compact-bank-v5.py');common=load('bank-process-common.py')
    for name,digest in plan['evidence_hashes'].items():assert audit.sha(ROOT/name)==digest,name
    layout=ROOT/plan['layout'];meta=json.loads((layout/'verification.json').read_text());cases=[];files={Path(__file__).resolve(),a.plan.resolve(),layout/'verification.json'}
    for case in plan['stages'][0]['cases']:
        coarse=ROOT/case['coarse'];fine=ROOT/case['fine']
        run,detail=audit.audit_run(coarse,layout,out/(case['name']+'-generated'))
        assert run['completed'] and detail['references']==192
        f=json.loads((fine/'result.json').read_text());ex=json.loads((fine/'transient/execution.json').read_text())
        assert not f['completed'] and not ex['completed'] and ex['timed_out'] and ex['errors']==[] and ex['returncode'] is None
        assert f['transient']==ex and not f['references_requested'] and f['step_ns']==50
        assert f['mos_corner']==run['mos_corner']==case['corner'] and f['pdk_provenance']==run['pdk_provenance']
        for field in ['columns','temperature_C','lights_pA','model_sha256','layout_gds_sha256','solver','method','driver_form','acquisition_us','sample_offset_s','stop_s','readout_slots']:assert f[field]==run[field],field
        assert audit.sha(fine/'runner.py')==audit.sha(ROOT/'scripts/simulate-compact-bank-v5.py')
        assert (fine/'.spiceinit').read_bytes()==(coarse/'.spiceinit').read_bytes()
        assert audit.sha(fine/'tile.spice')==run['model_sha256']==audit.sha(layout/'rc-port.spice')
        cdeck=(coarse/'transient/test.spice').read_text();fdeck=(fine/'transient/test.spice').read_text()
        expected=re.sub(r'^\.tran 100n (\S+) 0 100n$',r'.tran 50n \1 0 50n',cdeck,flags=re.M)
        assert expected!=cdeck and audit.normalize(expected)==audit.normalize(fdeck)
        assert ex['deck_sha256']==audit.sha(fine/'transient/test.spice');common.validate_models(fdeck,case['corner'])
        ix,data=reader.trace(fine/'transient/stream.raw');ci,cd=reader.trace(coarse/'transient/stream.raw')
        assert data is not None and np.isfinite(data).all() and data[0,0]==0 and np.all(np.diff(data[:,0])>0)
        assert len(data)==ex['points'] and abs(data[-1,0]-ex['last_complete_trace_time_s'])<1e-15
        assert data[-1,0]<f['stop_s'] and np.max(np.diff(data[:,0]))<=50e-9*1.001 and set(ix)==set(ci)
        at=bank.trace_sampler(ix,data);cat=bank.trace_sampler(ci,cd);rows=[]
        for sample in run['samples']:
            t=sample['time_s']
            if t>data[-1,0]:continue
            c=sample['column'];values={name:at(name,t) for name in sample['values']}
            difference=max((abs(value-values[name])*1e6,name) for name,value in sample['values'].items())
            hold=values['HOLD'];total=(hold-run['capture_references'][c]['values']['HOLD'])*1e6
            rows.append(dict(scan=sample['slot'],column=c,time_s=t,coarse_total_error_uV=sample['total_capture_readout_error_V']*1e6,
                             fine_error_against_coarse_capture_reference_uV=total,max_saved_sample_difference_uV=difference[0],worst_node=difference[1],hold_difference_uV=abs(hold-sample['values']['HOLD'])*1e6))
        events=[]
        for name,t in [('pre_capture',.0014-1e-9),('before_row_off',.001402-1e-9),('after_row_off',.0014025),('after_reset',.001405)]:
            assert t<=data[-1,0]
            delta=max((abs(at(n[2:-1],t)-cat(n[2:-1],t))*1e6,n) for n in ix if n.startswith('v('))
            events.append(dict(event=name,time_s=t,max_all_saved_node_difference_uV=delta[0],worst_node=delta[1]))
        late=[s for s in run['samples'] if s['slot']=='last'];first=[s for s in run['samples'] if s['slot']=='first']
        retention=[dict(column=s['column'],store_change_V=s['values'][f'STORE{s["column"]}']-first[s['column']]['values'][f'STORE{s["column"]}'],total_error_uV=s['total_capture_readout_error_V']*1e6,tracking_error_uV=s['output_tracking_error_V']*1e6,settled_state_change_uV=(s['total_capture_readout_error_V']-s['output_tracking_error_V'])*1e6) for s in late]
        record=dict(corner=case['corner'],coarse_audited=True,references_audited=detail['references'],coarse_total_error_uV=run['max_total_capture_readout_error_V']*1e6,
                    coarse_tracking_error_uV=run['max_output_tracking_error_V']*1e6,coarse_capture_readout_pass=run['capture_readout_pass'],coarse_tracking_pass=run['tracking_pass'],
                    fine_timed_out=True,fine_wall_seconds=ex['seconds'],fine_stop_ms=float(data[-1,0])*1000,required_stop_ms=f['stop_s']*1000,available_refined_samples=len(rows),required_refined_samples=128,
                    missing_samples=[dict(scan=s['slot'],column=s['column']) for s in run['samples'] if s['time_s']>data[-1,0]],
                    max_available_saved_sample_difference_uV=max(r['max_saved_sample_difference_uV'] for r in rows),
                    available_fine_total_error_failures=[r for r in rows if abs(r['fine_error_against_coarse_capture_reference_uV'])>=500],
                    rows=rows,events=events,late_scan_retention=retention,full_pair_audited=False,selected_screen_pass=False,accuracy_qualified=False)
        cases.append(record)
        for directory in [coarse,fine]:files.update(p for p in directory.rglob('*') if p.is_file())
        print(json.dumps({k:record[k] for k in ['corner','coarse_total_error_uV','coarse_tracking_error_uV','available_refined_samples','max_available_saved_sample_difference_uV']}),flush=True)
    files.update(p for p in out.rglob('*') if p.is_file());files.update(ROOT/n for n in plan['evidence_hashes'])
    status=ROOT/plan['output']/'status.json';files.add(status)
    result=dict(reviewed_at_utc=datetime.now(timezone.utc).isoformat(),scope=__doc__,cases=cases,completed_coarse_transients_audited=3,references_audited=576,partial_refined_transients_reviewed=3,
                full_pairs_completed=0,queue_advanced=False,full_bank_accuracy_qualified=False,full_chip_qualified=False,
                limits=['Fine-error estimates use the same coarse capture references as the normal paired audit; the unavailable final samples are not extrapolated.',
                        'All three complete cases still require finished refined transients. No accuracy pass is claimed.',
                        'Late settled-state change includes rail/bias and storage changes; it is not labeled pure storage leakage.'],
                evidence_hashes={str(p.relative_to(ROOT)):audit.sha(p) for p in sorted(files)})
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('Interrupted-batch evidence review complete.',flush=True)
if __name__=='__main__':main()
