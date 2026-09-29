"""Check crossed-case fixtures, reference budgets, and independent watcher outcomes."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

launcher=module('launch','launch-bank-cross.py')
bank=module('bank','simulate-compact-bank-v3.py')
audit=module('audit','report-bank-full-v2.py')
watchtests=module('watchtests','test-bank-resume-watcher.py')
watchtests.watcher=module('watcher','finish-bank-cross.py')

class Cases(unittest.TestCase):
    def test_budget_and_unique_outputs(self):
        plan=launcher.build_plan('test')
        self.assertEqual([(c['temperature'],c['pattern']) for c in plan['cases']],[(27,'inverse'),(125,'alternating')])
        self.assertEqual(len({r['path'] for r in plan['runs']}),4)
        self.assertEqual(len({r['container'] for r in plan['runs']}),4)
        self.assertEqual(sum('--transient-only' not in r['command'] for r in plan['runs']),2)
        self.assertTrue(all('--reuse-transient' not in r['command'] for r in plan['runs']))
        self.assertTrue(all(not (ROOT/'simulations'/c['report']).exists() for c in plan['cases']))

    def test_invalid_tags_rejected(self):
        for tag in ['', '../old','a/b','A',';bad']:
            with self.assertRaises(AssertionError):launcher.build_plan(tag)

    def test_only_illumination_changes_against_matched_completed_decks(self):
        import re
        with tempfile.TemporaryDirectory() as tmp:
            for run in launcher.build_plan('test')['runs']:
                with self.subTest(run=run['name']):
                    cmd=run['command'][1:];out=Path(tmp)/run['name'];cmd[cmd.index('--out')+1]=str(out);cmd+=['--deck-only']
                    with patch.object(sys,'argv',cmd):bank.main()
                    oldname=('nominal' if run['temperature']==27 else 'hot-inverse')+str(run['step_ns'])
                    previous=ROOT/'build'/f'compact-bank-c64-resume-{oldname}-20260928/transient/test.spice'
                    old=audit.normalize(previous.read_text()).splitlines()
                    new=audit.normalize((out/'transient/test.spice').read_text()).splitlines()
                    self.assertEqual(len(old),len(new))
                    changes=[(a,b) for a,b in zip(old,new) if a!=b]
                    self.assertEqual(len(changes),64)
                    for left,right in changes:
                        a=left.split();b=right.split()
                        self.assertRegex(a[0],r'^Ilight\d+$');self.assertEqual(a[:-1],b[:-1])
                        self.assertEqual({a[-1],b[-1]},{'0p','240p'})
                    self.assertIn(f'.temp {run["temperature"]}',new)
                    lights=[x.split()[-1] for x in new if re.match(r'^Ilight\d+ ',x)]
                    self.assertEqual(lights,(['240p','0p'] if run['pattern']=='inverse' else ['0p','240p'])*32)

    def test_renderer_rejects_wrong_temperature(self):
        renderer=module('renderer','render-bank-cross.py')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'simulations').mkdir()
            (root/'simulations/compact-bank-64-full.json').write_text(json.dumps(dict(temperature_C=125,pattern='alternating')))
            with patch.object(renderer,'ROOT',root),self.assertRaises(AssertionError):renderer.read_reports(launcher.build_plan('test'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Cases),unittest.defaultTestLoader.loadTestsFromTestCase(watchtests.Watcher)])
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    (a.out/'result.json').write_text(json.dumps(dict(tests=r.testsRun,passed=r.wasSuccessful(),failures=len(r.failures),errors=len(r.errors)),indent=2)+'\n')
    raise SystemExit(not r.wasSuccessful())
