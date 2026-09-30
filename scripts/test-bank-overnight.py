"""Require passing predecessor audits and reject damaged evidence before continuation."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('overnight', Path(__file__).with_name('continue-bank-overnight.py'))
overnight = importlib.util.module_from_spec(spec); spec.loader.exec_module(overnight)


class Gate(unittest.TestCase):
    def valid(self):
        return dict(failures={}, render_failures={}, watcher_expired=False, all_pairs_audited=True,
                    all_selected_screens_pass=True, audited={'bright27': True, 'bright125': True})

    def test_pending_does_not_launch(self):
        self.assertFalse(overnight.gate_ready({}))
        state = self.valid(); state['all_pairs_audited'] = False
        self.assertFalse(overnight.gate_ready(state))

    def test_complete_pass_is_ready(self):self.assertTrue(overnight.gate_ready(self.valid()))

    def test_failures_expiry_and_wrong_cases_stop_continuation(self):
        for key, value in [('failures', {'bright27': 'failed'}), ('render_failures', {'plot': 'failed'}),
                           ('watcher_expired', True), ('all_selected_screens_pass', False),
                           ('audited', {'bright27': True})]:
            state = self.valid(); state[key] = value
            with self.assertRaises(AssertionError):overnight.gate_ready(state)

    def fixture(self, root):
        (root / 'evidence').write_text('trace fixture')
        digest = hashlib.sha256((root / 'evidence').read_bytes()).hexdigest()
        report = dict(pattern='bright', selected_screen_pass=True,
            checks=dict(capture_readout=True, output_tracking=True, refinement=True, event_refinement=True),
            contrast_order_applicable=False, full_bank_accuracy_qualified=False, full_chip_qualified=False,
            runs=[dict(samples=128, references=192), dict(samples=128, references=0)],
            max_total_error_uV=100, max_tracking_error_uV=10, max_refinement_uV=1,
            event_refinement_worst=dict(difference_uV=1), evidence_hashes={'evidence': digest})
        for temperature in (27, 125):
            (root / f'{temperature}.json').write_text(json.dumps({**report, 'temperature_C': temperature}))
        return ['27.json', '125.json']

    def test_verified_reports_accepted_and_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); paths = self.fixture(root)
            self.assertEqual(len(overnight.verify_reports(root, paths)[0]), 2)
            (root / 'evidence').write_text('corrupt')
            with self.assertRaises(AssertionError):overnight.verify_reports(root, paths)

    def test_false_pass_with_out_of_limit_error_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); paths = self.fixture(root)
            report = json.loads((root / '27.json').read_text()); report['max_total_error_uV'] = 501
            (root / '27.json').write_text(json.dumps(report))
            with self.assertRaises(AssertionError):overnight.verify_reports(root, paths)


if __name__ == '__main__':unittest.main()
