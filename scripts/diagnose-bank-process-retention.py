"""Decompose audited process errors and estimate storage-clamp current from retained DC references.

Read-only analysis: no new simulation, no threshold changes, no causal fix claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    reports=['simulations/compact-bank-64-full-hot.json']+[f'simulations/compact-bank-process-{c}-inverse125-20260930-ssff.json' for c in ['ss','ff']]
    cases=[];evidence={}
    for name in reports:
        report=json.loads((ROOT/name).read_text());run=ROOT/report['runs'][0]['run'];path=run/'result.json'
        assert sha(path)==report['evidence_hashes'][str(path.relative_to(ROOT))]
        r=json.loads(path.read_text());assert r['completed'] and r['temperature_C']==125 and r['lights_pA']==[240,0]*32
        corner=r.get('mos_corner','typical');rows=[]
        for sample in r['samples']:
            c=sample['column'];n=f'STORE{c}';v=sample['values'];settled=sample['output_reference']['values']
            total=sample['total_capture_readout_error_V']*1e6;tracking=sample['output_tracking_error_V']*1e6
            rows.append(dict(scan=sample['slot'],column=c,time_s=sample['time_s'],light_pA=r['lights_pA'][c],total_error_uV=total,tracking_error_uV=tracking,
                             settled_state_change_uV=total-tracking,store_vs_capture_reference_uV=sample['storage_capture_error_V']*1e6,
                             hold_V=v['HOLD'],store_V=v[n],vdd_V=v['VDD'],bias_V=v['BIAS'],pref_V=v['PREF'],
                             inferred_store_leakage_pA=(v[n]-settled[n])*1e12))
        drift=[]
        for c in range(64):
            first,last=rows[c],rows[c+64];dt=last['time_s']-first['time_s'];assert abs(dt-.00128)<1e-12
            # Read the actual behavioral-source law; inference is based on 1 ohm,
            # not an assumed ideal clamp. It is a DC-state diagnostic, not direct
            # transient charge integration or a named-device leakage measurement.
            for scan in ['first','last']:
                deck=run/f'{scan}{c}-output-reference/test.spice';s=deck.read_text()
                law,=[x for x in s.splitlines() if x.startswith(f'Bstore{c} ')]
                assert re.fullmatch(rf'Bstore{c} STORE{c} 0 I=\(V\(STORE{c}\)-\([^)]*\)\)/1',law)
                assert sha(deck)==report['evidence_hashes'][str(deck.relative_to(ROOT))]
            delta=(last['store_V']-first['store_V'])*1e6
            drift.append(dict(column=c,elapsed_ms=dt*1000,store_change_uV=delta,total_error_change_uV=last['total_error_uV']-first['total_error_uV'],
                              tracking_change_uV=last['tracking_error_uV']-first['tracking_error_uV'],
                              equivalent_40pF_discharge_pA=-40e-12*(delta*1e-6)/dt*1e12))
        worst=max(rows,key=lambda q:abs(q['total_error_uV']))
        cases.append(dict(mos_corner=corner,report=name,rows=rows,drift=drift,worst=worst,
                          max_abs_store_drift_uV=max(abs(x['store_change_uV']) for x in drift),
                          total_failing_samples=sum(abs(x['total_error_uV'])>=500 for x in rows)))
        evidence[name]=sha(ROOT/name);evidence[str(path.relative_to(ROOT))]=sha(path)
    evidence['scripts/diagnose-bank-process-retention.py']=sha(Path(__file__))
    result=dict(scope=__doc__,cases=cases,evidence_hashes=evidence,
                limits=['Settled-state change includes storage and rail/bias changes; it is not storage-only error.',
                        'Inferred leakage uses the retained 1-ohm STORE-clamp DC law; subtraction has finite precision.',
                        '40 pF discharge is an approximate equivalent current, not exact extracted charge accounting.',
                        'Further probes are required to attribute leakage to individual devices.'],full_bank_accuracy_qualified=False,full_chip_qualified=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in c.items() if k not in ['rows','drift']} for c in cases],indent=2))

if __name__=='__main__':main()
