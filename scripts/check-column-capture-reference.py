"""Independent DC column targets at the common optical capture state.

Freezes each diode's measured differential voltage, closes the capture switches,
and removes transient integration. This exposes column acquisition lag that a
comparison against the already stored voltage would conceal.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, runpy, subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
read_raw = runpy.run_path(str(ROOT/'scripts/diagnose-functional-camera.py'))['read_raw']
p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--run', required=True)
p.add_argument('--op-us', type=float, default=200)
p.add_argument('--row-power-diagnostic', action='store_true',
               help='Accept a completed bounded row-power run that reaches common capture')
a = p.parse_args()
d = Path(a.run).resolve()
result = json.loads((d/'result.json').read_text())
transient = d/'transient'
if a.row_power_diagnostic:
    assert result['completed'] and result['resistance_factor']==1 and result['model_name']=='rc-port'
    assert result['analysis']['stop_s'] >= .001401-1e-12
    transient = d
    # Adapt only the helper's in-memory fixture description. Never mark a
    # bounded power run as a completed full readout in its saved evidence.
    result = {**result, 'column_storage_pF':40, 'rows':1, 'columns':64,
              'case':'r1c64', 'mode':'rc-port', 'capture_time_s':.0014}
assert result['completed'] and result['column_storage_pF'] and result['rows']==1
meta = json.loads((Path(a.source)/result['case']/'extraction.json').read_text())
assert hashlib.sha256((Path(a.source)/result['case']/(result['mode']+'.spice')).read_bytes()).hexdigest()==result['model_sha256']
names, data = read_raw(transient/'stream.raw')
assert np.isfinite(data).all()
t = result['capture_time_s']-1e-9
def node(n):
    return '0' if n=='GND' else n if n in meta['ports'] else 'xarray.'+n
def at(n):
    return 0. if n=='0' else float(np.interp(t,data[:,0],data[:,names.index('v('+n.lower()+')')]))
source_deck=(transient/'test.spice').read_text()
if a.row_power_diagnostic:
    assert all(f'Cstore{c} STORE{c} 0 40p\n' in source_deck for c in range(64))
    assert 'Vctl_sc CTL_SC 0 PWL(0 1 0.0014 1 0.00140001 0)' in source_deck
source_hash=hashlib.sha256(source_deck.replace(str(d),'/CASE').encode()).hexdigest()
deck = source_deck.split('.save ',1)[0]
deck = re.sub(r'(?m)^Ilight_.*\n','',deck)
for key, role in meta['roles']['rc'].items():
    sense, anode = node(role['sense']), node(role['anode'])
    deck += f'Bcapture_sense_{key} {sense} {anode} I=(V({sense},{anode})-({at(sense)-at(anode):.16g}))/1\n'
for name in ['ROW0','RST0']+[f'SEL{c}' for c in range(result['columns'])]:
    deck, count = re.subn(r'(?m)^Vctl_'+name+r' .*$', f'Vctl_{name} CTL_{name} 0 {int(name=="ROW0")}',deck)
    assert count==1
for pattern, replacement in [(r'^Vctl_sc .*$', 'Vctl_sc CTL_SC 0 1'),
                              (r'^Vacq .*$', 'Vacq ACQ 0 0'),
                              (r'^Vrst_adc .*$', 'Vrst_adc RSTADC 0 3.3')]:
    deck,count = re.subn(pattern,replacement,deck,flags=re.M);assert count==1
saves=' '.join(f'v({prefix}{c})' for c in range(result['columns']) for prefix in ['COL','STORE','CBUF'])
deck += '.save '+saves+'\n.control\nunset klu\nset num_threads=1\nset filetype=binary\noptran 1 1 1 100n '+str(a.op_us)+'u 0\nop\nwrite op.raw\nquit\n.endc\n.end\n'
out=d/f'capture-dc-{a.op_us:g}us';out.mkdir(exist_ok=False)
(out/'runner.py').write_bytes(Path(__file__).read_bytes())
(out/'test.spice').write_text(deck)
with (out/'ngspice.log').open('w') as log:
    proc=subprocess.run(['ngspice','-b','test.spice'],cwd=out,stdout=log,stderr=subprocess.STDOUT,
                        env={**os.environ,'SPICE_USERINIT_DIR':str(d.parent/'init'),'OMP_NUM_THREADS':'1'},timeout=180)
log=(out/'ngspice.log').read_text()
assert proc.returncode==0 and not re.search(r'aborted|^Error',log,re.M|re.I)
n,v=read_raw(out/'op.raw');assert v.shape==(1,len(n)) and np.isfinite(v).all()
columns={str(c):float(v[0,n.index(f'v(col{c})')]) for c in range(result['columns'])}
errors={str(c):at(f'STORE{c}')-columns[str(c)] for c in range(result['columns'])}
report={'normalized_transient_sha256':source_hash,'source_run':str(d),'model_sha256':result['model_sha256'],'capture_time_s':t,'op_duration_us':a.op_us,
        'column_targets_V':columns,'capture_acquisition_errors_V':errors,
        'max_capture_acquisition_error_V':max(abs(x) for x in errors.values()),
        'deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),
        'scope':'DC target at common captured diode state, not at already stored voltage; schematic storage/periphery and extracted unfilled row.'}
report['row_power_diagnostic'] = a.row_power_diagnostic
(out/'reference.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['column_targets_V','capture_acquisition_errors_V']}))
