"""Audit selected bank MOS-process cases with matching transient/reference models.

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
    bank=module('bank','simulate-compact-bank-v6.py');dc=module('dc','report-compact-bank-16.py')
    r=json.loads((directory/'result.json').read_text()) if result_override is None else result_override
    meta=json.loads((layout/'verification.json').read_text());nc=meta['columns']
    process=module('process','bank-process-common.py')
    corner=r.get('mos_corner','typical')
    process.validate_models((directory/'transient/test.spice').read_text(),corner)
    if 'mos_corner' in r:
        assert r['diode_corner']==r['mim_corner']=='typical'
        assert r['pdk_provenance']==process.pdk_provenance(bank.PDK)
        assert r['pdk_provenance']==json.loads((directory/'pdk-provenance.json').read_text())
        assert sha(directory/'process-helper.py')==sha(ROOT/'scripts/bank-process-common.py')
    else:
        assert corner=='typical', 'Legacy evidence is typical only'
    assert r['completed'] and r['phase']=='full' and r['columns']==nc
    assert r['solver']=='klu' and r['method']=='trap' and r['driver_form']=='current'
    assert r['model'] in ['rc-port','rc-far'] and r.get('acquisition_us',10) in [10,12,12.5,13]
    assert r['temperature_C'] in [27,125] and r['step_ns'] in [50,100]
    assert r['layout_gds_sha256']==meta['gds_sha256']==sha(layout/'bank.gds')
    assert r['model_sha256']==meta['hashes'][r['model']+'.spice']==sha(layout/(r['model']+'.spice'))==sha(directory/'tile.spice')
    assert meta['magic_drc_errors']==meta['klayout_main_drc_errors']==0 and meta['direct_and_resistor_collapsed_lvs']
    deck=(directory/'transient/test.spice').read_text()
    acq=r.get('acquisition_us',10);offset={10:11.999e-6,12:13.999e-6,12.5:14.499e-6,13:14.999e-6}[acq]
    assert r.get('sample_offset_s',offset)==offset
    if 'acquisition_us' in r:
        assert sha(directory/'runner.py') in {sha(ROOT/'scripts'/name) for name in (['simulate-compact-bank-v6.py'] if 'mos_corner' in r else ['simulate-compact-bank-v2.py','simulate-compact-bank-v3.py'])}
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
          '--acquisition-us',str(acq),'--model',r['model'],'--mos-corner',corner,'--deck-only','--transient-only']
    if has_mim:argv+=['--save-mim-terminals']
    with patch.object(sys,'argv',argv):bank.main()
    assert normalize(deck)==normalize((generated/'transient/test.spice').read_text()), 'Unexpected circuit/control/deck change'
    assert (directory/'.spiceinit').read_bytes()==(generated/'.spiceinit').read_bytes()
    ex=r['transient'];assert ex==json.loads((directory/'transient/execution.json').read_text())
    assert ex['completed'] and ex['returncode']==0 and not ex['timed_out'] and not ex['errors']
    assert ex['deck_sha256']==sha(directory/'transient/test.spice')
    if 'transient_reuse' in r:
        reuse=r['transient_reuse'];manifest=ROOT/reuse['evidence_manifest']
        assert sha(manifest)==reuse['evidence_manifest_sha256']
        hashes=json.loads(manifest.read_text())['evidence_hashes']
        source=ROOT/reuse['source_directory']
        for name,digest in reuse['source_hashes'].items():
            assert sha(source/name)==digest==hashes[str((source/name).relative_to(ROOT))]
            if name.startswith('transient/'):assert sha(directory/name)==digest
        for name,artifacts in r.get('reference_reuse',{}).items():
            for filename,digest in artifacts.items():
                assert sha(directory/name/filename)==sha(source/name/filename)==digest
                assert hashes[str((source/name/filename).relative_to(ROOT))]==digest
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
        process.validate_models((d/'test.spice').read_text(),corner)
        assert normalize((d/'test.spice').read_text())==normalize(probe.reference_deck(deck,meta,at,t,c,stores))
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
    private_events=[dict(event=label,time_s=t,values={node(n['extracted_node']):at(node(n['extracted_node']),t) for path in meta.get('stack_paths',[]) for n in path['private_nodes']}) for label,t in [('pre_capture',captured),('before_row_off',.001402-1e-9),('after_row_off',.0014025),('after_reset',.001405)]]
    return r,dict(private_events=private_events,run=str(directory.relative_to(ROOT)),columns=nc,references=reference_count,samples=len(r['samples']),transient_seconds=ex['seconds'],mim_terminals_saved=has_mim,events=events)



PATTERNS = ('alternating', 'inverse', 'dark', 'middle', 'bright')


def pattern_lights(pattern, columns=64):
    assert pattern in PATTERNS, 'Unknown illumination pattern'
    if pattern in ('alternating', 'inverse'):
        assert columns % 2 == 0
        return ([0, 240] if pattern == 'alternating' else [240, 0]) * (columns // 2)
    return [{'dark': 0, 'middle': 80, 'bright': 240}[pattern]] * columns


def validate_pair(coarse, fine, temperature, pattern):
    assert coarse.get('mos_corner','typical') == fine.get('mos_corner','typical'), 'Process corners differ'
    assert coarse['columns'] == fine['columns'] == 64
    assert coarse.get('model','rc-port') == fine.get('model','rc-port') == 'rc-port'
    assert coarse['acquisition_us'] == fine['acquisition_us'] == 13
    assert coarse['temperature_C'] == fine['temperature_C'] == temperature
    lights = pattern_lights(pattern)
    assert coarse['lights_pA'] == fine['lights_pA'] == lights, 'Illumination does not match the declared pattern'
    assert coarse['step_ns'] == 100 and fine['step_ns'] == 50
    assert coarse['references_requested'] and not fine['references_requested']
    return lights


def screen_checks(mainrun, differences, event_worst, pattern):
    lights = pattern_lights(pattern)
    assert mainrun['lights_pA'] == lights
    checks = dict(capture_readout=mainrun['capture_readout_pass'],
                  output_tracking=mainrun['tracking_pass'],
                  refinement=max(x['max_uV'] for x in differences) < 10,
                  event_refinement=event_worst['difference_uV'] < 10)
    # Uniform scenes have no bright/dark neighbors. Do not manufacture a
    # contrast pass from an empty set or compare nominally equal columns.
    if pattern in ('alternating', 'inverse'):
        checks['contrast_order'] = all(s['values']['HOLD'] > mainrun['samples'][i ^ 1]['values']['HOLD']
                                      for i, s in enumerate(mainrun['samples']) if lights[s['column']] == 0)
    return checks


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,default=ROOT/'build/compact-bank-c64-stack5-grid-20260930')
    p.add_argument('--run',type=Path,required=True);p.add_argument('--refined',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--temperature',type=int,choices=[27,125],default=27)
    p.add_argument('--pattern',choices=PATTERNS,default='alternating')
    p.add_argument('--mos-corner',choices=['typical','ss','ff','fs','sf'],required=True);a=p.parse_args()
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);a.layout=a.layout.resolve()
    meta=json.loads((a.layout/'verification.json').read_text())
    assert meta['ground_return_grid'] and (meta['mos'],meta['mim'],meta['diodes'])==(898,512,64)
    assert meta['capture_series_devices']==5 and len(meta['stack_paths'])==64
    geometry_path=a.layout/'physical-audit.json'
    geometry=json.loads(geometry_path.read_text())
    assert geometry['physical_checks_pass'] and geometry['columns']==64
    for name,digest in geometry['evidence_hashes'].items():assert sha(ROOT/name)==digest,name

    mainrun,detail=audit_run(a.run.resolve(),a.layout,a.out/'generated-main')
    fine,finedetail=audit_run(a.refined.resolve(),a.layout,a.out/'generated-fine')
    lights=validate_pair(mainrun,fine,a.temperature,a.pattern)
    assert mainrun.get('mos_corner','typical')==fine.get('mos_corner','typical')==a.mos_corner
    process=module('process','bank-process-common.py')
    provenance=process.pdk_provenance(Path('/foss/pdks/gf180mcuD/libs.tech/ngspice'))
    assert detail['references']==192 and finedetail['references']==0
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
    for left,right in zip(detail['private_events'],finedetail['private_events']):
        assert left['event']==right['event'] and left['values'].keys()==right['values'].keys()
        for name,value in left['values'].items():
            event_differences.append(dict(event=left['event'],column=None,quantity=name,difference_uV=abs(value-right['values'][name])*1e6))
    event_worst=max(event_differences,key=lambda x:x['difference_uV'])
    checks=screen_checks(mainrun,differences,event_worst,a.pattern)
    fine_total=max(abs(s['values']['HOLD']-mainrun['capture_references'][s['column']]['values']['HOLD'])*1e6 for s in fine['samples'])
    checks['fine_total_against_coarse_capture_references']=fine_total<500
    files={Path(__file__).resolve(),geometry_path,a.layout/'verification.json',a.layout/'bank.gds',a.layout/'rc-port.spice'}
    files.update(ROOT/'scripts'/name for name in ['simulate-compact-bank-v6.py','bank-process-common.py','probe-bank-readout.py','diagnose-capture-transient.py','report-compact-bank-16.py'])
    for directory in [a.run,a.refined,a.out]:
        files.update(x.resolve() for x in directory.rglob('*') if x.is_file())
    result=dict(fine_total_against_coarse_capture_references_uV=fine_total,scope=__doc__,mos_corner=a.mos_corner,diode_corner='typical',mim_corner='typical',pdk_provenance=provenance,layout=str(a.layout.relative_to(ROOT)),temperature_C=a.temperature,pattern=a.pattern,acquisition_us=13,runs=[detail,finedetail],rows=rows,refinement=differences,event_refinement_worst=event_worst,checks=checks,selected_screen_pass=all(checks.values()),
                contrast_order_applicable=a.pattern in ('alternating','inverse'),
                full_bank_readout_completed=True,full_bank_accuracy_qualified=False,full_chip_qualified=False,
                max_total_error_uV=max(abs(s['total_error_uV']) for s in rows),max_tracking_error_uV=max(abs(s['tracking_error_uV']) for s in rows),max_refinement_uV=max(x['max_uV'] for x in differences),
                limits=[f'{a.temperature} C, {a.mos_corner} MOS corner, typical diode/MIM, nominal supply/wire, {a.pattern} pattern only','50 ns transient has no separate DC references; refinement compares all saved voltages at all 128 output instants','Behavioral drivers, external bias resistors and ADC fixture; one capture and two scans','Remaining temperature/pattern/process/wire/supply/placement coverage and local supply/bias qualification remain open','Real drivers, repeated rows, exact 64x64 chip and provider manufacturing checks remain open'],
                evidence_hashes={str(f.relative_to(ROOT)):sha(f) for f in sorted(files)})
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['checks','max_total_error_uV','max_tracking_error_uV','max_refinement_uV','selected_screen_pass']},indent=2))
    # A measured failure is a completed audit; never hide it by omitting a report.


if __name__=='__main__':main()
