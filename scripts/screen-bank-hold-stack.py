"""Model-only series NMOS capture-switch stack screen in frozen FF output states.

This does not change GDS, constitute LVS evidence, or qualify capture/settling.
It is a bounded leakage tradeoff screen to select a later physical candidate.
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

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def change_length(model,instance,length):
    count=int(length);assert count in [2,3]
    lines=model.splitlines();old,=[l for l in lines if l.startswith(instance+' ')]
    f=old.split();assert f[5]=='nfet_03v3' and 'l=0.5u' in f
    newlines=[]
    for i in range(count):
        q=f.copy();q[0]=instance if i==0 else f'XDIAG_STACK_{i}'
        assert i==0 or q[0] not in model
        q[1]=f[1] if i==0 else f'DIAG_STACK_{i}'
        q[3]=f[3] if i==count-1 else f'DIAG_STACK_{i+1}'
        assert i==count-1 or q[3] not in model
        newlines.append(' '.join(q))
    new='\n'.join(newlines);altered=model.replace(old+'\n',new+'\n',1)
    assert altered.replace(new+'\n',old+'\n',1)==model
    assert sum(l.startswith('X') for l in altered.splitlines())==sum(l.startswith('X') for l in lines)+count-1
    return altered,old,new


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);(out/'runner.py').write_bytes(Path(__file__).read_bytes())
    probe=json.loads((source/'result.json').read_text())
    assert all(c['current_balance_within_0_25pA'] and c['voltage_equivalence_max_uV']<1 for c in probe['cases'])
    for name,digest in probe['evidence_hashes'].items():assert sha(ROOT/name)==digest,name
    spec=importlib.util.spec_from_file_location('dc',ROOT/'scripts/report-compact-bank-16.py');dc=importlib.util.module_from_spec(spec);spec.loader.exec_module(dc)
    def one(column,length):
        base=source/f'ff-last{column}';record=json.loads((base/'result.json').read_text());dest=out/f'ff-last{column}-stack{int(length)}';dest.mkdir()
        hold,=[r for r in record['probes'] if r['role']=='hold_n']
        model,old,new=change_length((base/'tile.spice').read_text(),hold['instance'],length)
        (dest/'tile.spice').write_text(model)
        deck=(base/'test.spice').read_text();oldinclude=f'.include {base}/tile.spice';assert deck.count(oldinclude)==1
        deck=deck.replace(oldinclude,f'.include {dest}/tile.spice');(dest/'test.spice').write_text(deck);shutil.copyfile(base/'.spiceinit',dest/'.spiceinit')
        start=time.monotonic()
        with (dest/'ngspice.log').open('w') as log:
            code=subprocess.run(['ngspice','-b','test.spice'],cwd=dest,stdout=log,stderr=subprocess.STDOUT,timeout=300,env={**os.environ,'SPICE_USERINIT_DIR':str(dest),'OMP_NUM_THREADS':'1'}).returncode
        errors=[l for l in (dest/'ngspice.log').read_text().splitlines() if re.search(r'^Error|aborted|timestep too small|no such|not found',l,re.I)]
        (dest/'execution.json').write_text(json.dumps(dict(returncode=code,errors=errors,seconds=time.monotonic()-start),indent=2)+'\n');assert code==0 and not errors
        values=dc.dc_values(dest/'op.raw')
        branch={r['role']:-values[f'i(v.xtile.{r["probe"].lower()})']*1e12 for r in record['probes']}
        supply=values['i(vdiag_clamp)']*1e12;kcl=abs(sum(branch.values())-supply);assert kcl<.25
        baseline=dc.dc_values(base/'op.raw')
        store_difference=abs(values[f'v(store{column})']-baseline[f'v(store{column})'])*1e6;assert store_difference<1
        result=dict(column=column,mos_corner='ff',series_devices=int(length),individual_length_um=.5,original_series_devices=1,changed_instance=hold['instance'],old_line=old,new_line=new,
                    nm_hold_leakage_pA=branch['hold_n'],net_store_leakage_pA=supply,kcl_residual_pA=kcl,store_state_change_uV=store_difference,
                    baseline_nm_hold_leakage_pA=record['device_current_leaving_store_pA']['hold_n'],baseline_net_store_leakage_pA=record['clamp_supply_measured_pA'],
                    diagnostic_only=True,physical_layout_changed=False,accuracy_qualified=False)
        (dest/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(one,c,l) for c in [0,63] for l in [2,3]];results=[f.result() for f in futures]
    files=[p for p in out.rglob('*') if p.is_file()]+[source/'result.json',Path(__file__)]
    result=dict(scope=__doc__,cases=results,evidence_hashes={str(p.resolve().relative_to(ROOT)):sha(p) for p in files},physical_layout_changed=False,
                limits=['The NMOS capture switch is replaced by two or three series devices in two frozen DC states; all results are diagnostic.',
                        'Physical dimensions, parasitic changes, capture charge injection, acquisition and process/temperature matrix must be rebuilt and checked before adopting a candidate.'],full_bank_accuracy_qualified=False,full_chip_qualified=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
