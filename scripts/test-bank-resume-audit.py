"""Exercise the resumed auditor on retained data and reject false reuse provenance."""
import argparse
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

tests=module('audit_tests','test-bank-full-audit.py')
tests.full=module('resume_audit','report-bank-full-v2.py')

class ResumeAudit(tests.Audit):
    def test_false_reuse_manifest_rejected(self):
        def mutation(r):
            r['transient_reuse']=dict(evidence_manifest='simulations/compact-bank-resume-snapshot-20260928.json',evidence_manifest_sha256='0'*64)
        with self.assertRaises(AssertionError):self.check(mutation)

    def test_false_reuse_source_rejected(self):
        def mutation(r):
            manifest=ROOT/'simulations/compact-bank-resume-snapshot-20260928.json'
            r['transient_reuse']=dict(evidence_manifest=str(manifest.relative_to(ROOT)),
                evidence_manifest_sha256=tests.full.sha(manifest),source_directory=str(tests.RUN.relative_to(ROOT)),
                source_hashes={'tile.spice':'0'*64})
        with self.assertRaises(AssertionError):self.check(mutation)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    tests.OUT=a.out.resolve();tests.OUT.mkdir(parents=True,exist_ok=False)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ResumeAudit))
    (tests.OUT/'result.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),passed=r.wasSuccessful()),indent=2)+'\n')
    raise SystemExit(not r.wasSuccessful())
