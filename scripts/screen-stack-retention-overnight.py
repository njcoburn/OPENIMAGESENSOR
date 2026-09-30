"""Model-only extra-series-device screen at full-bank storage age and 13 us acquisition.

Use the separately DRC/LVS-checked two-column candidate extraction unchanged.
Only the ADC acquisition edge is extended; full-bank qualification remains open.
All references use the transformed model. Both timesteps get fresh references.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / 'build/compact-bank-c2-stack3-v3-20260930'

def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

bank = module('bank', 'simulate-compact-bank-v4.py')
reader = module('reader', 'diagnose-capture-transient.py')
probe = module('probe', 'probe-bank-readout.py')
dc = module('dc', 'report-compact-bank-16.py')

def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def stack_model(model, count, columns=2):
    assert count in (3,4,5) and columns==2
    meta=json.loads((LAYOUT/'verification.json').read_text())
    assert sha(LAYOUT/'rc-port.spice')==meta['hashes']['rc-port.spice']
    assert model==(LAYOUT/'rc-port.spice').read_text()
    mids=[n['extracted_node'] for path in meta['stack_paths'] for n in path['private_nodes']]
    altered=model;changes=[]
    for c in range(columns):
        old,=[l for l in model.splitlines() if len(l.split())>5 and l.split()[5]=='nfet_03v3' and re.fullmatch(rf'STORE{c}(?:\.t\d+)?',l.split()[3])]
        f=old.split();assert 'w=1u' in f and 'l=0.5u' in f
        if count==3:continue
        nodes=[f[1]]+[f'EXTRA_{c}_{i}' for i in range(count-3)]+[f[3]]
        new=[]
        for i in range(count-2):
            q=f.copy();q[0]=f[0] if i==0 else f'XEXTRA_{c}_{i}';q[1]=nodes[i];q[3]=nodes[i+1];new.append(' '.join(q))
        text='\n'.join(new);altered=altered.replace(old+'\n',text+'\n',1);changes.append(dict(old=old,new=text));mids.extend(nodes[1:-1])
    restored=altered
    for change in reversed(changes):restored=restored.replace(change['new']+'\n',change['old']+'\n',1)
    assert restored==model and len(mids)==columns*(count-1)
    return altered,changes,mids

def diagnostic_schedule(columns):
    assert columns==2
    return [(scan,c,start+c*20e-6) for scan,start in [('first',.00141),('last',.00393)] for c in range(2)],.00398
bank.readout_schedule=diagnostic_schedule

def extend_hold(deck):
    lines=[]
    for line in deck.splitlines():
        if line.startswith(('Vctl_SEL','Vacq ','Vrst_adc ')):
            line=re.sub(r'(?<![\w.])0\.00[23]\d+',lambda m:f'{float(m[0])+.00126:.12g}' if float(m[0])>=.00267 else m[0],line)
        if line.startswith('.tran '):line=line.replace('0.00272','0.00398')
        lines.append(line)
    return '\n'.join(lines)+'\n'

def timing_deck(deck, acquisition_us, mids):
    assert acquisition_us in (12.5,13)
    slots, _ = bank.readout_schedule(2)
    points = [(0, 0)]
    for _, _, start in slots:
        end = start + (2 + acquisition_us) * 1e-6
        assert end + .01e-6 < start + 15.5e-6
        points += [(start + 2e-6, 0), (start + 2.01e-6, 3.3), (end, 3.3), (end + .01e-6, 0)]
    acq = 'Vacq ACQ 0 PWL(' + ' '.join(f'{t:.12g} {v:g}' for t, v in points) + ')'
    old, = [l for l in deck.splitlines() if l.startswith('Vacq ')]
    if acquisition_us == 12: assert old == acq
    result = deck.replace(old, acq, 1)
    reset=[(0,3.3)]
    for _,_,start in slots:reset += [(start+1e-6,3.3),(start+1.01e-6,0),(start+15.5e-6,0),(start+15.51e-6,3.3)]
    oldreset,=[l for l in result.splitlines() if l.startswith('Vrst_adc ')]
    result=result.replace(oldreset,'Vrst_adc RSTADC 0 PWL('+' '.join(f'{t:.12g} {v:g}' for t,v in reset)+')',1)
    saved, = [l for l in result.splitlines() if l.startswith('.save ')]
    result = result.replace(saved, saved + ''.join(' v(xtile.' + n.lower() + ')' for n in mids), 1)
    return result

def execute(directory, root, is_dc=False):
    start = time.monotonic()
    with (directory / 'ngspice.log').open('w') as log:
        code = subprocess.run(['ngspice', '-b', 'test.spice'], cwd=directory, stdout=log,
                              stderr=subprocess.STDOUT, timeout=300,
                              env={**os.environ, 'SPICE_USERINIT_DIR': str(root), 'OMP_NUM_THREADS': '1'}).returncode
    errors = [l for l in (directory / 'ngspice.log').read_text().splitlines()
              if re.search(r'^Error|aborted|timestep too small|no such command', l, re.I)]
    ix, data = reader.trace(directory / ('op.raw' if is_dc else 'stream.raw'))
    assert code == 0 and not errors and data is not None and np.isfinite(data).all(), str(directory)
    if is_dc: assert len(data) == 1
    else: assert abs(data[0, 0]) < 1e-15 and abs(data[-1, 0] - .00398) < 1e-12 and np.all(np.diff(data[:, 0]) > 0)
    save(directory / 'execution.json', dict(returncode=code, errors=errors, seconds=time.monotonic()-start, points=len(data)))
    return ix, data

def read_run(dest, meta, step, acquisition, references=True):
    ix, data = reader.trace(dest / 'transient/stream.raw')
    assert np.isfinite(data).all() and abs(data[-1, 0] - .00398) < 1e-12
    assert np.all(np.diff(data[:, 0]) > 0) and np.max(np.diff(data[:, 0])) <= step * 1e-9 * 1.001
    at = bank.trace_sampler(ix, data)
    deck = (dest / 'transient/test.spice').read_text()
    samples = []; captures = []
    for c in range(2):
        path = dest / f'capture{c}-reference'
        expected = probe.reference_deck(deck, meta, at, .0014 - 1e-9, c, False)
        if references:
            path.mkdir(); (path / 'test.spice').write_text(expected); execute(path, dest, True)
        assert (path / 'test.spice').read_text() == expected
        captures.append(dc.dc_values(path / 'op.raw'))
    for slot, c, start in bank.readout_schedule(2)[0]:
        t = start + (2 + acquisition) * 1e-6 - 1e-9
        values = {n: float(np.interp(t, data[:, 0], data[:, i])) for n, i in ix.items() if n != 'time'}
        for n in ['sc', 'row0', 'rstadc', f'selb{c}', f'sel{1-c}']: assert values[f'v({n})'] < .01
        for n in ['scb', 'rst0', 'acq', f'sel{c}', f'selb{1-c}']: assert values[f'v({n})'] > 3
        path = dest / f'{slot}{c}-output-reference'
        expected = probe.reference_deck(deck, meta, at, t, c, True)
        if references:
            path.mkdir(); (path / 'test.spice').write_text(expected); execute(path, dest, True)
        assert (path / 'test.spice').read_text() == expected
        ref = dc.dc_values(path / 'op.raw')
        assert abs(ref['v(hold)'] - ref['v(adcin)']) < 1e-8
        samples.append(dict(slot=slot, column=c, time_s=t, values=values,
                            total_error_uV=(values['v(hold)'] - captures[c]['v(hold)']) * 1e6,
                            tracking_error_uV=(values['v(hold)'] - ref['v(hold)']) * 1e6))
    events = [{n: float(np.interp(t, data[:, 0], data[:, i])) for n, i in ix.items() if n != 'time'}
              for t in [.0014-1e-9, .001402-1e-9, .0014025, .001405]]
    return dict(samples=samples, events=events, capture_hold_V=[r['v(hold)'] for r in captures])

def run_one(out, count, corner, acquisition, step):
    name = f'stack{count}-{corner}-acq{acquisition:g}-{step}'
    dest = out / name
    command = [sys.executable, str(ROOT/'scripts/simulate-compact-bank-v4.py'), '--layout', str(LAYOUT), '--out', str(dest),
               '--lights-pa', '240,0', '--temperature', '125', '--step-ns', str(step), '--solver', 'klu',
               '--mos-corner', corner, '--acquisition-us', '12', '--save-mim-terminals', '--deck-only']
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
    parent = (dest/'tile.spice').read_text(); deck = (dest/'transient/test.spice').read_text()
    (dest/'parent-tile.spice').write_text(parent); (dest/'parent-deck.spice').write_text(deck)
    model, changes, mids = stack_model(parent, count)
    (dest/'tile.spice').write_text(model)
    (dest/'transient/test.spice').write_text(timing_deck(extend_hold(deck), acquisition, mids))
    save(dest/'transformation.json', dict(series_devices=count, acquisition_us=acquisition, changes=changes, added_nodes=mids,
                                         model_only=True, physical_layout_changed=False, parent_layout=str(LAYOUT.relative_to(ROOT))))
    execute(dest/'transient', dest)
    meta = json.loads((LAYOUT/'verification.json').read_text())
    result = read_run(dest, meta, step, acquisition)
    # Retained physical controls must reproduce both fixture and measured errors.
    regression = None
    if count == 1 and acquisition == 12 and corner in ('ss', 'ff'):
        retained = ROOT/f'build/compact-bank-process-control-20260930/c2-{corner}-{step}'
        old = json.loads((retained/'result.json').read_text())
        assert (retained/'tile.spice').read_text() == model
        original_deck = (retained/'transient/test.spice').read_text().replace(str(retained), str(dest))
        assert original_deck == (dest/'transient/test.spice').read_text()
        regression = max(abs(s['values']['v(hold)'] - o['values']['HOLD']) * 1e6 for s, o in zip(result['samples'], old['samples']))
        assert regression < .001
    result.update(name=name, series_devices=count, corner=corner, acquisition_us=acquisition, step_ns=step,
                  model_only=True, physical_layout_changed=False, full_bank_accuracy_qualified=False, retained_control_max_hold_difference_uV=regression)
    save(dest/'candidate-result.json', result)
    print('Completed ' + name, flush=True)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--out', type=Path, required=True); p.add_argument('--audit', action='store_true'); a = p.parse_args()
    out = a.out.resolve(); meta = json.loads((LAYOUT/'verification.json').read_text())
    if a.audit:
        report = json.loads((out/'result.json').read_text())
        for name, digest in report['evidence_hashes'].items(): assert sha(ROOT/name) == digest, name
        for pair in report['cases']:
            for name in pair['runs']:
                dest=out/name; old=json.loads((dest/'candidate-result.json').read_text())
                model, changes, mids=stack_model((dest/'parent-tile.spice').read_text(), old['series_devices'])
                assert model == (dest/'tile.spice').read_text()
                assert timing_deck(extend_hold((dest/'parent-deck.spice').read_text()),old['acquisition_us'],mids)==(dest/'transient/test.spice').read_text()
                actual=read_run(dest,meta,old['step_ns'],old['acquisition_us'],False)
                assert all(actual[k]==old[k] for k in actual)
        print(f"Verified {len(report['evidence_hashes'])} hashes and all {2*len(report['cases'])} raw traces/references."); return
    out.mkdir(parents=True, exist_ok=False)
    (out/'screen-runner.py').write_bytes(Path(__file__).read_bytes())
    jobs=[(n,c,13) for n in [3,4,5] for c in ['ss','ff']]
    results={}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_one,out,n,c,acq,step) for n,c,acq in jobs for step in [100,50]]
        for f in futures:
            r=f.result(); results[r['name']]=r
    pairs=[]
    for n,c,acq in jobs:
        names=[f'stack{n}-{c}-acq{acq:g}-{s}' for s in [100,50]]; coarse,fine=[results[name] for name in names]
        sample_delta=max(abs(s['values'][v]-t['values'][v])*1e6 for s,t in zip(coarse['samples'],fine['samples']) for v in s['values'])
        event_delta=max(abs(s[v]-t[v])*1e6 for s,t in zip(coarse['events'],fine['events']) for v in s)
        error_delta=max(abs(s[k]-t[k]) for s,t in zip(coarse['samples'],fine['samples']) for k in ['total_error_uV','tracking_error_uV'])
        total=max(abs(s['total_error_uV']) for r in [coarse,fine] for s in r['samples'])
        tracking=max(abs(s['tracking_error_uV']) for r in [coarse,fine] for s in r['samples'])
        contrast=all(r['samples'][i+1]['values']['v(hold)']>r['samples'][i]['values']['v(hold)'] for r in [coarse,fine] for i in [0,2])
        checks=dict(total_error=total<500,output_tracking=tracking<500,sample_refinement=sample_delta<10,event_refinement=event_delta<10,error_refinement=error_delta<10,contrast=contrast)
        pairs.append(dict(series_devices=n,corner=c,acquisition_us=acq,runs=names,max_total_error_uV=total,max_tracking_error_uV=tracking,
                          sample_refinement_uV=sample_delta,event_refinement_uV=event_delta,error_refinement_uV=error_delta,checks=checks,selected_screen_pass=all(checks.values())))
    dependencies=[Path(__file__),LAYOUT/'rc-port.spice',LAYOUT/'verification.json',LAYOUT/'bank.gds']+[ROOT/'scripts'/n for n in ['simulate-compact-bank-v4.py','bank-process-common.py','diagnose-capture-transient.py','probe-bank-readout.py','report-compact-bank-16.py']]
    files=[p for p in out.rglob('*') if p.is_file()]+dependencies
    report=dict(scope=__doc__,cases=pairs,transients=12,references=72,temperature_C=125,lights_pA=[240,0],parent_layout=str(LAYOUT.relative_to(ROOT)),
                model_only=True,physical_layout_changed=False,full_bank_accuracy_qualified=False,full_chip_qualified=False,
                limits=['Extracted two-column candidate only; 64-column timing remains untested.', 'Candidate column and small bank have separate DRC/LVS; full-chip manufacturing checks remain open.', 'MOS corners only; diode/MIM remain typical, supply 3.3 V and wires nominal.'],
                evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in files})
    save(out/'result.json',report)
    print(json.dumps(pairs,indent=2))

if __name__=='__main__': main()
