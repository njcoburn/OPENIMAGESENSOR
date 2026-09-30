"""Check uniform fixtures, declared illumination, acceptance limits and retained-data audits."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


launcher = module('launcher', 'launch-bank-uniform.py')
bank = module('bank', 'simulate-compact-bank-v3.py')
audit = module('audit', 'report-bank-full-v3.py')
retained = module('retained', 'test-bank-resume-audit.py')
retained.tests.full = audit
watch = module('watch', 'test-bank-uniform-watcher.py')


class Uniform(unittest.TestCase):
    def pair(self, pattern):
        main = dict(columns=64, acquisition_us=12, temperature_C=27,
                    lights_pA=audit.pattern_lights(pattern), step_ns=100, references_requested=True)
        fine = {**main, 'step_ns': 50, 'references_requested': False}
        return main, fine

    def test_all_uniform_pairs_explicitly_accepted(self):
        for pattern, value in [('dark', 0), ('middle', 80), ('bright', 240)]:
            main, fine = self.pair(pattern)
            self.assertEqual(audit.validate_pair(main, fine, 27, pattern), [value] * 64)

    def test_wrong_or_relabelled_illumination_rejected(self):
        for pattern in audit.PATTERNS:
            main, fine = self.pair(pattern)
            main['lights_pA'] = list(main['lights_pA'])
            main['lights_pA'][31] += 1
            with self.assertRaisesRegex(AssertionError, 'Illumination'):
                audit.validate_pair(main, fine, 27, pattern)
        main, fine = self.pair('dark')
        with self.assertRaises(AssertionError):
            audit.validate_pair(main, fine, 27, 'alternating')

    def test_pair_temperature_timing_and_reference_roles_enforced(self):
        for key, value in [('temperature_C', 125), ('acquisition_us', 10), ('step_ns', 100), ('references_requested', True)]:
            main, fine = self.pair('middle')
            fine[key] = value
            with self.assertRaises(AssertionError):
                audit.validate_pair(main, fine, 27, 'middle')

    def test_uniform_contrast_is_not_a_vacuous_pass(self):
        for pattern in ('dark', 'middle', 'bright'):
            run = dict(lights_pA=audit.pattern_lights(pattern), capture_readout_pass=True, tracking_pass=True)
            checks = audit.screen_checks(run, [{'max_uV': 1}], {'difference_uV': 1}, pattern)
            self.assertEqual(set(checks), {'capture_readout', 'output_tracking', 'refinement', 'event_refinement'})
            self.assertTrue(all(checks.values()))
            self.assertFalse(audit.screen_checks(run, [{'max_uV': 10}], {'difference_uV': 1}, pattern)['refinement'])
            self.assertFalse(audit.screen_checks(run, [{'max_uV': 1}], {'difference_uV': 10}, pattern)['event_refinement'])
            run['capture_readout_pass'] = False
            self.assertFalse(all(audit.screen_checks(run, [{'max_uV': 1}], {'difference_uV': 1}, pattern).values()))

    def test_alternating_contrast_is_still_enforced(self):
        run = dict(lights_pA=audit.pattern_lights('alternating'), capture_readout_pass=True, tracking_pass=True,
                   samples=[dict(column=c, values={'HOLD': 2 if c % 2 == 0 else 1}) for c in range(64)] * 2)
        self.assertTrue(audit.screen_checks(run, [{'max_uV': 1}], {'difference_uV': 1}, 'alternating')['contrast_order'])
        run['samples'][0]['values']['HOLD'] = 0
        self.assertFalse(audit.screen_checks(run, [{'max_uV': 1}], {'difference_uV': 1}, 'alternating')['contrast_order'])

    def test_bounded_budget_and_fresh_names(self):
        names, paths, reports = set(), set(), set()
        for pattern in ('dark', 'middle', 'bright'):
            plan = launcher.build_plan('test', pattern)
            self.assertEqual(len(plan['runs']), 4)
            self.assertEqual({c['temperature'] for c in plan['cases']}, {27, 125})
            self.assertEqual(sum('--transient-only' not in r['command'] for r in plan['runs']), 2)
            for run in plan['runs']:
                self.assertNotIn(run['container'], names); names.add(run['container'])
                self.assertNotIn(run['path'], paths); paths.add(run['path'])
                self.assertNotIn('--reuse-transient', run['command'])
            for case in plan['cases']:
                self.assertNotIn(case['report'], reports); reports.add(case['report'])

    def test_invalid_pattern_and_tag_rejected(self):
        for pattern in ('uniform', 'alternating', '../dark'):
            with self.assertRaises(AssertionError):launcher.build_plan('test', pattern)
        for tag in ('', '../old', 'a/b', 'A', ';bad'):
            with self.assertRaises(AssertionError):launcher.build_plan(tag)

    def test_all_twelve_decks_change_only_illumination(self):
        with tempfile.TemporaryDirectory() as temporary:
            for pattern in ('dark', 'middle', 'bright'):
                for run in launcher.build_plan('test', pattern)['runs']:
                    with self.subTest(run=run['name']):
                        command = run['command'][1:]
                        out = Path(temporary) / run['name']
                        command[command.index('--out') + 1] = str(out)
                        command += ['--deck-only']
                        with patch.object(sys, 'argv', command):bank.main()
                        previous = ('nominal' if run['temperature'] == 27 else 'hot-inverse') + str(run['step_ns'])
                        old = ROOT / 'build' / f'compact-bank-c64-resume-{previous}-20260928/transient/test.spice'
                        oldlines = audit.normalize(old.read_text()).splitlines()
                        newlines = audit.normalize((out / 'transient/test.spice').read_text()).splitlines()
                        remove_lights = lambda lines: [line for line in lines if not re.match(r'^Ilight\d+ ', line)]
                        self.assertEqual(remove_lights(oldlines), remove_lights(newlines))
                        lights = [line.split()[-1] for line in newlines if re.match(r'^Ilight\d+ ', line)]
                        self.assertEqual(lights, [str(audit.pattern_lights(pattern)[0]) + 'p'] * 64)

    def test_renderer_rejects_false_contrast_claim(self):
        renderer = module('renderer', 'render-bank-uniform.py')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / 'simulations').mkdir()
            report = dict(temperature_C=27, pattern='dark', full_bank_readout_completed=True,
                          full_bank_accuracy_qualified=False, full_chip_qualified=False,
                          contrast_order_applicable=True)
            (root / 'simulations/compact-bank-64-uniform-dark27.json').write_text(json.dumps(report))
            with patch.object(renderer, 'ROOT', root), self.assertRaises(AssertionError):
                renderer.read_reports(launcher.build_plan('test'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=False)
    retained.tests.OUT = args.out / 'retained'; retained.tests.OUT.mkdir()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                               for cls in (Uniform, retained.ResumeAudit, watch.Watcher))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (args.out / 'result.json').write_text(json.dumps(dict(tests=result.testsRun, passed=result.wasSuccessful(),
        failures=len(result.failures), errors=len(result.errors)), indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
