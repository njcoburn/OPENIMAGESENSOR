"""Audit completed column fixtures, model hashes and stored sample records."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('diag',ROOT/'scripts/diagnose-capture-transient.py')
diag=importlib.util.module_from_spec(spec);spec.loader.exec_module(diag)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();root=a.run.resolve()
    report=json.loads((root/'report.json').read_text())
    results=json.loads((root/'transients.json').read_text())
    assert len(results)==48
    keys={(r['temperature_C'],r['input_V'],r['model'],r['step_ns']) for r in results}
    assert keys=={(t,l,n,s) for t in [27,125] for l in [1.2,1.6,2.0] for n in diag.NAMES for s in [100,50]}
    for name,digest in report['model_sha256'].items():
        assert hashlib.sha256((root/(name+'.spice')).read_bytes()).hexdigest()==digest
    reference_body=None;audit=[]
    for r in results:
        d=root/f"{r['temperature_C']}-{r['input_V']:g}"/f"{r['model']}-{r['step_ns']}"
        deck=(d/'test.spice').read_text();name=r['model']
        assert hashlib.sha256(deck.encode()).hexdigest()==r['deck_sha256']
        assert '\nunset klu\nset num_threads=1\n' in deck
        assert '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2' in deck
        assert f'.include {root}/{name}.spice' in deck
        normalized=deck.replace(f'.include {root}/{name}.spice','.include /MODEL')
        normalized=re.sub(r'(?m)^X'+name+r' (.*) '+name+'$',r'Xcolumn \1 MODEL',normalized)
        normalized=normalized.replace('_'+name,'_MODEL')
        normalized=re.sub(r'(?m)^\.temp .*','.temp TEMP',normalized)
        normalized=re.sub(r'(?m)^Vcol .*','Vcol COL 0 INPUT',normalized)
        normalized=re.sub(r'(?m)^\.tran .*','.tran STEP 2.7m 0 STEP',normalized)
        if reference_body is None:reference_body=normalized
        assert normalized==reference_body, d
        ix,data=diag.trace(d/'stream.raw')
        assert data is not None and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
        assert abs(data[-1,0]-.0027)<1e-12
        assert np.max(np.diff(data[:,0]))<=r['step_ns']*1e-9*1.001
        delta=0
        for slot,t in [('first',.0014215),('last',.0026815)]:
            for node,value in r['samples'][slot].items():
                actual=float(np.interp(t,data[:,0],data[:,ix[f'v({node}_{name})']]))
                delta=max(delta,abs(value-actual))
        assert delta==0
        audit.append(dict(run=str(d.relative_to(root)),points=len(data),max_step_s=float(np.max(np.diff(data[:,0]))),sample_recompute_difference_V=delta))
    references=[]
    for path in sorted(root.glob('*/*/reference-*us/test.spice')):
        text=path.read_text()
        assert 'Vsc CTLSC 0 1' in text and 'Vsel CTLSEL 0 1' in text
        assert 'Vacq ACQ 0 3.3' in text and 'Vreset RSTADC 0 0' in text
        assert 'PWL(' not in text
        log=path.with_name('ngspice.log').read_text()
        assert 'simulation(s) aborted' not in log
        references.append(dict(path=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            uses_transient_fallback='Transient op started' in log or 'transient op' in log.lower()))
    assert len(references)==36
    result=dict(all_48_fixtures_match_except_declared_model_temperature_input_step=True,
        all_traces_complete_finite_monotonic=True,samples_recomputed_exactly=True,
        max_steps_verified=True,runs=audit,references=references,
        reference_note='200/400 us are transient-assisted operating-point fallback limits; direct operating-point convergence does not exercise these durations.')
    (root/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['runs','references']}))


if __name__=='__main__':main()
