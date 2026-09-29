"""Reject corrupted, stale or incomplete evidence before reference-only reuse."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('reuse',Path(__file__).with_name('compact-bank-reuse.py'))
reuse=importlib.util.module_from_spec(spec);spec.loader.exec_module(reuse)


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.old=self.root/'old';self.new=self.root/'new'
        (self.old/'transient').mkdir(parents=True);self.new.mkdir()
        self.model='.subckt tile A B\nR1 A B 100\n.ends tile\n'
        self.settings=dict(columns=2,phase='full',solver='klu',method='trap',driver_form='current')
        self.init='set ngbehavior=hsa\n'
        self.reader=self.new/'trace-reader.py';self.reader.write_text('reader snapshot\n')
        self.deck=f'test\n.include {self.new}/tile.spice\nVDD A 0 3.3\n.end\n'
        olddeck=self.deck.replace(str(self.new),str(self.old))
        files={'tile.spice':self.model,'.spiceinit':self.init,'runner.py':'runner snapshot\n',
               'trace-reader.py':self.reader.read_text(),'transient/test.spice':olddeck,
               'transient/ngspice.log':'ngspice done\n','transient/stream.raw':'trace bytes\n'}
        for name,text in files.items():(self.old/name).write_text(text)
        execution=dict(completed=True,timed_out=False,returncode=0,errors=[],points=2,
                       deck_sha256=reuse.sha(self.old/'transient/test.spice'))
        (self.old/'transient/execution.json').write_text(json.dumps(execution))
        report=dict(**self.settings,completed=True,transient=execution,model_sha256=reuse.sha(self.old/'tile.spice'))
        (self.old/'result.json').write_text(json.dumps(report))
        self.manifest=self.root/'manifest.json';self.record_hashes()

    def record_hashes(self):
        self.manifest.write_text(json.dumps(dict(evidence_hashes={str((self.old/n).relative_to(self.root)):reuse.sha(self.old/n) for n in reuse.ARTIFACTS})))

    def audit(self):
        return reuse.audit(self.old,self.manifest,self.root,self.settings,self.deck,
                           self.new/'tile.spice',self.model,self.init,self.reader)

    def test_identical_fixture_allows_only_new_output_path(self):
        old,audit=self.audit()
        self.assertTrue(old['completed']);self.assertTrue(audit['regenerated_fixture_matches'])
        self.assertEqual(len(audit['source_hashes']),9)

    def test_changed_trace_rejected(self):
        (self.old/'transient/stream.raw').write_text('truncated')
        with self.assertRaisesRegex(AssertionError,'Changed reuse artifact'):self.audit()

    def test_changed_fixture_rejected(self):
        self.deck=self.deck.replace('3.3','3.0')
        with self.assertRaisesRegex(AssertionError,'fixture differs'):self.audit()

    def test_mismatched_solver_rejected(self):
        self.settings['solver']='sparse'
        with self.assertRaisesRegex(AssertionError,'setting mismatch: solver'):self.audit()

    def test_incomplete_recorded_run_rejected(self):
        p=self.old/'result.json';r=json.loads(p.read_text());r['completed']=False;p.write_text(json.dumps(r));self.record_hashes()
        with self.assertRaisesRegex(AssertionError,'complete full transient'):self.audit()

    def test_trace_without_prior_hash_rejected(self):
        r=json.loads(self.manifest.read_text());del r['evidence_hashes']['old/transient/stream.raw'];self.manifest.write_text(json.dumps(r))
        with self.assertRaisesRegex(AssertionError,'Missing previously recorded hash'):self.audit()

    def test_changed_model_rejected_even_with_same_settings(self):
        self.model=self.model.replace('100','101')
        with self.assertRaises(AssertionError):self.audit()

    def test_legacy_default_method_still_requires_identical_fixture(self):
        p=self.old/'result.json';r=json.loads(p.read_text());del r['method'];p.write_text(json.dumps(r));self.record_hashes()
        self.audit()
        self.deck=self.deck.replace('3.3','3.0')
        with self.assertRaisesRegex(AssertionError,'fixture differs'):self.audit()


if __name__=='__main__':unittest.main()
