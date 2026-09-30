"""Check candidate provenance, circuit identity and unchanged storage geometry."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    old=ROOT/'build/compact-capture-v4-20260926';column=ROOT/'build/compact-capture-stack3-v2-20260930';bank=ROOT/'build/compact-bank-c2-stack3-v3-20260930'
    cm=json.loads((column/'verification.json').read_text());bm=json.loads((bank/'verification.json').read_text())
    assert cm['mos']==9 and bm['mos']==26 and bm['mim']==16 and bm['diodes']==2
    assert cm['direct_and_resistor_collapsed_lvs'] and bm['direct_and_resistor_collapsed_lvs']
    assert bm['magic_drc_errors']==cm['magic_drc_errors']==0
    for directory,meta in [(column,cm),(bank,bm)]:
        for name,digest in meta['hashes'].items():assert sha(directory/name)==digest,name
        for report in ['main-drc.lyrdb']+(['abutment-drc.lyrdb'] if directory==column else []):
            assert len(ET.parse(directory/report).getroot().find('items'))==0
        for name in ['direct','collapsed']:
            assert 'Circuits match uniquely' in (directory/f'{name}-lvs.log').read_text()
    layouts=[]
    for directory in [old,column]:
        ly=k.Layout();ly.read(str(directory/'column.gds'));layouts.append(ly)
    a,b=layouts;assert a.dbu==b.dbu
    assert a.cell('capture_column').bbox()==b.cell('capture_column').bbox()
    unchanged=[]
    for layer in [46,75,81,41]:
        before=k.Region(a.cell('capture_column').begin_shapes_rec(a.layer(layer,0)))
        after=k.Region(b.cell('capture_column').begin_shapes_rec(b.layer(layer,0)))
        assert (before^after).is_empty(),layer
        unchanged.append(layer)
    # Independently require exact original contract plus two NMOS and two private nodes.
    original=(ROOT/'checkpoints/capture-column-preparation/capture-column.spice').read_text()
    updated=(ROOT/'circuits/capture-column-stack3.spice').read_text()
    oldline=next(l for l in original.splitlines() if l.startswith('Xholdn '))
    newlines=[l for l in updated.splitlines() if l.startswith(('Xholdn ','Xholdn2 ','Xholdn3 '))]
    assert len(newlines)==3
    restored=updated.replace('\n'.join(newlines),oldline).replace('Nine-transistor','Seven-transistor')
    assert restored==original
    paths=[column,bank]
    files=[p for d in paths for p in d.rglob('*') if p.is_file()]
    files += [ROOT/'scripts'/n for n in ['build-capture-column-stack3.py','verify-capture-column-stack3.py','check-compact-capture-stack3.py','build-compact-bank-stack3.py','capture-stack-connectivity.py','test-capture-stack-connectivity.py','audit-physical-stack3.py']]
    files += [ROOT/'circuits/capture-column-stack3.spice',old/'column.gds']
    report=dict(column=str(column.relative_to(ROOT)),bank=str(bank.relative_to(ROOT)),column_mos=9,bank_mos=26,bank_mim=16,bank_diodes=2,
                column_drc_pass=True,bank_drc_pass=True,column_and_bank_direct_and_collapsed_lvs=True,abutment_40um_drc_pass=True,
                column_bbox_unchanged=True,unchanged_storage_layers=unchanged,contract_change_exactly_three_series_nmos=True,
                shunt_approximation_scope='Conserved signed shunt totals, including new private nodes; all resistors retained. Placement sensitivity still requires checking.',
                full_bank_accuracy_qualified=False,full_chip_qualified=False,
                evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in files})
    dest=ROOT/'simulations/compact-bank-physical-stack3-20260930.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='evidence_hashes'},indent=2))
if __name__=='__main__':main()
