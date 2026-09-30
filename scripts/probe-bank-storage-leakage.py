"""Measure DC storage-terminal currents with auditable zero-volt series probes.

The source is a retained matched-state output reference. Circuit devices, values,
models, tolerances and frozen states are unchanged; three zero-volt probes and
current saves are added. This is a diagnostic, not a corrected layout or pass.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def instrument(model,column):
    lines=model.splitlines();records=[];modified=[]
    for line in lines:
        f=line.split()
        if f and f[0].startswith('X') and len(f)>5 and f[5] in ['nfet_03v3','pfet_03v3']:
            hits=[i for i in range(1,5) if re.fullmatch(rf'STORE{column}(?:\..*)?',f[i])]
            if hits:
                assert len(hits)==1
                pin=hits[0]
                if pin==2:role='follower_gate';assert f[5]=='pfet_03v3'
                else:assert pin==3;role='hold_n' if f[5]=='nfet_03v3' else 'hold_p'
                assert not any(r['role']==role for r in records)
                old=f[pin];probe='VDIAG_'+role;node='DIAG_'+role
                assert node not in model and probe not in model
                f[pin]=node;new=' '.join(f)
                records.append(dict(role=role,instance=f[0],pin_index=pin,store_terminal=old,probe=probe,new_node=node,original=line,replacement=new))
                line=new
        if line.startswith('.ends'):
            modified.extend(f'{r["probe"]} {r["new_node"]} {r["store_terminal"]} 0' for r in records)
        modified.append(line)
    assert {r['role'] for r in records}=={'hold_n','hold_p','follower_gate'}
    text='\n'.join(modified)+'\n';reconstructed=text
    for r in records:
        reconstructed=reconstructed.replace(r['replacement']+'\n',r['original']+'\n',1)
        reconstructed=reconstructed.replace(f'{r["probe"]} {r["new_node"]} {r["store_terminal"]} 0\n','',1)
    assert reconstructed==model, 'Probe inversion must reproduce exact model bytes'
    return text,records

def probe(out,report_path,column,scan,timeout):
    report=json.loads(report_path.read_text());run=ROOT/report['runs'][0]['run'];r=json.loads((run/'result.json').read_text())
    corner=r.get('mos_corner','typical');name=f'{corner}-{scan}{column}';dest=out/name;dest.mkdir()
    source=run/f'{scan}{column}-output-reference';model=(run/'tile.spice').read_text();deck=(source/'test.spice').read_text()
    for p in [run/'result.json',run/'tile.spice',source/'test.spice',source/'op.raw']:
        assert sha(p)==report['evidence_hashes'][str(p.relative_to(ROOT))]
    transformed,records=instrument(model,column);(dest/'tile.spice').write_text(transformed)
    old_include=f'.include {run}/tile.spice';assert deck.count(old_include)==1
    deck=deck.replace(old_include,f'.include {dest}/tile.spice')
    save,=[line for line in deck.splitlines() if line.startswith('.save ')]
    currents=[f'i(v.xtile.{r["probe"].lower()})' for r in records]
    deck=deck.replace(save,save+' '+' '.join(currents))
    (dest/'test.spice').write_text(deck);shutil.copyfile(run/'.spiceinit',dest/'.spiceinit')
    start=time.monotonic();expired=False
    with (dest/'ngspice.log').open('w') as log:
        try:code=subprocess.run(['ngspice','-b','test.spice'],cwd=dest,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,
                                env={**os.environ,'SPICE_USERINIT_DIR':str(dest),'OMP_NUM_THREADS':'1'}).returncode
        except subprocess.TimeoutExpired:code=None;expired=True
    errors=[line for line in (dest/'ngspice.log').read_text().splitlines() if re.search(r'^Error|aborted|timestep too small|no such|not found',line,re.I)]
    execution=dict(returncode=code,timed_out=expired,errors=errors,seconds=time.monotonic()-start,deck_sha256=sha(dest/'test.spice'))
    (dest/'execution.json').write_text(json.dumps(execution,indent=2)+'\n');assert code==0 and not expired and not errors,name
    dc=module('dc','report-compact-bank-16.py');old=dc.dc_values(source/'op.raw');new=dc.dc_values(dest/'op.raw')
    voltage_difference=max(abs(new[n]-v) for n,v in old.items() if n.startswith('v('))
    assert voltage_difference<1e-6, 'Instrumenting changed a DC voltage by >=1 uV'
    branch={record['role']:-new[current]*1e12 for record,current in zip(records,currents)}
    sample=next(s for s in r['samples'] if s['column']==column and s['slot']==scan)
    clamp_supply=(sample['values'][f'STORE{column}']-new[f'v(store{column})'])*1e12
    kcl=abs(sum(branch.values())-clamp_supply);assert kcl<.25,(name,branch,clamp_supply,kcl)
    result=dict(mos_corner=corner,column=column,scan=scan,source_report=str(report_path.relative_to(ROOT)),source_reference=str(source.relative_to(ROOT)),
                probes=records,voltage_equivalence_max_uV=voltage_difference*1e6,device_current_leaving_store_pA=branch,
                net_current_leaving_store_pA=sum(branch.values()),clamp_supply_pA=clamp_supply,kcl_residual_pA=kcl,
                execution=execution,diagnostic_only=True,full_bank_accuracy_qualified=False,full_chip_qualified=False)
    (dest/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,branch,'KCL pA',kcl,flush=True)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--timeout',type=float,default=300);p.add_argument('--test-only',action='store_true');a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);(out/'runner.py').write_bytes(Path(__file__).read_bytes())
    model=(ROOT/'build/compact-bank-c64-ground-grid-20260927/rc-port.spice').read_text()
    for column in range(64):instrument(model,column)
    try:instrument(model,64)
    except AssertionError:pass
    else:raise AssertionError('Invalid column accepted')
    if a.test_only:
        (out/'result.json').write_text(json.dumps(dict(transform_controls_pass=True,columns=64,invalid_column_rejected=True))+'\n');print('64 exact model reconstructions passed; invalid column rejected');return
    tt=ROOT/'simulations/compact-bank-64-full-hot.json';ss=ROOT/'simulations/compact-bank-process-ss-inverse125-20260930-ssff.json';ff=ROOT/'simulations/compact-bank-process-ff-inverse125-20260930-ssff.json'
    jobs=[(tt,63,'last'),(ss,63,'last'),(ff,63,'last'),(ff,63,'first'),(ff,0,'last')]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(probe,out,*j,a.timeout) for j in jobs];results=[f.result() for f in futures]
    files=[p for p in out.rglob('*') if p.is_file()]+[tt,ss,ff,Path(__file__),ROOT/'scripts/report-compact-bank-16.py']
    result=dict(scope=__doc__,transform_controls_pass=True,cases=results,evidence_hashes={str(p.resolve().relative_to(ROOT)):sha(p) for p in files},
                current_sign='Positive means current leaves STORE through the named device terminal; negative means injection.',
                limits=['Frozen-state DC diagnosis at selected columns/states, not integrated transient charge or a layout correction.','Terminal current includes all modeled mechanisms at that terminal; naming a device does not identify the microscopic leakage mechanism.'],full_bank_accuracy_qualified=False,full_chip_qualified=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
