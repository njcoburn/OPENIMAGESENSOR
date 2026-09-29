"""Audit complete-bank accuracy and refinement from retained binary evidence.

A selected screen is distinct from full pattern/corner or manufacturing
qualification. The refined transient does not acquire its own DC references.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def normalize(deck):
    return re.sub(r'^\.include .*/tile\.spice$', '.include CANONICAL/tile.spice',deck,flags=re.M)


def audit_run(directory,layout,generated,result_override=None):
    probe=module('probe','probe-bank-readout.py');reader=module('reader','diagnose-capture-transient.py')
    bank=module('bank','simulate-compact-bank-v2.py');dc=module('dc','report-compact-bank-16.py')
    r=json.loads((directory/'result.json').read_text()) if result_override is None else result_override
    meta=json.loads((layout/'verification.json').read_text());nc=meta['columns']
    assert r['completed'] and r['phase']=='full' and r['columns']==nc
    assert r['solver']=='klu' and r['method']=='trap' and r['driver_form']=='current'
    assert r['model']=='rc-port' and r.get('acquisition_us',10) in [10,12]
    assert r['temperature_C'] in [27,125] and r['step_ns'] in [50,100]
    assert r['layout_gds_sha256']==meta['gds_sha256']==sha(layout/'bank.gds')
    assert r['model_sha256']==meta['hashes']['rc-port.spice']==sha(layout/'rc-port.spice')==sha(directory/'tile.spice')
    assert meta['magic_drc_errors']==meta['klayout_main_drc_errors']==0 and meta['direct_and_resistor_collapsed_lvs']
    deck=(directory/'transient/test.spice').read_text()
    acq=r.get('acquisition_us',10);offset=11.999e-6 if acq==10 else 13.999e-6
    assert r.get('sample_offset_s',offset)==offset
    if 'acquisition_us' in r:
        assert sha(directory/'runner.py')==sha(ROOT/'scripts/simulate-compact-bank-v2.py')
        assert not r['full_bank_accuracy_qualified'] and not r['full_chip_qualified']
    model=(directory/'tile.spice').read_text()
    plates=[x.split()[1:3] for x in model.splitlines() if x.startswith('X') and len(x.split())>3 and x.split()[3].startswith('cap_mim_')]
    assert len(plates)==8*nc
    def node(name):return '0' if name=='GND' else name if name in meta['ports'] else 'xtile.'+name
    plate_nodes={node(n).lower() for plate in plates for n in plate if node(n)!='0'}
    save,=[x for x in deck.splitlines() if x.startswith('.save ')]
    saved={x[2:-1] for x in save.split()[1:]};has_mim=plate_nodes<=saved
    argv=['v2','--layout',str(layout),'--out',str(generated),'--lights-pa',','.join(map(str,r['lights_pA'])),
          '--temperature',str(r['temperature_C']),'--step-ns',str(r['step_ns']),'--solver','klu',
          '--acquisition-us',str(acq),'--deck-only','--transient-only']
    if has_mim:argv+=['--save-mim-terminals']
    with patch.object(sys,'argv',argv):bank.main()
    assert normalize(deck)==normalize((generated/'transient/test.spice').read_text()), 'Unexpected circuit/control/deck change'
    assert (directory/'.spiceinit').read_bytes()==(generated/'.spiceinit').read_bytes()
    ex=r['transient'];assert ex==json.loads((directory/'transient/execution.json').read_text())
    assert ex['completed'] and ex['returncode']==0 and not ex['timed_out'] and not ex['errors']
    assert ex['deck_sha256']==sha(directory/'transient/test.spice')
    ix,data=reader.trace(directory/'transient/stream.raw')
    assert data is not None and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    slots,stop=bank.readout_schedule(nc)
    assert data[0,0]==0 and abs(data[-1,0]-stop)<1e-12 and len(data)==ex['points']
    assert np.max(np.diff(data[:,0]))<=r['step_ns']*1.001e-9
    assert r['stop_s']==stop and len(r['samples'])==2*nc
    assert r['readout_slots']==[dict(slot=scan,column=c,start_s=t) for scan,c,t in slots]
    at=bank.trace_sampler(ix,data);captured=.0014-1e-9
    capture_nodes={'VDD'}|{f'{n}{c}' for c in range(nc) for n in ['COL','STORE']}|{node(v) for role in meta['pixel_roles'].values() for k,v in role.items() if k in ['sense','anode']}
    assert set(r['capture_state'])==capture_nodes
    for n,v in r['capture_state'].items():assert at(n,captured)==v
    for sample,(scan,c,start) in zip(r['samples'],slots):
        t=start+offset;v=sample['values']
        assert (sample['slot'],sample['column'],sample['time_s'])==(scan,c,t)
        assert {n.lower() for n in v}==saved
        for n,value in v.items():assert at(n,t)==value,(scan,c,n)
        assert v['ACQ']>3 and v['RSTADC']<.01 and v['SC']<.01 and v['SCB']>3 and v['ROW0']<.01 and v['RST0']>3
        assert v[f'SEL{c}']>3 and v[f'SELB{c}']<.01
        assert all(v[f'SEL{i}']<.01 and v[f'SELB{i}']>3 for i in range(nc) if i!=c)
    assert len(r['storage_reset_window_change_V'])==nc
    for c,change in enumerate(r['storage_reset_window_change_V']):assert change==at(f'STORE{c}',.001405)-at(f'STORE{c}',.0014025)
    reference_count=0
    def reference(name,record,t,c,stores):
        nonlocal reference_count
        d=directory/name;execution=record['execution']
        assert execution==json.loads((d/'execution.json').read_text())
        assert execution['completed'] and execution['returncode']==0 and not execution['timed_out'] and not execution['errors']
        assert execution['deck_sha256']==sha(d/'test.spice')
        assert (d/'test.spice').read_text()==probe.reference_deck(deck,meta,at,t,c,stores)
        values=dc.dc_values(d/'op.raw')
        expected={'BUF','ADCIN','HOLD','VDD'}|{f'{n}{c}' for c in range(nc) for n in ['COL','STORE']}
        assert set(record['values'])==expected
        for n,v in record['values'].items():assert values[f'v({n.lower()})']==v
        assert abs(values['v(adcin)']-values['v(hold)'])<1e-8
        reference_count+=1
    if r['references_requested']:
        assert r['reference_progress']==dict(completed=3*nc,expected=3*nc) and len(r['capture_references'])==nc
        for c,ref in enumerate(r['capture_references']):reference(f'capture{c}-reference',ref,captured,c,False)
        for s in r['samples']:
            c=s['column'];reference(f'{s["slot"]}{c}-output-reference',s['output_reference'],s['time_s'],c,True)
            v=s['values'];capture=r['capture_references'][c]['values'];output=s['output_reference']['values']
            assert s['total_capture_readout_error_V']==v['HOLD']-capture['HOLD']
            assert s['output_tracking_error_V']==v['HOLD']-output['HOLD']
            assert s['storage_capture_error_V']==v[f'STORE{c}']-capture[f'STORE{c}']
        for key,samplekey,flag in [('max_total_capture_readout_error_V','total_capture_readout_error_V','capture_readout_pass'),('max_output_tracking_error_V','output_tracking_error_V','tracking_pass')]:
            worst=max(abs(s[samplekey]) for s in r['samples']);assert r[key]==worst and r[flag]==(worst<500e-6)
        assert reference_count==3*nc and len(list(directory.glob('*-reference')))==3*nc
    else:
        assert not list(directory.glob('*-reference'))
        assert 'capture_readout_pass' not in r and 'tracking_pass' not in r
    # Ground events are measurements, not ADC accuracy criteria.
    events=[]
    if has_mim:
        for label,t in [('pre_capture',captured),('before_row_off',.001402-1e-9),('after_row_off',.0014025),('after_reset',.001405)]:
            grounds=[at(node(pair[1]),t) for pair in plates]
            columns=[]
            for c in range(nc):
                local=[pair for pair in plates if re.fullmatch(f'STORE{c}(?:[.].*)?',pair[0])]
                assert len(local)==8
                upper=sum(at(node(pair[0]),t) for pair in local)/8
                lower=sum(at(node(pair[1]),t) for pair in local)/8
                columns.append(dict(column=c,upper_V=upper,ground_V=lower,differential_V=upper-lower,store_V=at(f'STORE{c}',t)))
            events.append(dict(event=label,time_s=t,max_mim_ground_V=max(grounds),min_mim_ground_V=min(grounds),VDD_V=at('VDD',t),BIAS_V=at('BIAS',t),PREF_V=at('PREF',t),columns=columns))
    return r,dict(run=str(directory.relative_to(ROOT)),columns=nc,references=reference_count,samples=len(r['samples']),transient_seconds=ex['seconds'],mim_terminals_saved=has_mim,events=events)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,default=ROOT/'build/compact-bank-c64-ground-grid-20260927')
    p.add_argument('--run',type=Path,required=True);p.add_argument('--refined',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--temperature',type=int,choices=[27,125],default=27)
    p.add_argument('--pattern',choices=['alternating','inverse'],default='alternating');a=p.parse_args()
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);a.layout=a.layout.resolve()
    meta=json.loads((a.layout/'verification.json').read_text())
    assert meta['ground_return_grid'] and (meta['mos'],meta['mim'],meta['diodes'])==(642,512,64)
    plan_path=ROOT/'build/compact-bank-c64-full-plan-20260927.json'
    plan=json.loads(plan_path.read_text())
    for name,digest in plan['evidence_hashes'].items():assert sha(ROOT/name)==digest,name
    geometry_path=ROOT/'build/compact-bank-c64-ground-grid-geometry-20260927/result.json'
    geometry=json.loads(geometry_path.read_text())
    assert geometry['only_recorded_ground_additions'] and geometry['reference_identical']
    for name,digest in geometry['evidence_hashes'].items():assert sha(ROOT/name)==digest,name

    mainrun,detail=audit_run(a.run.resolve(),a.layout,a.out/'generated-main')
    fine,finedetail=audit_run(a.refined.resolve(),a.layout,a.out/'generated-fine')
    assert mainrun['columns']==fine['columns']==64 and mainrun['acquisition_us']==fine['acquisition_us']==12
    assert mainrun['temperature_C']==fine['temperature_C']==a.temperature
    lights=([0,240] if a.pattern=='alternating' else [240,0])*32
    assert mainrun['lights_pA']==fine['lights_pA']==lights
    assert mainrun['step_ns']==100 and fine['step_ns']==50 and detail['references']==192 and finedetail['references']==0
    assert detail['mim_terminals_saved'] and finedetail['mim_terminals_saved']
    differences=[];rows=[]
    for s,f in zip(mainrun['samples'],fine['samples']):
        assert (s['slot'],s['column'],s['time_s'])==(f['slot'],f['column'],f['time_s']) and s['values'].keys()==f['values'].keys()
        ds=[(abs(v-f['values'][n])*1e6,n) for n,v in s['values'].items()]
        val,node=max(ds);differences.append(dict(scan=s['slot'],column=s['column'],max_uV=val,node=node,hold_uV=abs(s['values']['HOLD']-f['values']['HOLD'])*1e6))
        rows.append(dict(scan=s['slot'],column=s['column'],time_s=s['time_s'],hold_V=s['values']['HOLD'],total_error_uV=s['total_capture_readout_error_V']*1e6,tracking_error_uV=s['output_tracking_error_V']*1e6,hold_refinement_uV=differences[-1]['hold_uV']))
    event_differences=[]
    for coarse_event,fine_event in zip(detail['events'],finedetail['events']):
        assert coarse_event['event']==fine_event['event']
        for c,f in zip(coarse_event['columns'],fine_event['columns']):
            for key in ['upper_V','ground_V','differential_V','store_V']:
                event_differences.append(dict(event=coarse_event['event'],column=c['column'],quantity=key,difference_uV=abs(c[key]-f[key])*1e6))
    event_worst=max(event_differences,key=lambda x:x['difference_uV'])
    checks=dict(capture_readout=mainrun['capture_readout_pass'],output_tracking=mainrun['tracking_pass'],refinement=max(x['max_uV'] for x in differences)<10,
                event_refinement=event_worst['difference_uV']<10,
                contrast_order=all(s['values']['HOLD']>mainrun['samples'][i^1]['values']['HOLD'] for i,s in enumerate(mainrun['samples']) if lights[s['column']]==0))
    files={Path(__file__).resolve(),ROOT/'scripts/simulate-compact-bank-v2.py',ROOT/'scripts/test-bank-v2-timing.py',ROOT/'scripts/render-bank-full.py',ROOT/'scripts/finish-bank-full.py',ROOT/'scripts/monitor-bank-full.py',geometry_path,ROOT/'scripts/test-bank-full-audit.py',ROOT/'scripts/probe-bank-readout.py',ROOT/'scripts/diagnose-capture-transient.py',ROOT/'scripts/report-compact-bank-16.py',ROOT/'scripts/run-tools.sh',a.layout/'verification.json',a.layout/'bank.gds',a.layout/'rc-port.spice',ROOT/'build/compact-bank-c64-full-plan-20260927.json'}
    for directory in [a.run,a.refined,a.out,ROOT/'build/compact-bank-full-audit-tests-20260927',ROOT/'build/compact-bank-v2-deck-regression-20260927']:
        files.update(x.resolve() for x in directory.rglob('*') if x.is_file())
    result=dict(scope=__doc__,layout=str(a.layout.relative_to(ROOT)),temperature_C=a.temperature,pattern=a.pattern,acquisition_us=12,runs=[detail,finedetail],rows=rows,refinement=differences,event_refinement_worst=event_worst,checks=checks,selected_screen_pass=all(checks.values()),
                full_bank_readout_completed=True,full_bank_accuracy_qualified=False,full_chip_qualified=False,
                max_total_error_uV=max(abs(s['total_error_uV']) for s in rows),max_tracking_error_uV=max(abs(s['tracking_error_uV']) for s in rows),max_refinement_uV=max(x['max_uV'] for x in differences),
                limits=[f'{a.temperature} C, typical process, nominal supply/wire, {a.pattern} pattern only','50 ns transient has no separate DC references; refinement compares all saved voltages at all 128 output instants','Behavioral drivers, external bias resistors and ADC fixture; one capture and two scans','Remaining temperature/pattern/process/wire/supply/placement coverage and local supply/bias qualification remain open','Real drivers, repeated rows, exact 64x64 chip and provider manufacturing checks remain open'],
                evidence_hashes={str(f.relative_to(ROOT)):sha(f) for f in sorted(files)})
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['checks','max_total_error_uV','max_tracking_error_uV','max_refinement_uV','selected_screen_pass']},indent=2))
    # A measured failure is a completed audit; never hide it by omitting a report.


if __name__=='__main__':main()
