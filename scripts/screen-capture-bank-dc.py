"""Isolate shared-bank DC behavior with all column inputs imposed equally.

This is a static bank diagnostic, not camera capture/readout qualification.
The full physical and ideal-wire models use the same physical MIM devices.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('trace',ROOT/'scripts/diagnose-capture-transient.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--temperatures',type=int,nargs='+',default=[27,125])
    p.add_argument('--levels',type=float,nargs='+',default=[1.2,1.6,2.0])
    p.add_argument('--timeout',type=float,default=60)
    p.add_argument('--solver',choices=['sparse','klu'],default='sparse')
    a=p.parse_args();bank=a.bank.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    meta=json.loads((bank/'verification.json').read_text());assert meta['columns']==64
    sources={name:(bank/(name+'.spice')).read_text() for name in ['rc-port','reference']}
    sources['reference']=sources['reference'].replace('.subckt reference ','.subckt bank ').replace('.ends reference','.ends bank')
    ports=re.search(r'(?m)^\.subckt bank (.*)',sources['rc-port'])[1].split()
    for name,source in sources.items():(out/(name+'.spice')).write_text(source)
    def node(n):return '0' if n=='GND' else n if n in ports else 'xbank.'+n
    def run(job):
        name,temp,level=job;d=out/f'{name}-{temp}-{level:g}';d.mkdir()
        deck=['Uniform-input static shared-bank diagnostic',
            '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
            '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
            '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical',
            f'.include {out}/{name}.spice',f'.temp {temp}',
            '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap',
            'Vsource RAW 0 3.3','Rsupply RAW VDD 2',
            'Rbias VDD BIAS 500k','Rpref PREF 0 12.4k','Cbias BIAS 0 1p','Cpref PREF 0 1p',
            'Bsc SC 0 I=(V(SC)-V(VDD))/100','Bscb SCB 0 I=V(SCB)/100',
            'Rload BUF 0 1T','Cload BUF 0 100p',
            'Xbank '+' '.join('0' if n=='GND' else n for n in ports)+' bank']
        for c in range(64):
            deck += [f'Vcol{c} COL{c} 0 {level:g}',
                     f'Bsel{c} SEL{c} 0 I=(V(SEL{c})-{1 if c==0 else 0}*V(VDD))/100',
                     f'Bselb{c} SELB{c} 0 I=(V(SELB{c})-{0 if c==0 else 1}*V(VDD))/100']
        saves=['v(VDD)','v(BIAS)','v(PREF)','v(BUF)','i(Vsource)']+[f'v({net}{c})' for c in range(64) for net in ['STORE','CBUF']]
        if name=='rc-port':
            saves += [f'v({node(n)})' for role in meta['roles'].values() for device in role.values() for n in device.values() if node(n)!='0']
        deck += ['.save '+' '.join(dict.fromkeys(saves)),'.control',
                 'unset klu' if a.solver=='sparse' else 'set klu','set num_threads=1','set filetype=binary',
                 'op','write op.raw','quit','.endc','.end']
        (d/'test.spice').write_text('\n'.join(deck)+'\n')
        start=time.monotonic();expired=False
        with (d/'ngspice.log').open('w') as log:
            try:
                proc=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,
                    env={**os.environ,'SPICE_USERINIT_DIR':str(out),'OMP_NUM_THREADS':'1'},timeout=a.timeout)
                code=proc.returncode
            except subprocess.TimeoutExpired:expired=True;code=None
        log=(d/'ngspice.log').read_text()
        errors=[l for l in log.splitlines() if re.search('aborted|^Error',l,re.I)]
        r=dict(model=name,temperature_C=temp,input_V=level,solver=a.solver,completed=False,
               timed_out=expired,returncode=code,errors=errors,seconds=time.monotonic()-start,
               deck_sha256=hashlib.sha256((d/'test.spice').read_bytes()).hexdigest())
        ix,data=trace.trace(d/'op.raw')
        if data is not None and len(data)==1 and np.isfinite(data).all() and not expired and code==0 and not errors:
            r['completed']=True;r['values']={n:float(data[0,j]) for n,j in ix.items()}
        (d/'result.json').write_text(json.dumps(r,indent=2)+'\n')
        print(json.dumps({key:r[key] for key in ['model','temperature_C','input_V','completed','seconds']}),flush=True)
        return r
    jobs=[(name,t,v) for t in a.temperatures for v in a.levels for name in sources]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,jobs))
    comparisons=[]
    lookup={(r['model'],r['temperature_C'],r['input_V']):r for r in results}
    for t in a.temperatures:
        for v in a.levels:
            physical=lookup['rc-port',t,v];ideal=lookup['reference',t,v]
            if not physical['completed'] or not ideal['completed']:continue
            pv,iv=physical['values'],ideal['values']
            shifts=[pv[f'v(cbuf{c})']-iv[f'v(cbuf{c})'] for c in range(64)]
            comparisons.append(dict(temperature_C=t,input_V=v,
                max_buffer_shift_V=max(map(abs,shifts)),buffer_shifts_V=shifts,
                physical_buffer_span_V=max(pv[f'v(cbuf{c})'] for c in range(64))-min(pv[f'v(cbuf{c})'] for c in range(64)),
                physical_supply_current_A=-pv['i(vsource)'],
                physical_bias_V=pv['v(bias)'],physical_pref_V=pv['v(pref)']))
    report=dict(scope=__doc__,results=results,comparisons=comparisons,
        all_completed=all(r['completed'] for r in results),accuracy_qualified=False,
        model_sha256={name:hashlib.sha256((out/(name+'.spice')).read_bytes()).hexdigest() for name in sources})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
