"""Double settling for capture targets and selected full-readout DC references."""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
read_raw=runpy.run_path(str(ROOT/'scripts/diagnose-functional-camera.py'))['read_raw']
p=argparse.ArgumentParser()
p.add_argument('--runs',type=Path,required=True)
p.add_argument('--source',type=Path,default=ROOT/'build/row-power-grid-20260924')
a=p.parse_args();root=a.runs.resolve();out=root/'reference-verification';out.mkdir(exist_ok=False)
selected=json.loads((root/'manifest.json').read_text()).get('selected_matched_runs',{})
shutil.copyfile(__file__,out/'runner.py')
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
report={'capture':{},'output':[],'reference_agreement_limit_V':1e-8}
jobs=[]
for temp in [27,125]:
    original=root/f'{temp}-100/r1c64-rc-port'
    matched=root/selected.get(str(temp),f'{temp}-100-matched')/'r1c64-rc-port'
    r=json.loads((matched/'result.json').read_text());assert r['completed']
    with (out/f'capture-{temp}.log').open('w') as f:
        subprocess.run([sys.executable,str(ROOT/'scripts/check-column-capture-reference.py'),
                        '--source',str(a.source.resolve()),'--run',str(original),'--op-us','400'],
                       env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    refs=[json.loads((original/f'capture-dc-{duration}us/reference.json').read_text()) for duration in [200,400]]
    assert refs[0]['normalized_transient_sha256']==refs[1]['normalized_transient_sha256']
    delta=max(abs(v-refs[1]['column_targets_V'][k]) for k,v in refs[0]['column_targets_V'].items())
    assert delta<1e-8
    report['capture'][str(temp)]={'maximum_target_difference_V':delta}
    worst=max(range(64),key=lambda i:abs(r['samples'][i]['errors_V']['10']))
    for c in sorted({0,63,worst}):jobs.append((temp,c,matched,r['samples'][c]))
def verify(job):
    temp,c,matched,sample=job;d=out/f'{temp}-column-{c:02d}';d.mkdir()
    source=matched/f'dc-{c:03d}/test.spice';text=source.read_text()
    assert text.count('optran 1 1 1 100n 200u 0')==1
    deck=text.replace('optran 1 1 1 100n 200u 0','optran 1 1 1 100n 400u 0')
    (d/'test.spice').write_text(deck)
    with (d/'ngspice.log').open('w') as f:
        proc=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,
                            env={**env,'SPICE_USERINIT_DIR':str(matched.parent/'init')},timeout=600)
    log=(d/'ngspice.log').read_text()
    assert proc.returncode==0 and not re.search(r'aborted|^Error|timestep too small',log,re.M|re.I)
    names,data=read_raw(d/'op.raw');assert data.shape==(1,len(names)) and np.isfinite(data).all()
    values={n:float(data[0,i]) for i,n in enumerate(names)}
    delta=abs(values['v(hold)']-sample['dc']['v(hold)'])
    residual=abs(values['v(hold)']-values['v(adcin)'])
    assert delta<1e-8 and residual<1e-8,(temp,c,delta,residual)
    result={'temperature_C':temp,'column':c,'target_difference_V':delta,'hold_adcin_residual_V':residual,
            'source_deck_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'deck_sha256':hashlib.sha256(deck.encode()).hexdigest()}
    (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
with ThreadPoolExecutor(max_workers=3) as pool:report['output']=list(pool.map(verify,jobs))
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
