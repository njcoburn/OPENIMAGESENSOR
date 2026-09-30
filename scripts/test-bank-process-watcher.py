"""Watcher failure handling for process-corner jobs and independent audits."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('watcher',Path(__file__).with_name('finish-bank-process.py'))
watcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(watcher)

class Watcher(unittest.TestCase):
    def exercise(self,render_error=False,early_failure=False,expired=False,all_pass=False):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir();(root/'simulations').mkdir()
            (root/'scripts/monitor-bank-full.py').write_text('def progress(path): return dict(run=str(path))\n')
            cases=[];runs=[]
            for corner in ['ss','ff']:
                cases.append(dict(name=corner,coarse=corner+'100',fine=corner+'50',temperature=125,pattern='inverse',mos_corner=corner,report=corner+'.json'))
                for step in [100,50]:
                    name=corner+str(step);d=root/name;d.mkdir()
                    runs.append(dict(path=name,exit_record=name+'/exit.json'))
                    if corner=='ss':
                        (d/'exit.json').write_text(json.dumps(dict(returncode=1 if early_failure else 0)))
                        if not early_failure:(d/'result.json').write_text(json.dumps(dict(completed=True,pdk_provenance={})))
            plan=root/'plan.json';plan.write_text(json.dumps(dict(cases=cases,runs=runs,evidence_hashes={},pdk_provenance={},layout='fixture')));out=root/'watch'
            def execute(command,**kwargs):
                if command[1]=='scripts/report-bank-process.py':
                    d=Path(command[command.index('--out')+1]);d.mkdir()
                    (d/'result.json').write_text(json.dumps(dict(selected_screen_pass=all_pass or 'ss-audit' in d.name)))
                elif render_error:raise subprocess.CalledProcessError(1,command)
            def complete_second(_):
                for step in [100,50]:
                    d=root/f'ff{step}';(d/'exit.json').write_text(json.dumps(dict(returncode=0)))
                    (d/'result.json').write_text(json.dumps(dict(completed=True,pdk_provenance={})))
            argv=['watcher','--plan',str(plan),'--out',str(out)]
            if expired:argv+=['--watch-seconds','0.00000001']
            with patch.object(watcher,'ROOT',root),patch.object(sys,'argv',argv),patch.object(watcher.subprocess,'run',side_effect=execute),patch.object(watcher.time,'sleep',side_effect=complete_second):
                with self.assertRaises(SystemExit) as exit_:watcher.main()
            return json.loads((out/'status.json').read_text()),exit_.exception.code

    def test_render_failure_does_not_skip_pending_pair(self):
        state,code=self.exercise(render_error=True)
        self.assertEqual(state['audited'],dict(ss=True,ff=False));self.assertTrue(state['render_failures']);self.assertTrue(code)

    def test_accuracy_failure_is_completed_but_stops_success(self):
        state,code=self.exercise()
        self.assertTrue(state['all_pairs_audited']);self.assertFalse(state['all_selected_screens_pass']);self.assertFalse(state['failures']);self.assertTrue(code)

    def test_early_process_failure_without_result_is_recorded(self):
        state,code=self.exercise(early_failure=True)
        self.assertIn('ss',state['failures']);self.assertIn('ff',state['audited']);self.assertTrue(code)

    def test_watchdog_cannot_claim_success(self):
        state,code=self.exercise(expired=True)
        self.assertTrue(state['watcher_expired']);self.assertFalse(state['all_pairs_audited']);self.assertTrue(code)

    def test_success_requires_both_pairs(self):
        state,code=self.exercise(all_pass=True)
        self.assertTrue(state['all_selected_screens_pass']);self.assertFalse(code)

if __name__=='__main__':unittest.main()
