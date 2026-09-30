"""Guard unattended stage transitions and validate all full-bank corner decks."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    controller=load('continue-bank-stack5.py');launcher=load('launch-bank-stack5.py');bank=load('simulate-compact-bank-v6.py');common=load('bank-process-common.py');probe=load('probe-bank-readout.py')
    good={'selected_screen_pass':True};bad={'selected_screen_pass':False}
    assert controller.stage_pass([good,good],2,{})
    for reports,n,failures in [([good],2,{}),([good,bad],2,{}),([good,{}],2,{}),([good,good],2,{'audit':'failed'}),([],2,{})]:assert not controller.stage_pass(reports,n,failures)
    plan=launcher.build_plan('guard-test');assert len(plan['stages'])==8
    assert plan['max_workers']==3 and plan['job_timeout_seconds']==43200 and plan['sequence_timeout_seconds']==172800
    cases=[c for s in plan['stages'] for c in s['cases']];runs=[r for s in plan['stages'] for r in s['runs']]
    assert len(cases)==18 and len(runs)==36 and len({c['report'] for c in cases})==18 and len({r['path'] for r in runs})==36
    assert all(r['command'][r['command'].index('--timeout')+1]=='28800' for r in runs)
    assert all(r['command'][r['command'].index('--acquisition-us')+1]=='13' for r in runs)
    assert len(plan['stages'][0]['runs'])==6 and {c['corner'] for c in plan['stages'][1]['cases']}=={'fs','sf'}
    for tag in ['', '../bad','BAD']:
        try:launcher.build_plan(tag)
        except AssertionError:pass
        else:raise AssertionError('Bad tag accepted')
    layout=ROOT/launcher.LAYOUT;meta=json.loads((layout/'verification.json').read_text());decks={}
    for step in [100,50]:
        for corner in ['typical','ss','ff','fs','sf']:
            dest=out/f'{corner}-{step}'
            argv=['bank','--layout',str(layout),'--out',str(dest),'--lights-pa',','.join(map(str,[240,0]*32)),'--temperature','125','--step-ns',str(step),'--solver','klu','--mos-corner',corner,'--acquisition-us','13','--save-mim-terminals','--deck-only']
            with patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):bank.main()
            deck=(dest/'transient/test.spice').read_text();decks[corner,step]=deck
            private=['v(xtile.'+n['extracted_node'].lower()+')' for path in meta['stack_paths'] for n in path['private_nodes']]
            assert len(private)==len(set(private))==256 and all(n in deck for n in private)
            assert (dest/'tile.spice').read_bytes()==(layout/'rc-port.spice').read_bytes()
            common.compare_process_only(decks['typical',step],deck,corner)
            for stores in [False,True]:
                reference=probe.reference_deck(deck,meta,lambda n,t:.5,.0014,63,stores);common.validate_models(reference,corner)
    # Explicit legacy timing must generate the same circuit as the frozen v5 runner.
    legacy=load('simulate-compact-bank-v5.py');legacy_layout=ROOT/'build/compact-bank-c2-stack3-v3-20260930'
    legacy_decks=[]
    for label,runner in [('v5',legacy),('v6',bank)]:
        dest=out/('legacy-'+label)
        argv=['bank','--layout',str(legacy_layout),'--out',str(dest),'--lights-pa','240,0','--temperature','125','--step-ns','100','--solver','klu','--acquisition-us','12.5','--save-mim-terminals','--deck-only']
        with patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):runner.main()
        legacy_decks.append((dest/'transient/test.spice').read_text().replace(str(dest),'NORMALIZED'))
    assert legacy_decks[0]==legacy_decks[1]
    report=dict(legacy_timing_deck_unchanged=True,passed=True,transition_guard_cases=6,full_bank_decks_checked=10,reference_corner_checks=20,planned_cases=18,planned_transients=36,planned_references=3456,
                source_hashes={f'scripts/{n}':controller.sha(ROOT/'scripts'/n) for n in ['test-bank-stack5-continuation.py','continue-bank-stack5.py','launch-bank-stack5.py','simulate-compact-bank-v6.py','report-bank-stack5.py','render-bank-stack5-progress.py']})
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'},indent=2))
if __name__=='__main__':main()
