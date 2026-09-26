"""Couple the extracted row to the physical shared bank in the retained fixture.

This records transient completion and terminal measurements only. Independent
capture/output references and timestep/placement comparisons are separate gates.
Row-to-bank terminal links are ideal; no physical row/bank joining wires exist.
"""
from pathlib import Path
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
    p.add_argument('--model',choices=['rc-port','rc-far','reference'],default='rc-port')
    p.add_argument('--temperature',type=float,default=27)
    p.add_argument('--step-ns',type=float,default=200)
    p.add_argument('--stop-ms',type=float,default=2.7)
    p.add_argument('--timeout',type=float,default=600)
    p.add_argument('--solver',choices=['sparse','klu'],default='sparse')
    p.add_argument('--method',choices=['trap','gear'],default='trap',
                   help='Integration-method diagnostic; accuracy tolerances are unchanged.')
    p.add_argument('--op-only',action='store_true')
    p.add_argument('--equivalent-bank-model',type=Path,
                   help='Use an audited deterministic degree-4 resistor-only reduction of the selected bank model.')
    p.add_argument('--seed-bank-dc',type=Path,
                   help='Use a completed zero-input bank DC result and prior row initial state as Newton nodesets; equations are unchanged.')
    a=p.parse_args();assert a.step_ns>0 and a.timeout>0 and 0<a.stop_ms<=2.7
    bank=a.bank.resolve();meta=json.loads((bank/'verification.json').read_text())
    assert meta['columns']==64 and meta['direct_and_resistor_collapsed_lvs']
    assert meta['magic_drc_errors']==meta['klayout_main_drc_errors']==0
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'trace-reader.py').write_bytes((ROOT/'scripts/diagnose-capture-transient.py').read_bytes())
    fixture=ROOT/'build/grid-readout-20260924/27-100/r1c64-rc-port'
    original=(fixture/'transient/test.spice').read_text()
    (out/'original-fixture.spice').write_text(original)
    for name in ['array.spice','buffer.spice']:(out/name).write_bytes((fixture/name).read_bytes())
    bank_text=(bank/(a.model+'.spice')).read_text()
    equivalent_audit=None
    if a.equivalent_bank_model:
        assert a.model in ['rc-port','rc-far'] and not a.seed_bank_dc
        compact_spec=importlib.util.spec_from_file_location('compact',ROOT/'scripts/compact-bank-resistors.py')
        compact=importlib.util.module_from_spec(compact_spec);compact_spec.loader.exec_module(compact)
        equivalent_audit=compact.verify_files(bank/(a.model+'.spice'),a.equivalent_bank_model)
        equivalent_audit['source_sha256']=compact.digest(bank/(a.model+'.spice'))
        equivalent_audit['model_sha256']=compact.digest(a.equivalent_bank_model)
        (out/'equivalent-model-audit.json').write_text(json.dumps(equivalent_audit,indent=2)+'\n')
        (out/'compact-runner.py').write_bytes((ROOT/'scripts/compact-bank-resistors.py').read_bytes())
        bank_text=a.equivalent_bank_model.read_text()
    if a.model=='reference': bank_text=bank_text.replace('.subckt reference ','.subckt bank ').replace('.ends reference','.ends bank')
    (out/'bank.spice').write_text(bank_text)
    ports=re.search(r'(?m)^\.subckt bank (.*)',bank_text)[1].split()
    lines=[];removed=[]
    for line in original.split('.save ',1)[0].splitlines():
        f=line.split()
        if not f:continue
        if f[0] in ['Xref','Xstorage_ref'] or re.fullmatch(r'(Xbias|Xholdn|Xholdp|Xstoreload|Xstorefollow|Xmuxn|Xmuxp|Cstore)\d+',f[0]):
            removed.append(line);continue
        if f[0]=='.include' and Path(f[1]).name in ['array.spice','buffer.spice']:
            line='.include '+str(out/Path(f[1]).name)
        if f[0]=='.temp':line=f'.temp {a.temperature:g}'
        if f[0]=='.options':line=re.sub(r'method=\w+','method='+a.method,line)
        lines.append(line)
    assert len(removed)==514
    lines += ['.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical',
              f'.include {out}/bank.spice','Xbank '+' '.join('0' if n=='GND' else n for n in ports)+' bank']
    saves=re.search(r'(?m)^\.save (.*)',original)[1].split()
    def banknode(n):return '0' if n=='GND' else n if n in ports else 'xbank.'+n
    if a.model!='reference':
        saves += [f'v({banknode(n)})' for role in meta['roles'].values() for device in role.values() for n in device.values()]
    saves += [f'v(SELB{c})' for c in range(64)]
    saves=list(dict.fromkeys(s.lower() for s in saves if s!='v(0)'))
    if a.seed_bank_dc:
        seedpath=a.seed_bank_dc.resolve()
        seed=json.loads(seedpath.read_text())
        assert seed['completed'] and seed['model']==a.model=='rc-port'
        assert seed['input_V']==0 and seed['temperature_C']==a.temperature
        screen=json.loads((seedpath.parent.parent/'report.json').read_text())
        assert screen['model_sha256'][a.model]==hashlib.sha256((out/'bank.spice').read_bytes()).hexdigest()
        prior_trace=fixture/'transient/stream.raw'
        oldix,olddata=trace.trace(prior_trace)
        assert olddata is not None and olddata[0,oldix['time']]==0
        seeds={n:v for n,v in seed['values'].items() if n.startswith('v(')}
        # The old row's saved external controls reflect reset/unselected state.
        # Keep new bank-internal values but prefer old row/external nodes.
        seeds.update({n:float(olddata[0,j]) for n,j in oldix.items() if n.startswith('v(')})
        assert all(np.isfinite(v) for v in seeds.values())
        seed_record=dict(values=seeds,bank_dc_sha256=hashlib.sha256(seedpath.read_bytes()).hexdigest(),
                         row_trace_sha256=hashlib.sha256(prior_trace.read_bytes()).hexdigest(),
                         scope='Newton initial guesses only; no UIC, imposed initial conditions or altered circuit equations.')
        (out/'nodesets.json').write_text(json.dumps(seed_record,indent=2)+'\n')
        for n,v in seeds.items():lines.append(f'.nodeset {n}={v:.17g}')
    lines.append('.save '+' '.join(saves))
    if not a.op_only:lines.append(f'.tran {a.step_ns:g}n {a.stop_ms:g}m 0 {a.step_ns:g}n')
    lines += ['.control','unset klu' if a.solver=='sparse' else 'set klu','set num_threads=1','set filetype=binary']
    lines += ['op','write op.raw'] if a.op_only else ['run stream.raw']
    lines += ['quit','.endc','.end']
    (out/'test.spice').write_text('\n'.join(lines)+'\n')
    (out/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    record=dict(scope=__doc__,bank_source=str(bank),model=a.model,
        temperature_C=a.temperature,step_ns=a.step_ns,stop_ms=a.stop_ms,
        solver=a.solver,
        method=a.method,
        op_only=a.op_only,completed=False,accuracy_qualified=False,
        nodeset_initial_guesses=bool(a.seed_bank_dc),
        equivalent_resistor_model=equivalent_audit,
        removed_fixture_elements=removed,
        source_sha256={name:hashlib.sha256((out/name).read_bytes()).hexdigest()
            for name in ['test.spice','array.spice','bank.spice','buffer.spice','original-fixture.spice']})
    (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    start=time.monotonic();timedout=False
    with (out/'ngspice.log').open('w') as log:
        try:
            result=subprocess.run(['ngspice','-b','test.spice'],cwd=out,stdout=log,stderr=subprocess.STDOUT,
                env={**os.environ,'SPICE_USERINIT_DIR':str(out),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},timeout=a.timeout)
            returncode=result.returncode
        except subprocess.TimeoutExpired:timedout=True;returncode=None
    log=(out/'ngspice.log').read_text()
    errors=[l for l in log.splitlines() if re.search(r'timestep too small|aborted|^Error',l,re.I)]
    record.update(seconds=time.monotonic()-start,timed_out=timedout,returncode=returncode,errors=errors,
                  warnings=[l for l in log.splitlines() if 'Warning:' in l])
    ix,data=trace.trace(out/('op.raw' if a.op_only else 'stream.raw'))
    if data is not None and len(data):
        finite=bool(np.isfinite(data).all())
        record.update(points=len(data),finite=finite)
        record['completed']=not timedout and returncode==0 and not errors and finite
        if a.op_only:
            record['completed'] &= len(data)==1
            record['dc']={name:float(data[0,j]) for name,j in ix.items()}
        else:
            times=data[:,ix['time']]
            record['last_time_s']=float(times[-1])
            record['completed'] &= bool(np.all(np.diff(times)>0) and times[-1]>=a.stop_ms*1e-3-1e-12)
            def wave(n):return np.zeros(len(data)) if n=='0' else data[:,ix[f'v({n.lower()})']]
            def at(n,t):return float(np.interp(t,times,wave(n)))
            samples=[]
            for c in range(64):
                t=.00141+c*.00002+.000012-1e-9
                if t>times[-1]:continue
                sample=dict(column=c,time_s=t,hold_V=at('HOLD',t),storage_V=at(f'STORE{c}',t),
                    sc_V=at('SC',t),scb_V=at('SCB',t),sel_V=at(f'SEL{c}',t),selb_V=at(f'SELB{c}',t))
                samples.append(sample)
            record['samples']=samples
            if a.model!='reference':
                record['local_bank_measurements']={}
                for c,role in meta['roles'].items():
                    vdd=wave(banknode(role['follower']['body']))
                    gnd=wave(banknode(role['follower']['drain']))
                    record['local_bank_measurements'][c]=dict(
                        max_vdd_drop_V=float(np.max(wave('VDD')-vdd)),
                        max_ground_rise_V=float(np.max(gnd)),
                        min_local_supply_V=float(np.min(vdd-gnd)))
    (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({key:record[key] for key in ['completed','seconds','timed_out','errors','points','last_time_s'] if key in record}),flush=True)
    if not record['completed']:raise SystemExit(1)


if __name__=='__main__':main()
