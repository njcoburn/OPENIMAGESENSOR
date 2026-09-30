"""Deck regression, corner isolation, reference propagation and adversarial checks."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

common=module('common','bank-process-common.py');old=module('old','simulate-compact-bank-v3.py');new=module('new','simulate-compact-bank-v4.py')
audit=module('audit','report-bank-process.py');probe=module('probe','probe-bank-readout.py')
OUT=None

class Process(unittest.TestCase):
    def deck(self,name,runner,corner='typical',temp=125,step=100,columns=64):
        layout=ROOT/('build/compact-bank-c64-ground-grid-20260927' if columns==64 else 'build/compact-bank-c2-v1-20260926')
        dest=OUT/name
        args=['runner','--layout',str(layout),'--out',str(dest),'--lights-pa',','.join(map(str,[240,0]*(columns//2))),
              '--temperature',str(temp),'--step-ns',str(step),'--solver','klu','--acquisition-us','12','--deck-only','--transient-only','--save-mim-terminals']
        if runner is new:args+=['--mos-corner',corner]
        with patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO()):runner.main()
        return (dest/'transient/test.spice').read_text(),json.loads((layout/'verification.json').read_text())

    def test_typical_decks_unchanged(self):
        for nc,temp,step in [(2,27,100),(64,27,50),(64,125,100),(64,125,50)]:
            name=f'{nc}-{temp}-{step}'
            a,_=self.deck('old-'+name,old,temp=temp,step=step,columns=nc)
            b,_=self.deck('new-'+name,new,temp=temp,step=step,columns=nc)
            common.compare_process_only(a,b,'typical')

    def test_all_mos_corners_change_only_library_and_reference_propagates(self):
        for step in [100,50]:
            original,meta=self.deck(f'typical-{step}',new,step=step)
            for corner in ['ss','ff','fs','sf']:
                deck,_=self.deck(f'{corner}-{step}',new,corner,step=step)
                common.compare_process_only(original,deck,corner)
                for stores in [False,True]:
                    ref=probe.reference_deck(deck,meta,lambda n,t:0.5,.0014,0,stores)
                    base=probe.reference_deck(original,meta,lambda n,t:0.5,.0014,0,stores)
                    common.validate_models(ref,corner);common.compare_process_only(base,ref,corner)

    def test_wrong_or_additional_libraries_rejected(self):
        deck,_=self.deck('corrupt-library',new,'ss')
        for changed in [deck.replace('diode_typical','diode_ss'),deck.replace('mimcap_typical','mimcap_ff'),deck.replace('ngspice ss','ngspice ff'),deck+'\n.lib unwanted.spice typical\n']:
            with self.assertRaises(AssertionError):common.validate_models(changed,'ss')

    def test_supply_or_timing_change_rejected(self):
        typical,_=self.deck('supply-typical',new);ss,_=self.deck('supply-ss',new,'ss')
        for changed in [ss.replace('Vsource RAW 0 3.3','Vsource RAW 0 3.0'),ss.replace('14.','13.',1),ss.replace('abstol=1e-16','abstol=1e-12')]:
            # Explicitly guarantee this corruption is a real modification.
            if changed==ss:changed=ss.replace('.tran 100n','.tran 200n')
            with self.assertRaises(AssertionError):common.compare_process_only(typical,changed,'ss')

    def test_mismatched_process_pair_rejected(self):
        base=dict(columns=64,acquisition_us=12,temperature_C=125,lights_pA=[240,0]*32,mos_corner='ss')
        coarse=dict(base,step_ns=100,references_requested=True);fine=dict(base,step_ns=50,references_requested=False)
        audit.validate_pair(coarse,fine,125,'inverse')
        fine['mos_corner']='ff'
        with self.assertRaises(AssertionError):audit.validate_pair(coarse,fine,125,'inverse')

    def test_pass_thresholds_not_relaxed(self):
        run=dict(lights_pA=[240,0]*32,capture_readout_pass=True,tracking_pass=True,
                 samples=[dict(column=c,values={'HOLD':1 if c%2==0 else 2}) for c in range(64)]*2)
        self.assertTrue(all(audit.screen_checks(run,[dict(max_uV=9.99)],dict(difference_uV=9.99),'inverse').values()))
        self.assertFalse(audit.screen_checks(run,[dict(max_uV=10)],dict(difference_uV=0),'inverse')['refinement'])
        self.assertFalse(audit.screen_checks(run,[dict(max_uV=0)],dict(difference_uV=10),'inverse')['event_refinement'])
        run['capture_readout_pass']=False
        self.assertFalse(all(audit.screen_checks(run,[dict(max_uV=0)],dict(difference_uV=0),'inverse').values()))

    def test_reuse_rejected(self):
        args=['runner','--layout','unused','--out',str(OUT/'reuse'),'--mos-corner','ss','--reuse-transient','old','--reuse-manifest','old.json']
        with patch.object(sys,'argv',args),self.assertRaisesRegex(AssertionError,'fresh evidence'):new.main()
        self.assertFalse((OUT/'reuse').exists())

    def test_pdk_snapshot_covers_installed_files(self):
        provenance=common.pdk_provenance()
        self.assertIn('sm141064.ngspice',provenance['files'])
        self.assertIn('sm141064.spice',provenance['files'])
        self.assertEqual(set(provenance['mos_corners']),set(common.CORNERS))
        (OUT/'pdk-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')

    def test_fresh_plan_names_and_counts(self):
        launch=module('launch','launch-bank-process.py');plan=launch.build_plan('test-process')
        self.assertEqual(len(plan['runs']),4);self.assertEqual(len(plan['cases']),2)
        self.assertEqual({c['mos_corner'] for c in plan['cases']},{'ss','ff'})
        self.assertEqual(len({r['path'] for r in plan['runs']}),4)
        self.assertTrue(all('test-process' in c['report'] for c in plan['cases']))
        for tag in ['', '../bad', 'UPPER']:
            with self.assertRaises(AssertionError):launch.build_plan(tag)


def main():
    global OUT
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    OUT=a.out.resolve();OUT.mkdir(parents=True,exist_ok=False)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Process)
    watcher=module('watch_tests','test-bank-process-watcher.py')
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(watcher))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    files=['simulate-compact-bank-v4.py','report-bank-process.py','bank-process-common.py','test-bank-process.py','test-bank-process-watcher.py','launch-bank-process.py','finish-bank-process.py','run-bank-process-job.py','render-bank-process.py','update-verification-journal.py']
    summary=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                 source_hashes={f'scripts/{n}':hashlib.sha256((ROOT/'scripts'/n).read_bytes()).hexdigest() for n in files})
    (OUT/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())

if __name__=='__main__':main()
