"""Reject corrupted simulation summaries and unintended placement-model edits."""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit', ROOT / 'scripts/report-bank-16-extension.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((LAYOUT / 'verification.json').read_text())
        cls.result = json.loads((RUN / 'result.json').read_text())
        cls.reader = audit.module('reader', 'diagnose-capture-transient.py')
        cls.bank = audit.module('bank', 'simulate-compact-bank.py')
        cls.dc = audit.module('dc', 'report-compact-bank-16.py')

    def check(self, directory):
        return audit.audit_run(directory, LAYOUT, self.meta, self.reader, self.bank, self.dc)

    def test_retained_control(self):
        self.assertTrue(self.check(RUN)['capture_readout_pass'])

    def corrupted_summary(self, edit):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for path in RUN.iterdir():
                if path.name != 'result.json':
                    (directory / path.name).symlink_to(path.resolve(), target_is_directory=path.is_dir())
            result = deepcopy(self.result)
            edit(result)
            (directory / 'result.json').write_text(json.dumps(result))
            with self.assertRaises(AssertionError):
                self.check(directory)

    def test_fabricated_sample_rejected(self):
        self.corrupted_summary(lambda r: r['samples'][0]['values'].__setitem__('HOLD', 1.234))

    def test_missing_scan_rejected(self):
        self.corrupted_summary(lambda r: r['samples'].pop())

    def test_fabricated_reference_rejected(self):
        self.corrupted_summary(lambda r: r['capture_references'][0]['values'].__setitem__('HOLD', 1.234))

    def test_relabelled_accuracy_rejected(self):
        self.corrupted_summary(lambda r: r.__setitem__('max_total_capture_readout_error_V', 0))

    def test_all_intended_placements(self):
        for model in ['rc-far'] + ['rc-' + r['net'].lower() + '-far' for r in self.meta['shunt_approximations']]:
            with self.subTest(model=model):
                audit.check_variant(LAYOUT, self.meta, model)

    def test_unintended_circuit_changes_rejected(self):
        original = (LAYOUT / 'rc-bias-far.spice').read_text()
        resistor = next(line for line in original.splitlines() if line.startswith('R'))
        shunt = next(line for line in original.splitlines() if line.startswith('CFIX0 '))
        for altered in [original.replace(resistor + '\n', ''), original.replace(shunt, shunt.rsplit(' ', 1)[0] + ' 1e-15')]:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                (directory / 'rc-port.spice').write_bytes((LAYOUT / 'rc-port.spice').read_bytes())
                (directory / 'rc-bias-far.spice').write_text(altered)
                with self.assertRaises(AssertionError):
                    audit.check_variant(directory, self.meta, 'rc-bias-far')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layout', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    LAYOUT, RUN = args.layout.resolve(), args.run.resolve()
    unittest.main(argv=[__file__] + remaining)
