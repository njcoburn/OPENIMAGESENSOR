"""Use retained passing evidence and adversarial summaries to exercise the audit."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('full',ROOT/'scripts/report-bank-full.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
RUN=ROOT/'build/compact-bank-c16-ground8-nominal-20260927';LAYOUT=ROOT/'build/compact-bank-c16-ground8-20260927'

class Audit(unittest.TestCase):
    def check(self,mutation=None):
        r=json.loads((RUN/'result.json').read_text())
        if mutation:mutation(r)
        return full.audit_run(RUN,LAYOUT,OUT/self.id().rsplit('.',1)[1],r)
    def test_retained_complete_control(self):
        r,d=self.check();self.assertEqual(d['references'],48);self.assertEqual(d['samples'],32);self.assertTrue(r['capture_readout_pass'])
    def test_missing_sample_rejected(self):
        with self.assertRaises(AssertionError):self.check(lambda r:r['samples'].pop())
    def test_wrong_sample_time_rejected(self):
        with self.assertRaises(AssertionError):self.check(lambda r:r['samples'][0].update(time_s=.001423999))
    def test_missing_saved_node_rejected(self):
        with self.assertRaises(AssertionError):self.check(lambda r:r['samples'][0]['values'].pop('HOLD'))
    def test_false_reference_rejected(self):
        with self.assertRaises(AssertionError):self.check(lambda r:r['capture_references'][0]['values'].update(HOLD=2.1))
    def test_false_error_or_pass_rejected(self):
        with self.assertRaises(AssertionError):self.check(lambda r:r.update(capture_readout_pass=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();OUT=a.out.resolve();OUT.mkdir(parents=True,exist_ok=False)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Audit))
    (OUT/'result.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),passed=r.wasSuccessful()),indent=2)+'\n')
    raise SystemExit(not r.wasSuccessful())
