"""Analytical circuit and corruption controls for exact resistor reduction."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('compact', Path(__file__).with_name('compact-bank-resistors.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReductionTests(unittest.TestCase):
    def test_series_parallel_and_dangling(self):
        source = '.subckt bank A B\nR1 A n 2\nR2 n B 3\nR3 A B 5\nR4 n dangling 7\n.ends bank\n'
        target, removed = m.compact(source)
        _, _, edges = m.parse(target)
        self.assertEqual(len(edges), 1)
        self.assertAlmostEqual(edges[0][2], 1/2.5)
        m.audit(source, target, removed)

    def test_star_mesh_known_delta(self):
        source = '.subckt bank A B C\nR1 A n 3\nR2 B n 3\nR3 C n 3\n.ends bank\n'
        target, removed = m.compact(source)
        _, _, edges = m.parse(target)
        self.assertEqual(len(edges), 3)
        for _, _, conductance in edges:
            self.assertAlmostEqual(conductance, 1/9)
        m.audit(source, target, removed)

    def test_capacitor_and_device_terminals_protected(self):
        source = ('.subckt bank A B\nR1 A n 2\nR2 n B 3\nR3 A d 4\nR4 d B 4\n'
                  'C1 n B 1p\nX1 d B cap_mim_2f0_m4m5_noshield c_width=1u c_length=1u\n.ends bank\n')
        target, removed = m.compact(source)
        self.assertEqual(removed, [])
        m.audit(source, target, removed)

    def test_corrupted_serialized_resistor_rejected(self):
        source = '.subckt bank A B\nR1 A n 2\nR2 n B 3\n.ends bank\n'
        target, removed = m.compact(source)
        target = target.replace('REQ0 A B 5', 'REQ0 A B 6')
        with self.assertRaises(AssertionError):
            m.audit(source, target, removed)

    def test_changed_capacitor_rejected(self):
        source = '.subckt bank A B\nR1 A B 2\nC1 A B 1p\n.ends bank\n'
        target, removed = m.compact(source)
        with self.assertRaises(AssertionError):
            m.audit(source, target.replace('1p', '2p'), removed)


if __name__ == '__main__':
    unittest.main()
