"""Check bounded interpolation against NumPy and archived simulation results."""
import argparse
import importlib.util
import json
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bank=module('bank','simulate-compact-bank.py')
reader=module('reader','diagnose-capture-transient.py')


class SamplingTests(unittest.TestCase):
    def test_nonuniform_interpolation_and_endpoints_are_exact(self):
        rng=np.random.default_rng(321)
        times=np.cumsum(rng.uniform(1e-12,1e-6,600))
        data=np.column_stack([times,rng.normal(size=600),rng.normal(size=600)*1e6])
        sample=bank.trace_sampler({'time':0,'v(a)':1,'v(b)':2},data)
        points=np.concatenate([times,times[:-1]+np.diff(times)*.31,[-1,1]])
        for n,j in [('a',1),('b',2)]:
            expected=np.interp(points,times,data[:,j])
            np.testing.assert_array_equal([sample(n,float(t)) for t in points],expected)
        self.assertEqual(sample('0',float(times[0])),0.)

    def test_archived_capture_and_samples_are_exact(self):
        self.assertTrue(RUNS,'Pass at least one archived --run')
        for directory in RUNS:
            r=json.loads((directory/'result.json').read_text())
            self.assertTrue(r['completed'])
            ix,data=reader.trace(directory/'transient/stream.raw')
            at=bank.trace_sampler(ix,data)
            for name,value in r['capture_state'].items():self.assertEqual(at(name,.0014-1e-9),value)
            for sample in r['samples']:
                for name,value in sample['values'].items():self.assertEqual(at(name,sample['time_s']),value)
            for c,value in enumerate(r['storage_reset_window_change_V']):
                self.assertEqual(at(f'STORE{c}',.001405)-at(f'STORE{c}',.0014025),value)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True)
    args,rest=p.parse_known_args();RUNS=args.run
    unittest.main(argv=[__file__,*rest])
