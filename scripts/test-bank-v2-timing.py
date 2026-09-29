"""Check v2 deck compatibility, selected-control reproduction and full timing."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

old=module('old','simulate-compact-bank.py');new=module('new','simulate-compact-bank-v2.py')

class Captured(Exception):pass

def normalize(deck):
    return re.sub(r'^\.include .*/tile\.spice$', '.include CANONICAL/tile.spice',deck,flags=re.M)

def generate(mod,layout,out,temperature=27,acquisition=10,selected=False):
    nc=json.loads((layout/'verification.json').read_text())['columns']
    argv=['bank','--layout',str(layout),'--out',str(out),'--lights-pa',','.join(map(str,[0,240]*(nc//2))),
          '--temperature',str(temperature),'--solver','klu','--step-ns','100','--transient-only']
    if mod is new:argv+=['--deck-only','--acquisition-us',str(acquisition)]
    schedule=mod.readout_schedule
    if selected:mod.readout_schedule=lambda n:([('first',62,.00141),('last',62,.00267)],.0027)
    try:
        with patch.object(sys,'argv',argv),patch.object(mod.subprocess,'Popen',side_effect=Captured):
            if mod is old:
                try:mod.main()
                except Captured:pass
                else:raise AssertionError('Original runner did not reach simulator boundary')
            else:mod.main()
    finally:mod.readout_schedule=schedule
    return (out/'transient/test.spice').read_text()

def waveform(deck,name):
    line,=[x for x in deck.splitlines() if x.startswith(name+' ')]
    values=np.array(list(map(float,line.split('PWL(')[1].rstrip(')').split()))).reshape(-1,2)
    assert np.all(np.diff(values[:,0])>0)
    return lambda t:float(np.interp(t,values[:,0],values[:,1]))

class Timing(unittest.TestCase):
    def test_default_decks_match_original(self):
        for nc,temp,layout in [(2,125,'compact-bank-c2-v1-20260926'),(16,27,'compact-bank-c16-ground8-20260927'),(64,27,'compact-bank-c64-ground-grid-20260927')]:
            with self.subTest(columns=nc):
                a=generate(old,ROOT/'build'/layout,OUT/f'old-{nc}',temp)
                b=generate(new,ROOT/'build'/layout,OUT/f'new-{nc}',temp)
                self.assertEqual(normalize(a),normalize(b))

    def test_selected_deck_matches_passing_archived_12us(self):
        deck=generate(new,ROOT/'build/compact-bank-c64-ground-grid-20260927',OUT/'selected12',acquisition=12,selected=True)
        archived=(ROOT/'build/compact-bank-c64-grid-acquisition12-v2-20260927/transient/test.spice').read_text()
        self.assertEqual(normalize(deck),normalize(archived))

    def test_full_deck_changes_only_acquisition(self):
        layout=ROOT/'build/compact-bank-c64-ground-grid-20260927'
        a=generate(new,layout,OUT/'full10',acquisition=10)
        b=generate(new,layout,OUT/'full12',acquisition=12)
        changes=[(x,y) for x,y in zip(normalize(a).splitlines(),normalize(b).splitlines()) if x!=y]
        self.assertEqual(len(changes),1);self.assertTrue(changes[0][0].startswith('Vacq '))
        acq=waveform(b,'Vacq');rst=waveform(b,'Vrst_adc');sels=[waveform(b,f'Vctl_SEL{c}') for c in range(64)]
        slots,stop=new.readout_schedule(64);self.assertEqual(len(slots),128);self.assertAlmostEqual(stop,.00398)
        self.assertEqual(len({(scan,c) for scan,c,t in slots}),128)
        for scan,c,t in slots:
            sample=t+13.999e-6
            self.assertEqual(acq(sample),3.3);self.assertEqual(rst(sample),0)
            self.assertEqual([sel(sample) for sel in sels],[float(i==c) for i in range(64)])
            self.assertEqual(acq(t+14.02e-6),0)
            self.assertEqual(rst(t+14.02e-6),0)
        self.assertFalse(json.loads((OUT/'full12/result.json').read_text())['electrical_accuracy_qualified'])

    def test_all_supported_widths_keep_windows_disjoint(self):
        for n in range(2,65):
            slots,stop=new.readout_schedule(n)
            for acq in [10,12]:
                end,fall,sample=new.acquisition_timing(acq)
                self.assertTrue(2.01e-6<sample<end<fall<15e-6<16e-6)
                self.assertTrue(all(b[2]-a[2]>16.01e-6 for a,b in zip(slots,slots[1:])))
                self.assertGreater(stop,slots[-1][2]+16.01e-6)
        with self.assertRaises(ValueError):new.acquisition_timing(14)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();OUT=a.out.resolve();OUT.mkdir(parents=True,exist_ok=False)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Timing);r=unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/'result.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),passed=r.wasSuccessful()),indent=2)+'\n')
    raise SystemExit(not r.wasSuccessful())
