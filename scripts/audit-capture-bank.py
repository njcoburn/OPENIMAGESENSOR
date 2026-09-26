"""Independently read back bank diagnostic models, fixtures and DC measurements."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('trace',ROOT/'scripts/diagnose-capture-transient.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank',type=Path,required=True)
    p.add_argument('--dc',type=Path,required=True)
    p.add_argument('--runs',type=Path,nargs='+',required=True)
    a=p.parse_args();bank=a.bank.resolve();meta=json.loads((bank/'verification.json').read_text())
    for name,digest in meta['hashes'].items():assert hashlib.sha256((bank/name).read_bytes()).hexdigest()==digest
    raw=re.sub(r'\n\+',' ',(bank/'raw-rc.spice').read_text())
    resistors=[l for l in raw.splitlines() if l.startswith('R')]
    for model in ['rc-port','rc-far']:
        text=(bank/(model+'.spice')).read_text()
        assert [l for l in text.splitlines() if l.startswith('R')]==resistors
        caps=[l.split() for l in text.splitlines() if l.startswith('C')]
        assert all(not r[3].startswith('-') for r in caps)
        assert all(r[2]!='0' for r in caps)
    report=json.loads((a.dc/'report.json').read_text())
    assert report['all_completed'] and len(report['results'])==16
    expected={(model,temp,level) for model in ['rc-port','reference'] for temp in [27,125] for level in [0,1.2,1.6,2.0]}
    assert {(r['model'],r['temperature_C'],r['input_V']) for r in report['results']}==expected
    for r in report['results']:
        d=a.dc/f"{r['model']}-{r['temperature_C']}-{r['input_V']:g}"
        assert hashlib.sha256((d/'test.spice').read_bytes()).hexdigest()==r['deck_sha256']
        ix,data=trace.trace(d/'op.raw');assert data.shape==(1,len(ix)) and np.isfinite(data).all()
        assert r['values']=={n:float(data[0,j]) for n,j in ix.items()}
        assert 'Transient op started' not in (d/'ngspice.log').read_text(), 'DC control used transient-assisted fallback'
    lookup={(r['model'],r['temperature_C'],r['input_V']):r['values'] for r in report['results']}
    for r in report['comparisons']:
        physical=lookup['rc-port',r['temperature_C'],r['input_V']]
        ideal=lookup['reference',r['temperature_C'],r['input_V']]
        shifts=[physical[f'v(cbuf{c})']-ideal[f'v(cbuf{c})'] for c in range(64)]
        assert shifts==r['buffer_shifts_V']
        assert max(map(abs,shifts))==r['max_buffer_shift_V']
    fixtures=[]
    for d in a.runs:
        r=json.loads((d/'result.json').read_text());deck=(d/'test.spice').read_text()
        for name,digest in r['source_sha256'].items():assert hashlib.sha256((d/name).read_bytes()).hexdigest()==digest
        original=(d/'original-fixture.spice').read_text()
        unchanged=[]
        for line in original.split('.save ',1)[0].splitlines():
            f=line.split()
            if not f or f[0] in ['.include','.temp'] or line in r['removed_fixture_elements']:continue
            unchanged.append(line);assert line in deck.splitlines(),(d,line)
        assert len(r['removed_fixture_elements'])==514
        assert '.options gmin=1e-17 abstol=1e-16 reltol=1e-06 chgtol=1e-18 trtol=1 method=trap' in deck
        assert hashlib.sha256((d/'bank.spice').read_bytes()).hexdigest()==meta['hashes'][r['model']+'.spice']
        assert sum(l.startswith('Xbank ') for l in deck.splitlines())==1
        assert not any(re.match(r'^(Xbias|Xholdn|Xholdp|Xstoreload|Xstorefollow|Xmuxn|Xmuxp|Cstore)\d+ ',l) for l in deck.splitlines())
        fixtures.append(dict(path=str(d),completed=r['completed'],unchanged_fixture_lines=len(unchanged)))
    result=dict(all_16_dc_results_read_back=True,direct_dc_without_transient_fallback=True,
                all_resistors_retained_in_both_placements=True,derived_capacitances_nonnegative=True,
                unchanged_coupled_source_load_timing_tolerances=True,coupled_fixtures=fixtures,
                full_readout_accuracy_qualified=False)
    (bank/'diagnostic-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
