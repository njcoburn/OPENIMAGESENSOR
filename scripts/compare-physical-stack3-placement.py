"""Recompute the physical candidate's port/far HOLD and STORE sensitivity."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=Path,default=ROOT/'build/compact-bank-physical-cycles-20260930')
    p.add_argument('--far',type=Path,default=ROOT/'build/compact-bank-physical-far-cycles-20260930')
    p.add_argument('--out',type=Path,default=ROOT/'simulations/compact-bank-physical-stack3-placement-20260930.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();cases=[];hashes={}
    for corner in ['typical','ss','ff']:
        values=[]
        for step in [100,50]:
            name=f'stack3-{corner}-acq12.5-{step}';paths=[base/name/'candidate-result.json' for base in [a.port,a.far]]
            left,right=[json.loads(p.read_text()) for p in paths]
            for path in paths:hashes[str(path.resolve().relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
            assert len(left['samples'])==len(right['samples'])==4
            for s,t in zip(left['samples'],right['samples']):
                assert (s['slot'],s['column'],s['time_s'])==(t['slot'],t['column'],t['time_s'])
                values += [abs(s['values'][n]-t['values'][n])*1e6 for n in ['v(hold)','v(store0)','v(store1)']]
        peak=max(values);assert peak<10
        cases.append(dict(corner=corner,max_hold_store_placement_difference_uV=peak,limit_uV=10,selected_pass=True))
    result=dict(cases=cases,scope='Same extracted physical two-column candidate; move all four conserved shunt groups jointly from port to far placement; compare HOLD and both STORE nodes at both timesteps.',full_bank_accuracy_qualified=False,evidence_hashes=hashes)
    if a.check:assert json.loads(a.out.read_text())==result
    else:
        assert not a.out.exists();a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(cases,indent=2))
if __name__=='__main__':main()
