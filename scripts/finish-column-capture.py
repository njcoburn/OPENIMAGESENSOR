"""Compute independent capture/output references for one completed strip run.

The transient is reused only after the simulator runner verifies the entire
normalized deck. This helper reconstructs its settings from the saved result.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', required=True)
p.add_argument('--run', required=True, help='Completed case directory')
p.add_argument('--output', required=True, help='New matched-reference run directory')
p.add_argument('--dc-workers', type=int, default=3)
p.add_argument('--op-us', type=float, default=200)
p.add_argument('--dc-timeout', type=float, default=600)
a = p.parse_args()
d = Path(a.run).resolve()
r = json.loads((d/'result.json').read_text())
assert r['completed'] and r['column_storage_pF'] and r['rows'] == 1
assert not Path(a.output).exists(), 'Preserve previous evidence; use a new output directory'

def run(script, args):
    subprocess.run([sys.executable, str(ROOT/'scripts'/script), *args], check=True)

reference = d/f'capture-dc-{a.op_us:g}us/reference.json'
assert not reference.parent.exists(), 'Compute fresh references for this invocation'
run('check-column-capture-reference.py', [
    '--source', a.source, '--run', str(d), '--op-us', str(a.op_us)])
args = ['--source', a.source, '--output', a.output,
        '--cases', r['case'], '--modes', r['mode'], '--fixture', r['fixture'],
        '--reuse-transients', str(d.parent), '--capture-reference', str(reference),
        '--dc-workers', str(a.dc_workers), '--dc-op-us', str(a.op_us),
        '--dc-timeout', str(a.dc_timeout)]
for flag, key in [('step-ns', 'step_ns'), ('method', 'method'),
                  ('slot-us', 'slot_us'), ('acquisition-us', 'acquisition_us'),
                  ('pref-ohm', 'pref_ohm'), ('bias-ohm', 'bias_ohm'),
                  ('read-delay-us', 'read_delay_us'), ('solver', 'solver'),
                  ('column-storage-pf', 'column_storage_pF'),
                  ('temperature', 'temperature_C'), ('capture-edge-ns', 'capture_edge_ns')]:
    args += ['--'+flag, str(r[key])]
for key in ['reltol', 'abstol', 'chgtol']:
    args += ['--'+key, str(r['tolerances'][key])]
# Omission of the default vntol is part of the exact original deck.
if ' vntol=' in (d/'transient/test.spice').read_text():
    args += ['--vntol', str(r['tolerances']['vntol'])]
if r.get('pivrel') is not None:
    args += ['--pivrel', str(r['pivrel'])]
for flag, key in [('reset-after-capture', 'reset_after_capture'),
                  ('seed-storage-op', 'seed_storage_op')]:
    if r.get(key):
        args += ['--'+flag]
run('simulate-array-strips.py', args)
run('analyze-strip-recovery.py', ['--source', a.source, a.output])
