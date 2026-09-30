"""Reject missing devices, shorted private nodes, wrong gates and extra branches."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stack',ROOT/'scripts/capture-stack-connectivity.py')
stack=importlib.util.module_from_spec(spec);spec.loader.exec_module(stack)
body=(ROOT/'circuits/capture-column-stack3.spice').read_text().split('.subckt capture_column ',1)[1].split('.ends',1)[0]
PORTS=body.splitlines()[0].split()
RECORDS=[line.split() for line in body.splitlines() if line.startswith('X')]
class StackTests(unittest.TestCase):
    def verify(self,records,aliases=None):
        aliases=aliases or {}
        return stack.identify(records,lambda n:aliases.get(n,n),{n:n for n in PORTS})
    def test_expected_path(self):
        result=self.verify(RECORDS)
        self.assertEqual(result[0]['instances'],['Xholdn','Xholdn2','Xholdn3'])
    def test_missing_device(self):
        with self.assertRaises(ValueError):self.verify([r for r in RECORDS if r[0]!='Xholdn2'])
    def test_shorted_private_node(self):
        with self.assertRaises(AssertionError):self.verify(RECORDS,{'HN1':'STORE'})
    def test_wrong_gate(self):
        records=copy.deepcopy(RECORDS);next(r for r in records if r[0]=='Xholdn2')[2]='SCB'
        with self.assertRaises(ValueError):self.verify(records)
    def test_extra_branch(self):
        records=copy.deepcopy(RECORDS);branch=next(r for r in records if r[0]=='Xholdn2').copy();branch[0]='Xextra';records.append(branch)
        with self.assertRaises(ValueError):self.verify(records)
    def test_wrong_size(self):
        records=copy.deepcopy(RECORDS);r=next(r for r in records if r[0]=='Xholdn2');r[r.index('w=1u')]='w=2u'
        with self.assertRaises(AssertionError):self.verify(records)
if __name__=='__main__':unittest.main()
