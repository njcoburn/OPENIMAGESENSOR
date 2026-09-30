"""Audit the new 64-column physical candidate without inheriting old-bank qualification."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--layout',type=Path,required=True);a=p.parse_args();d=a.layout.resolve();m=json.loads((d/'verification.json').read_text())
    assert m['columns']==64 and (m['mos'],m['mim'],m['diodes'])==(898,512,64)
    assert m['ground_return_grid'] and m['ground_bus_width_um']==8 and m['capture_series_devices']==5
    assert m['magic_drc_errors']==m['klayout_main_drc_errors']==0 and m['direct_and_resistor_collapsed_lvs']
    for name,digest in m['hashes'].items():assert sha(d/name)==digest
    assert sha(d/'bank.gds')==m['gds_sha256']
    assert len(ET.parse(d/'main-drc.lyrdb').getroot().find('items'))==0
    for name in ['direct','collapsed']:assert 'Circuits match uniquely' in (d/f'{name}-lvs.log').read_text()
    old=json.loads((ROOT/'build/compact-bank-c64-ground-grid-20260927/verification.json').read_text())
    assert m['ground_grid_added_rectangles_um']==old['ground_grid_added_rectangles_um']
    physical=ROOT/'simulations/compact-bank-physical-stack5-20260930.json';review=json.loads(physical.read_text())
    for name,digest in review['evidence_hashes'].items():assert sha(ROOT/name)==digest,name
    column=ROOT/review['column'];assert m['source_hashes'][str((column/'column.gds').relative_to(ROOT))]==sha(column/'column.gds')
    for name,digest in m['source_hashes'].items():assert sha(ROOT/name)==digest
    raw=re.sub(r'\n\+',' ',(d/'raw-rc.spice').read_text());records=[l.split() for l in raw.splitlines() if l and l[0] not in '*.'];parent={}
    def find(n):
        parent.setdefault(n,n)
        if parent[n]!=n:parent[n]=find(parent[n])
        return parent[n]
    for r in records:
        if r[0][0]=='R':parent[find(r[1])]=find(r[2])
    spec=importlib.util.spec_from_file_location('stack',ROOT/'scripts/capture-stack5-connectivity.py');stack=importlib.util.module_from_spec(spec);spec.loader.exec_module(stack)
    paths=stack.identify(records,find,{find(n):n for n in m['ports']},64);assert paths==m['stack_paths']
    assert len({device for path in paths for device in path['instances']})==320
    expected=Counter(r[5] if r[0][0]=='X' and not r[3].startswith('cap_mim_') else r[3] for r in records if r[0][0] in 'XD')
    assert expected['nfet_03v3']==641 and expected['pfet_03v3']==257 and expected['cap_mim_2f0_m4m5_noshield']==512 and expected['diode_nd2ps_03v3']==64
    files=[p for p in d.iterdir() if p.is_file()]+[Path(__file__),ROOT/'scripts/build-compact-bank-stack5.py',ROOT/'scripts/capture-stack5-connectivity.py',ROOT/'circuits/capture-column-stack5.spice',physical,column/'verification.json',ROOT/'build/compact-bank-c64-ground-grid-20260927/verification.json']
    result=dict(physical_checks_pass=True,columns=64,mos=898,mim=512,diodes=64,five_device_chains=64,ground_grid_rectangles_match_baseline=True,original_checkpoint_replaced=False,full_bank_accuracy_qualified=False,evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in files})
    assert not (d/'physical-audit.json').exists();(d/'physical-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Full 64-column physical audit passed: 898 MOS, 512 MIM, 64 diodes, 64 capture chains.')
if __name__=='__main__':main()
