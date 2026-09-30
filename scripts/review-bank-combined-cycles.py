"""Independent raw-result review and parent-fixture regeneration for candidate cycles."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/name)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
screen=load('screen-bank-combined-cycles.py')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    report=json.loads((source/'result.json').read_text())
    for name,digest in report['evidence_hashes'].items():assert screen.sha(ROOT/name)==digest,name
    meta=json.loads((screen.LAYOUT/'verification.json').read_text())
    assert screen.sha(screen.LAYOUT/'rc-port.spice')==meta['hashes']['rc-port.spice']
    assert screen.sha(screen.LAYOUT/'bank.gds')==meta['gds_sha256']
    cases=[];hashes={str((source/'result.json').relative_to(ROOT)):screen.sha(source/'result.json')}
    for case in report['cases']:
        measurements=[]
        for name in case['runs']:
            run=source/name; record=json.loads((run/'candidate-result.json').read_text());generated=out/name
            subprocess.run([sys.executable,str(ROOT/'scripts/simulate-compact-bank-v4.py'),'--layout',str(screen.LAYOUT),'--out',str(generated),
                            '--lights-pa','240,0','--temperature','125','--step-ns',str(record['step_ns']),'--solver','klu',
                            '--mos-corner',case['corner'],'--acquisition-us','12','--save-mim-terminals','--deck-only'],check=True,stdout=subprocess.DEVNULL)
            assert (generated/'tile.spice').read_bytes()==(run/'parent-tile.spice').read_bytes()
            assert (generated/'transient/test.spice').read_text().replace(str(generated),str(run))==(run/'parent-deck.spice').read_text()
            assert (generated/'pdk-provenance.json').read_bytes()==(run/'pdk-provenance.json').read_bytes()
            model,changes,mids=screen.stack_model((generated/'tile.spice').read_text(),case['series_devices'])
            assert model==(run/'tile.spice').read_text()
            deck=screen.timing_deck((run/'parent-deck.spice').read_text(),case['acquisition_us'],mids)
            assert deck==(run/'transient/test.spice').read_text()
            # Read binary data and recompute errors directly, independently of screen.read_run.
            ix,data=screen.reader.trace(run/'transient/stream.raw')
            assert np.isfinite(data).all() and abs(data[0,0])<1e-15 and abs(data[-1,0]-.00272)<1e-12
            assert np.all(np.diff(data[:,0])>0) and np.max(np.diff(data[:,0]))<=record['step_ns']*1e-9*1.001
            def at(node,t):return 0. if node=='0' else float(np.interp(t,data[:,0],data[:,ix['v('+node.lower()+')']]))
            ref={}
            times=[(f'capture{c}-reference',.0014-1e-9,c,False) for c in range(2)]
            times += [(f'{slot}{c}-output-reference',start+(2+case['acquisition_us'])*1e-6-1e-9,c,True) for slot,c,start in screen.bank.readout_schedule(2)[0]]
            for dirname,t,c,stores in times:
                path=run/dirname
                expected=screen.probe.reference_deck(deck,meta,at,t,c,stores)
                assert expected==(path/'test.spice').read_text()
                ex=json.loads((path/'execution.json').read_text());assert ex['returncode']==0 and not ex['errors']
                ref[dirname]=screen.dc.dc_values(path/'op.raw')
            totals=[];tracks=[];sample_voltages=[]
            for s,(slot,c,start) in zip(record['samples'],screen.bank.readout_schedule(2)[0]):
                t=start+(2+case['acquisition_us'])*1e-6-1e-9
                assert s['time_s']==t and s['slot']==slot and s['column']==c
                actual={n:float(np.interp(t,data[:,0],data[:,i])) for n,i in ix.items() if n!='time'}
                assert actual==s['values']
                total=(at('HOLD',t)-ref[f'capture{c}-reference']['v(hold)'])*1e6
                track=(at('HOLD',t)-ref[f'{slot}{c}-output-reference']['v(hold)'])*1e6
                assert abs(total-s['total_error_uV'])<1e-7 and abs(track-s['tracking_error_uV'])<1e-7
                totals.append(total);tracks.append(track);sample_voltages.append(actual)
            plates=[l.split()[1:3] for l in model.splitlines() if len(l.split())>3 and l.split()[3].startswith('cap_mim_')]
            assert len(plates)==16
            def node(n):return '0' if n=='GND' else n if n in meta['ports'] else 'xtile.'+n
            events=[]
            for t in [.0014-1e-9,.001402-1e-9,.0014025,.001405]:
                events.extend(at(node(hi),t)-at(node(lo),t) for hi,lo in plates)
            measurements.append(dict(total=totals,tracking=tracks,mim_events=events,samples=sample_voltages))
        coarse,fine=measurements
        total=max(abs(v) for m in measurements for v in m['total']);tracking=max(abs(v) for m in measurements for v in m['tracking'])
        assert total==case['max_total_error_uV'] and tracking==case['max_tracking_error_uV']
        mim_delta=max(abs(a-b)*1e6 for a,b in zip(coarse['mim_events'],fine['mim_events']))
        cases.append(dict(name=case['runs'][0].rsplit('-',1)[0],max_total_error_uV=total,max_tracking_error_uV=tracking,
                          mim_differential_refinement_uV=mim_delta,selected_screen_pass=case['selected_screen_pass'] and mim_delta<10))
    # Guard tests: reject unsupported topology/timing and missing or duplicate hold devices.
    parent=(source/report['cases'][0]['runs'][0]/'parent-tile.spice').read_text()
    original,=[l for l in parent.splitlines() if l.startswith('X34 ')]
    rejects=[lambda:screen.stack_model(parent,4),lambda:screen.stack_model(parent.replace(original+'\n',''),2),
             lambda:screen.stack_model(parent+original.replace('X34 ','XDUP ')+ '\n',2),
             lambda:screen.timing_deck(deck,13,[])]
    for reject in rejects:
        try:reject()
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Invalid candidate accepted')
    files=[p for p in out.rglob('*') if p.is_file()]+[Path(__file__)]
    hashes.update({str(p.relative_to(ROOT)):screen.sha(p) for p in files})
    result=dict(cases=cases,reviewed_transients=6,reviewed_references=36,verified_source_hashes=len(report['evidence_hashes']),
                regenerated_parent_decks=6,guard_tests_passed=len(rejects),model_only=True,full_bank_accuracy_qualified=False,evidence_hashes=hashes)
    screen.save(out/'result.json',result);print(json.dumps(result['cases'],indent=2))

if __name__=='__main__':main()
