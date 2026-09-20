"""Check device records and basic capacitor validity of the fresh lumped baseline.
Exact capacitance-matrix and distributed-R acceptance are separate open checks.
"""
from pathlib import Path
from collections import Counter
import json,hashlib,re
R=Path(__file__).resolve().parents[1];B=R/'build/filled-electrical-baseline'
old=R/'build/filled-demonstrator/routed_extracted.spice';new=B/'filled_lumped.spice'
def records(p):
 rows=[]
 for l in p.read_text().splitlines():
  if l.startswith('+'):rows[-1]+=' '+l[1:]
  elif l.strip() and not l.startswith('*'):rows.append(l)
 return rows
x,y=records(old),records(new)
def devices(rows):return Counter(tuple(l.split()[1:]) for l in rows if l.startswith(('X','D','R')))
a,b=devices(x),devices(y);removed=list((a-b).elements());added=list((b-a).elements())
units={'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'meg':1e6,'g':1e9}
def number(s):
 m=re.fullmatch(r'([+-]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][+-]?\d+)?)([A-Za-z]*)',s);assert m,s
 return float(m[1])*units[m[2].lower()]
caps=[l.split() for l in y if l.startswith('C')];values=[number(t[3]) for t in caps]
r=dict(reference_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),device_records_match=not removed and not added,reference_devices=sum(a.values()),baseline_devices=sum(b.values()),removed_examples=removed[:5],added_examples=added[:5],capacitor_count=len(caps),negative_capacitors=sum(v<0 for v in values),self_capacitors=sum(t[1]==t[2] for t in caps),port_header_match=next(l for l in x if l.startswith('.subckt'))==next(l for l in y if l.startswith('.subckt')),original_capacitance_matrix_audit='Pending',distributed_wire_resistance='Absent by design in this baseline',accepted_full_chip_rc=False)
(B/'audit.json').write_text(json.dumps(r,indent=2)+'\n');(R/'simulations/filled-electrical-baseline.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
assert r['device_records_match'] and r['port_header_match'] and r['negative_capacitors']==0
