"""Bounded 12 µs acquisition diagnostic from the audited 10 µs selected-read deck.

All device models, loads, controls and tolerances remain identical except ACQ's
falling edges, delayed 2 µs. Selection ends at +16 µs and reset starts at +15 µs;
sampling moves from +11.999 to +13.999 µs. This is not full-bank qualification.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def transformed(deck, source, out):
    old, = [x for x in deck.splitlines() if x.startswith('Vacq ')]
    values = list(map(float, old.split('PWL(')[1].rstrip(')').split()))
    pairs = list(zip(values[::2], values[1::2]))
    expected = [(0, 0)]
    for start in [.00141, .00267]:
        expected += [(start + 2e-6, 0), (start + 2.01e-6, 3.3), (start + 12e-6, 3.3), (start + 12.01e-6, 0)]
    assert np.allclose(pairs, expected, atol=1e-15, rtol=0)
    for i in [3, 4, 7, 8]:
        pairs[i] = (pairs[i][0] + 2e-6, pairs[i][1])
    new = 'Vacq ACQ 0 PWL(' + ' '.join(f'{t:.12g} {v:g}' for t, v in pairs) + ')'
    before = f'.include {source.resolve()}/tile.spice'
    assert deck.count(before) == 1
    return deck.replace(old, new).replace(before, f'.include {out.resolve()}/tile.spice')


def execute(directory, deck, out, timeout, dc=False):
    directory.mkdir(); (directory / 'test.spice').write_text(deck)
    start = time.monotonic()
    with (directory / 'ngspice.log').open('w') as log:
        try:
            process = subprocess.run(['ngspice', '-b', 'test.spice'], cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                timeout=timeout, env={**os.environ, 'SPICE_USERINIT_DIR': str(out.resolve()), 'OMP_NUM_THREADS': '1'})
            code, expired = process.returncode, False
        except subprocess.TimeoutExpired:
            code, expired = None, True
    errors = [x for x in (directory / 'ngspice.log').read_text().splitlines()
              if re.search(r'timestep too small|aborted|^Error|no such command', x, re.I)]
    result = dict(returncode=code, timed_out=expired, errors=errors, seconds=time.monotonic()-start)
    (directory / 'execution.json').write_text(json.dumps(result, indent=2)+'\n')
    assert code == 0 and not expired and not errors, str(directory)
    print('Completed ' + str(directory), flush=True)


def audit(source_report, out):
    probe = module('probe', 'probe-bank-readout.py')
    base = json.loads(source_report.read_text())
    assert base['independent_audit_completed'] and base['ground_return_grid']
    for name, digest in base['evidence_hashes'].items():
        assert probe.sha(ROOT/name) == digest, name
    source = ROOT/base['run']; layout=ROOT/base['layout']
    meta = json.loads((layout/'verification.json').read_text())
    deck=(out/'transient/test.spice').read_text()
    assert deck == transformed((source/'transient/test.spice').read_text(), Path(base['run']), out)
    assert (out/'tile.spice').read_bytes() == (source/'tile.spice').read_bytes()
    assert (out/'.spiceinit').read_bytes() == (source/'.spiceinit').read_bytes()
    reader=module('reader','diagnose-capture-transient.py'); bank=module('bank','simulate-compact-bank.py'); dc=module('dc','report-compact-bank-16.py')
    ix,data=reader.trace(out/'transient/stream.raw')
    assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    assert data[0,0]==0 and abs(data[-1,0]-.0027)<1e-12 and np.max(np.diff(data[:,0])) <=100.1e-9
    at=bank.trace_sampler(ix,data)
    refs={}
    for name,t,stores in [('capture',.0014-1e-9,False),('first',.00141+13.999e-6,True),('last',.00267+13.999e-6,True)]:
        directory=out/(name+'-reference')
        assert (directory/'test.spice').read_text()==probe.reference_deck(deck,meta,at,t,62,stores)
        refs[name]=dc.dc_values(directory/'op.raw')
        assert abs(refs[name]['v(adcin)']-refs[name]['v(hold)'])<1e-8
    for directory in [out/'transient']+[out/(x+'-reference') for x in refs]:
        ex=json.loads((directory/'execution.json').read_text());assert ex['returncode']==0 and not ex['timed_out'] and not ex['errors']
    samples=[]
    for scan,start in [('first',.00141),('last',.00267)]:
        t=start+13.999e-6
        assert at('ACQ',t)>3 and at('RSTADC',t)<.01 and at('SC',t)<.01 and at('ROW0',t)<.01
        assert at('SEL62',t)>3 and at('SELB62',t)<.01
        assert all(at(f'SEL{c}',t)<.01 and at(f'SELB{c}',t)>3 for c in range(64) if c!=62)
        samples.append(dict(scan=scan,time_s=t,column=62,hold_V=at('HOLD',t),total_error_uV=(at('HOLD',t)-refs['capture']['v(hold)'])*1e6,tracking_error_uV=(at('HOLD',t)-refs[scan]['v(hold)'])*1e6))
    old_ix,old_data=reader.trace(source/'transient/stream.raw'); old_at=bank.trace_sampler(old_ix,old_data)
    # Compare before the first modified edge, including the original first sample.
    nodes=[n[2:-1] for n in ix.keys() & old_ix.keys() if n.startswith('v(')]
    comparisons=[(abs(at(n,t)-old_at(n,t))*1e6,n,t) for n in nodes
                 for t in [.0014-1e-9,.0014025,.001405,.00141+11.999e-6]]
    prefix=max(comparisons)
    assert prefix[0]<10, prefix
    files=[p for p in out.rglob('*') if p.is_file() and p.name!='result.json']
    files += [source_report,Path(__file__),ROOT/'scripts/probe-bank-readout.py']
    result=dict(scope=__doc__,source_report=str(source_report),run=str(out),layout=base['layout'],columns=64,column_read=62,
        step_ns=100,temperature_C=27,acquisition_us=12,completed=True,independent_audit_completed=True,
        ground_return_grid=True,full_bank_accuracy_qualified=False,full_bank_readout_completed=False,
        samples=samples,references=refs,unchanged_prefix_max_uV=prefix[0],unchanged_prefix_worst_node=prefix[1],
        selected_capture_readout_pass=all(abs(s['total_error_uV'])<500 for s in samples),
        selected_tracking_pass=all(abs(s['tracking_error_uV'])<500 for s in samples),
        evidence_hashes={str(p.resolve().relative_to(ROOT)):probe.sha(p) for p in files})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-report',type=Path,default=Path('simulations/compact-bank-64-ground-grid-read.json'))
    p.add_argument('--out',type=Path,required=True);p.add_argument('--timeout',type=float,default=1800);p.add_argument('--audit-only',action='store_true')
    a=p.parse_args();probe=module('probe','probe-bank-readout.py')
    if not a.audit_only:
        assert not a.out.exists();base=json.loads(a.source_report.read_text())
        assert base['independent_audit_completed'] and base['ground_return_grid']
        for name,digest in base['evidence_hashes'].items(): assert probe.sha(ROOT/name)==digest,name
        source=ROOT/base['run'];a.out.mkdir(parents=True)
        for name in ['tile.spice','.spiceinit']:shutil.copyfile(source/name,a.out/name)
        (a.out/'runner.py').write_bytes(Path(__file__).read_bytes())
        deck=transformed((source/'transient/test.spice').read_text(),Path(base['run']),a.out)
        execute(a.out/'transient',deck,a.out,a.timeout)
        reader=module('reader','diagnose-capture-transient.py');bank=module('bank','simulate-compact-bank.py')
        ix,data=reader.trace(a.out/'transient/stream.raw');assert data is not None and np.isfinite(data).all() and abs(data[-1,0]-.0027)<1e-12
        at=bank.trace_sampler(ix,data);meta=json.loads((ROOT/base['layout']/'verification.json').read_text())
        for name,t,stores in [('capture',.0014-1e-9,False),('first',.00141+13.999e-6,True),('last',.00267+13.999e-6,True)]:
            execute(a.out/(name+'-reference'),probe.reference_deck(deck,meta,at,t,62,stores),a.out,a.timeout,True)
    result=audit(a.source_report,a.out)
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['samples','unchanged_prefix_max_uV','selected_capture_readout_pass','selected_tracking_pass']},indent=2))


if __name__=='__main__':main()
