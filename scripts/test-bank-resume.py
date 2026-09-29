"""Reject unsafe reuse while accepting complete transients with interrupted references."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

legacy=module('legacy_tests','test-compact-bank-reuse.py')
reuse=module('reuse_v2','compact-bank-reuse-v2.py')
legacy.reuse=reuse

class Resume(legacy.ReuseTests):
    def test_incomplete_recorded_run_rejected(self):
        # Overall completion includes references; transient completion is separate.
        p=self.old/'result.json';r=json.loads(p.read_text());r['completed']=False
        p.write_text(json.dumps(r));self.record_hashes()
        old,audit=self.audit()
        self.assertFalse(old['completed']);self.assertFalse(audit['source_run_completed'])

    def test_incomplete_transient_rejected(self):
        p=self.old/'result.json';r=json.loads(p.read_text());r['transient']['completed']=False
        p.write_text(json.dumps(r));self.record_hashes()
        with self.assertRaises(AssertionError):self.audit()

    def test_12us_requires_matching_timing(self):
        p=self.old/'result.json';r=json.loads(p.read_text())
        r.update(acquisition_us=12,sample_offset_s=13.999e-6)
        p.write_text(json.dumps(r));self.record_hashes()
        self.settings.update(acquisition_us=12,sample_offset_s=13.999e-6)
        self.audit()
        self.settings['acquisition_us']=10
        with self.assertRaisesRegex(AssertionError,'setting mismatch: acquisition_us'):self.audit()
        self.settings.update(acquisition_us=12,sample_offset_s=11.999e-6)
        with self.assertRaisesRegex(AssertionError,'setting mismatch: sample_offset_s'):self.audit()

    def test_legacy_timing_defaults_only_to_10us(self):
        self.settings.update(acquisition_us=10,sample_offset_s=11.999e-6);self.audit()
        self.settings['acquisition_us']=12
        with self.assertRaisesRegex(AssertionError,'setting mismatch: acquisition_us'):self.audit()

    def reference(self):
        return reuse.audit_reference(self.old,'capture0-reference',self.manifest,self.root,self.deck,self.reader_module)

    def prepare_reference(self):
        d=self.old/'capture0-reference';d.mkdir()
        (d/'test.spice').write_text(self.deck.replace(str(self.new),str(self.old)))
        (d/'ngspice.log').write_text('done\n')
        header=b'Title: DC\nFlags: real\nNo. Variables: 1\nNo. Points: 1\nVariables:\n\t0\tv(hold)\tvoltage\nBinary:\n'
        (d/'op.raw').write_bytes(header+np.array([1.0],dtype=np.float64).tobytes())
        (d/'execution.json').write_text(json.dumps(dict(completed=True,timed_out=False,returncode=0,errors=[],points=1,deck_sha256=reuse.sha(d/'test.spice'))))
        manifest=json.loads(self.manifest.read_text())
        manifest['evidence_hashes'].update({str(p.relative_to(self.root)):reuse.sha(p) for p in d.iterdir()})
        self.manifest.write_text(json.dumps(manifest))
        self.reader_module=module('reader','diagnose-capture-transient.py')
        return d

    def test_reference_requires_matching_frozen_state(self):
        self.prepare_reference();self.assertIsNotNone(self.reference())
        self.deck=self.deck.replace('3.3','3.0')
        with self.assertRaisesRegex(AssertionError,'reference fixture differs'):self.reference()

    def test_reference_corruption_rejected(self):
        d=self.prepare_reference();(d/'op.raw').write_bytes(b'truncated')
        with self.assertRaisesRegex(AssertionError,'Changed reuse artifact'):self.reference()

    def test_interrupted_reference_is_resimulated(self):
        d=self.prepare_reference();(d/'execution.json').unlink()
        self.assertIsNone(self.reference())

    def test_nonfinite_reference_rejected_even_with_hash(self):
        d=self.prepare_reference();p=d/'op.raw'
        p.write_bytes(p.read_bytes()[:-8]+np.array([np.nan],dtype=np.float64).tobytes())
        manifest=json.loads(self.manifest.read_text());manifest['evidence_hashes'][str(p.relative_to(self.root))]=reuse.sha(p)
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(AssertionError,'Incomplete reference trace'):self.reference()

class Decks(unittest.TestCase):
    def test_v3_decks_match_v2(self):
        timing=module('timing','test-bank-v2-timing.py')
        v2=timing.new;v3=module('v3','simulate-compact-bank-v3.py')
        with tempfile.TemporaryDirectory() as tmp:
            for nc,layout in [(2,'compact-bank-c2-v1-20260926'),(16,'compact-bank-c16-ground8-20260927'),(64,'compact-bank-c64-ground-grid-20260927')]:
                for acq in [10,12]:
                    for temp in [27,125]:
                        decks=[]
                        for mod in [v2,v3]:
                            timing.new=mod
                            decks.append(timing.generate(mod,ROOT/'build'/layout,Path(tmp)/f'{mod.__name__}-{nc}-{acq}-{temp}',temp,acq))
                        self.assertEqual(timing.normalize(decks[0]),timing.normalize(decks[1]))

if __name__=='__main__':unittest.main()
