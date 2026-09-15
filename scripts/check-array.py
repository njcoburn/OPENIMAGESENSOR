"""Check actual verification reports and count devices through the hierarchy."""
from pathlib import Path
import re,json,hashlib,xml.etree.ElementTree as E
root=Path(__file__).resolve().parents[1];out=root/'build/array-check'
magic=(out/'magic.log').read_text();lvs=(out/'lvs.log').read_text();xlvs=(out/'xschem_lvs.log').read_text()
assert 'ARRAY_DRC_COUNT=0' in magic
assert 'Final result: Circuits match uniquely.' in lvs and 'Final result: Circuits match uniquely.' in xlvs
s=(out/'array_extracted.spice').read_text();s=re.sub(r'\n\+\s*',' ',s)
cells={};current=None
for line in s.splitlines():
 tok=line.split()
 if not tok or line.startswith('*'):continue
 if tok[0].lower()=='.subckt':current=tok[1];cells[current]=[]
 elif tok[0].lower()=='.ends':current=None
 elif current:cells[current].append(tok)
def count(name):
 mos=diodes=0
 for t in cells[name]:
  if t[0][0].lower()=='d':diodes+=1
  elif t[0][0].lower()=='x':
   device=next((v for v in t[1:] if v in cells or v=='nfet_03v3'),None)
   if device=='nfet_03v3':mos+=1
   else:
    assert device in cells, t
    m,d=count(device);mos+=m;diodes+=d
 return mos,diodes
assert count('array_3x3')==(27,9),count('array_3x3')
report=E.parse(out/'klayout-final.lyrdb').getroot();items=report.findall('.//items/item')
violations={}
for item in items:
 key=item.findtext('category','unknown');violations[key]=violations.get(key,0)+1
result=dict(magic_drc_errors=0,lvs='unique match',xschem_lvs='unique match',mosfets=27,diodes=9,klayout_violations=violations,klayout_total=len(items),gds_sha256=hashlib.sha256((root/'build/array_3x3.gds').read_bytes()).hexdigest(),scope='Local GF180MCUD core checks; not wafer.space tapeout signoff.')
(root/'simulations/array-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert not items,'Full KLayout DRC still has violations'
