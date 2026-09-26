"""Check bank readout timing independently of SPICE execution."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'bank', Path(__file__).with_name('simulate-compact-bank.py'))
bank = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bank)


class ReadoutScheduleTests(unittest.TestCase):
    def test_existing_two_column_times(self):
        slots, stop = bank.readout_schedule(2)
        self.assertEqual([(s, c) for s, c, _ in slots],
                         [('first', 0), ('first', 1), ('last', 0), ('last', 1)])
        for (_, _, actual), expected in zip(slots, [.00141, .00143, .00267, .00269]):
            self.assertAlmostEqual(actual, expected, places=14)
        self.assertAlmostEqual(stop, .00272, places=14)

    def test_every_size_has_two_complete_nonoverlapping_scans(self):
        for columns in range(2, 65):
            with self.subTest(columns=columns):
                slots, stop = bank.readout_schedule(columns)
                self.assertEqual([(s, c) for s, c, _ in slots],
                                 [(s, c) for s in ['first', 'last'] for c in range(columns)])
                for (_, _, start), (_, _, following) in zip(slots, slots[1:]):
                    # Selection ends at +16.01 us; ADC reset finishes at +15.01 us.
                    self.assertGreater(following - start, 16.01e-6)
                    self.assertGreaterEqual(following - start, 20e-6 - 1e-15)
                self.assertGreater(stop, slots[-1][2] + 16.01e-6)

    def test_full_bank_scan_boundary(self):
        slots, stop = bank.readout_schedule(64)
        self.assertAlmostEqual(slots[63][2], .00267, places=14)
        self.assertAlmostEqual(slots[64][2], .00269, places=14)
        self.assertAlmostEqual(stop, .00398, places=14)

    def test_unsupported_sizes(self):
        for columns in [0, 1, 65]:
            with self.assertRaises(ValueError):
                bank.readout_schedule(columns)


if __name__ == '__main__':
    unittest.main()
