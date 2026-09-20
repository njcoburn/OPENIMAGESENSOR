"""Build a scoped nominal MOS-cap approximation from a successful stock DC OP."""
from pathlib import Path
import hashlib,json,math
R=Path(__file__).resolve().parents[1];F=R/'build/functional-pad-model'
op_path=R/'build/functional-camera/op-100ns/result.json'
op=json.loads(op_path.read_text());info=json.loads((F/'caps.json').read_text())
raw=(F/'stock-model.spice').read_text()
assert op['completed'] and op['stage']=='op'
assert hashlib.sha256(raw.encode()).hexdigest()==op['candidate_sha256']
assert info['source_sha256']==op['source_model_sha256']
s=op['summary'];voltages=s['last_values'][s['base_vector_count']:]
assert len(voltages)==len(info['pairs']) and all(3.2<v<3.4 for v in voltages)
bias=dict(zip(map(tuple,info['pairs']),voltages));replacements={};records=[]
for c in info['capacitors']:
 v=bias[c['p'],c['n']];cv=c['area_m2']*(.001107+.00107*math.tanh(6.25*v-4.1875))
 replacements[c['line']]=f"Cfreeze_{c['name']} {c['p']} {c['n']} {cv:.17g}"
 records.append({**c,'bias_V':v,'frozen_F':cv})
out='\n'.join(replacements.get(l,l) for l in raw.splitlines())+'\n'
assert len(replacements)==1680 and ' cap_nmos_06v0 ' not in out
assert [l for l in raw.splitlines() if l not in replacements]==[l for l in out.splitlines() if not l.startswith('Cfreeze_')]
(F/'frozen-model.spice').write_text(out)
(F/'frozen-model.json').write_text(json.dumps(dict(op_complete=True,op_sha256=hashlib.sha256(op_path.read_bytes()).hexdigest(),source_sha256=info['source_sha256'],stock_sha256=op['candidate_sha256'],frozen_sha256=hashlib.sha256(out.encode()).hexdigest(),other_records_unchanged=True,capacitors=records,scope='Typical, 27 C, settled 3.3 V only. Requires transient capacitor-voltage validation; excludes startup/ESD.'),indent=2)+'\n')
print('Froze 1680 MOS capacitors; all other netlist records retained.')
