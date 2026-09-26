"""Compare full-readout circuits/stimuli with the completed grid power test."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--runs',type=Path,required=True)
p.add_argument('--reference',type=Path,default=ROOT/'build/row-power-grid-sparse-refine-20260924/grid-refined/test.spice')
a=p.parse_args();root=a.runs.resolve();out=root/'fixture-verification';out.mkdir(exist_ok=False)
shutil.copyfile(__file__,out/'runner.py');shutil.copyfile(a.reference,out/'reference.spice')
def records(path):
    result=[];disconnected=False
    for line in path.read_text().splitlines():
        if line.startswith('Vdiagnostic_steps '):disconnected=True;continue
        if disconnected and line.startswith('+'):continue
        disconnected=False
        assert 'diagnostic_steps' not in line.lower()
        if line.startswith(('.save ','.tran ','.temp ')):continue
        if line.startswith('.include ') and line.endswith(('/array.spice','/buffer.spice')):
            line='.include /CASE/'+line.split('/')[-1]
        result.append(' '.join(line.split()))
    return sorted(result)
reference=records(a.reference)
expected=hashlib.sha256((ROOT/'build/row-power-grid-20260924/r1c64/rc-port.spice').read_bytes()).hexdigest()
checks=[]
for temp in [27,125]:
    for step in [100,200]:
        d=root/f'{temp}-{step}/r1c64-rc-port';deck=d/'transient/test.spice'
        assert records(deck)==reference,(temp,step)
        assert hashlib.sha256((d/'array.spice').read_bytes()).hexdigest()==expected
        assert (d/'buffer.spice').read_bytes()==(a.reference.parent/'buffer.spice').read_bytes()
        checks.append({'temperature_C':temp,'step_ns':step,'deck_sha256':hashlib.sha256(deck.read_bytes()).hexdigest()})
report={'all_four_circuits_and_stimuli_match':True,'source_model_sha256':expected,
        'reference_sha256':hashlib.sha256(a.reference.read_bytes()).hexdigest(),'decks':checks,
        'excluded_differences':['temperature','transient stop/maxstep','observations',
                                'disconnected breakpoint voltage source','per-case model include paths'],
        'model_comparison':'Full extracted row model and peripheral buffer model byte-identical to accepted power diagnostic.'}
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
