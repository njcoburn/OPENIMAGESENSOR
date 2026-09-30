"""Keep remaining audits alive after rendering errors; distinguish accuracy failure."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('watcher',Path(__file__).with_name('finish-bank-placement.py'))
watcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(watcher)

class Watcher(unittest.TestCase):
    def exercise(self,render_error=False):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir();(root/'simulations').mkdir()
            (root/'scripts/monitor-bank-full.py').write_text('def progress(path): return dict(run=str(path))\n')
            cases=[dict(baseline_report='baseline.json',name=name,coarse=name+'100',fine=name+'50',temperature=temp,pattern=pattern,report=report)
                   for name,temp,pattern,report in [('nominal',27,'alternating','compact-bank-64-full.json'),('hot',125,'inverse','hot.json')]]
            for case in cases:
                for key in ['coarse','fine']:
                    d=root/case[key];d.mkdir();(d/'result.json').write_text(json.dumps(dict(completed=case['name']=='nominal')))
            plan=root/'plan.json';plan.write_text(json.dumps(dict(cases=cases)));out=root/'watch'
            def execute(command,**kwargs):
                if command[1]=='scripts/report-bank-placement.py':
                    d=Path(command[command.index('--out')+1]);d.mkdir()
                    (d/'result.json').write_text(json.dumps(dict(selected_screen_pass='nominal' in d.name)))
                elif render_error:raise subprocess.CalledProcessError(1,command)
            def complete_second(_):
                for key in ['coarse','fine']:(root/cases[1][key]/'result.json').write_text(json.dumps(dict(completed=True)))
            argv=['watcher','--plan',str(plan),'--out',str(out)]
            with patch.object(watcher,'ROOT',root),patch.object(sys,'argv',argv),patch.object(watcher.subprocess,'run',side_effect=execute),patch.object(watcher.time,'sleep',side_effect=complete_second) as sleep:
                with self.assertRaises(SystemExit) as exit_:watcher.main()
            state=json.loads((out/'status.json').read_text())
            self.assertEqual(sleep.call_count,1)
            self.assertTrue(state['all_pairs_audited'])
            self.assertFalse(state['all_selected_screens_pass'])
            self.assertEqual(state['audited'],dict(nominal=True,hot=False))
            self.assertEqual(state['failures'],{})
            self.assertEqual(bool(exit_.exception.code),render_error)
            self.assertEqual(bool(state['render_failures']),render_error)

    def test_render_failure_does_not_skip_pending_pair(self):self.exercise(render_error=True)
    def test_accuracy_failure_is_a_completed_audit(self):self.exercise()

if __name__=='__main__':unittest.main()
