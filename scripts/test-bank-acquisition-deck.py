"""Check that the acquisition diagnostic changes only its intended timing."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('acq',ROOT/'scripts/probe-bank-acquisition.py')
acq=importlib.util.module_from_spec(spec);spec.loader.exec_module(acq)

class AcquisitionDeck(unittest.TestCase):
    source=Path('build/compact-bank-c64-ground-grid-far-read-20260927')
    out=Path('build/acquisition-deck-test')
    deck=(ROOT/source/'transient/test.spice').read_text()

    def test_only_include_and_acquisition_change(self):
        result=acq.transformed(self.deck,self.source,self.out)
        changes=[(a,b) for a,b in zip(self.deck.splitlines(),result.splitlines()) if a!=b]
        self.assertEqual(len(self.deck.splitlines()),len(result.splitlines()))
        self.assertEqual(len(changes),2)
        self.assertTrue(changes[0][0].startswith('.include '))
        self.assertTrue(changes[1][0].startswith('Vacq '))

    def test_acquisition_stays_before_reset_and_deselection(self):
        result=acq.transformed(self.deck,self.source,self.out)
        line,=[x for x in result.splitlines() if x.startswith('Vacq ')]
        numbers=list(map(float,line.split('PWL(')[1].rstrip(')').split()))
        pairs=list(zip(numbers[::2],numbers[1::2]))
        for offset,start in [(1,.00141),(5,.00267)]:
            self.assertAlmostEqual(pairs[offset][0],start+2e-6,places=15)
            self.assertAlmostEqual(pairs[offset+2][0],start+14e-6,places=15)
            self.assertLess(pairs[offset+3][0],start+15e-6)
            self.assertLess(start+15.01e-6,start+16e-6)
            self.assertEqual([v for _,v in pairs[offset:offset+4]],[0,3.3,3.3,0])

    def test_rejects_already_changed_or_wrong_source(self):
        altered=acq.transformed(self.deck,self.source,self.out)
        with self.assertRaises(AssertionError):acq.transformed(altered,self.out,Path('build/again'))
        with self.assertRaises(AssertionError):acq.transformed(self.deck,Path('build/wrong'),self.out)

if __name__=='__main__':unittest.main()
