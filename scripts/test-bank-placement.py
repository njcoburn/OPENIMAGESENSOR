"""Validate exact placement edits, fixtures, sensitivity gates and retained-data audits."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


helper = module('helper', 'bank-placement-common.py')
launch = module('launch', 'launch-bank-placement.py')
audit = module('audit', 'report-bank-placement.py')
bank = module('bank', 'simulate-compact-bank-v3.py')
retained = module('retained', 'test-bank-resume-audit.py'); retained.tests.full = audit
watch = module('watch', 'test-bank-placement-watcher.py')
LAYOUT = ROOT / 'build/compact-bank-c64-ground-grid-20260927'


class Placement(unittest.TestCase):
    def test_exact_67_shunt_variant(self):
        meta = json.loads((LAYOUT / 'verification.json').read_text())
        self.assertEqual(len(helper.check_variant(LAYOUT, meta)), 67)

    def test_value_and_endpoint_changes_rejected_even_with_new_hash(self):
        for change in ('value', 'endpoint'):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)
                meta = json.loads((LAYOUT / 'verification.json').read_text())
                (path / 'rc-port.spice').write_bytes((LAYOUT / 'rc-port.spice').read_bytes())
                lines = (LAYOUT / 'rc-far.spice').read_text().splitlines()
                index = next(i for i, line in enumerate(lines) if line.startswith('CFIX0 '))
                fields = lines[index].split()
                if change == 'value':fields[-1] = str(float(fields[-1]) * 2)
                else:fields[1] = 'WRONG_ENDPOINT'
                lines[index] = ' '.join(fields)
                target = path / 'rc-far.spice'; target.write_text('\n'.join(lines) + '\n')
                meta['hashes']['rc-far.spice'] = hashlib.sha256(target.read_bytes()).hexdigest()
                with self.assertRaises(AssertionError):helper.check_variant(path, meta)

    def test_matched_samples_and_sensitivity(self):
        baseline = json.loads((ROOT / 'build/compact-bank-c64-resume-nominal100-20260928/result.json').read_text())
        placed = copy.deepcopy(baseline)
        self.assertEqual(helper.sample_delta(baseline, placed)['hold_max_uV'], 0)
        placed['samples'][7]['values']['HOLD'] += 11e-6
        self.assertGreater(helper.sample_delta(baseline, placed)['hold_max_uV'], 10)
        placed['samples'][9]['values']['STORE63'] += 12e-6
        self.assertGreater(helper.sample_delta(baseline, placed)['store_max_uV'], 10)
        placed['samples'][0]['time_s'] += 1e-6
        with self.assertRaises(AssertionError):helper.sample_delta(baseline, placed)

    def test_wrong_pattern_or_temperature_rejected(self):
        baseline = json.loads((ROOT / 'build/compact-bank-c64-resume-nominal100-20260928/result.json').read_text())
        for key, value in [('temperature_C', 125), ('lights_pA', [80] * 64)]:
            placed = copy.deepcopy(baseline); placed[key] = value
            with self.assertRaises(AssertionError):helper.sample_delta(baseline, placed)

    def test_four_decks_keep_all_fixture_lines_identical(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan = launch.build_plan('test')
            self.assertEqual(len(plan['runs']), 4)
            self.assertEqual(sum('--transient-only' not in r['command'] for r in plan['runs']), 2)
            for run in plan['runs']:
                command = run['command'][1:]; path = Path(temporary) / run['name']
                command[command.index('--out') + 1] = str(path); command += ['--deck-only']
                with patch.object(sys, 'argv', command):bank.main()
                name = ('nominal' if run['temperature'] == 27 else 'hot-inverse') + str(run['step_ns'])
                old = ROOT / f'build/compact-bank-c64-resume-{name}-20260928/transient/test.spice'
                self.assertEqual(audit.normalize(old.read_text()), audit.normalize((path / 'transient/test.spice').read_text()))
                self.assertEqual((path / 'tile.spice').read_bytes(), (LAYOUT / 'rc-far.spice').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=False)
    retained.tests.OUT = args.out / 'retained'; retained.tests.OUT.mkdir()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                               for cls in (Placement, retained.ResumeAudit, watch.Watcher))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (args.out / 'result.json').write_text(json.dumps(dict(tests=result.testsRun, passed=result.wasSuccessful(),
        failures=len(result.failures), errors=len(result.errors)), indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
