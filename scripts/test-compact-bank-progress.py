"""Check that partial or buffered SPICE data cannot become false progress."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('bank',Path(__file__).with_name('simulate-compact-bank.py'))
bank=importlib.util.module_from_spec(spec);spec.loader.exec_module(bank)


class ProgressTests(unittest.TestCase):
    def test_only_complete_real_records_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'trace.raw'
            self.assertIsNone(bank.saved_progress(p))
            header=b'Title: test\nFlags: real\nVariables:\n\t0\ttime\ttime\n\t1\tv(out)\tvoltage\nBinary:\n'
            p.write_bytes(header[:-3]);self.assertIsNone(bank.saved_progress(p))
            p.write_bytes(header);self.assertIsNone(bank.saved_progress(p))
            p.write_bytes(header+struct.pack('dd',.001,2)+struct.pack('d',.002))
            self.assertEqual(bank.saved_progress(p),.001)
            p.write_bytes(p.read_bytes()+struct.pack('d',3))
            self.assertEqual(bank.saved_progress(p),.002)

    def test_non_time_vector_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'op.raw'
            p.write_bytes(b'Flags: real\nVariables:\n\t0\tv(out)\tvoltage\nBinary:\n'+struct.pack('d',2))
            with self.assertRaises(AssertionError):bank.saved_progress(p)


if __name__=='__main__':unittest.main()
