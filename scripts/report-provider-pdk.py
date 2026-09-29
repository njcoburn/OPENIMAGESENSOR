"""Reconcile provider-pinned sources and a scoped DRC run without changing PDKs."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    installed_path=ROOT/'build/gf180-installed-nodeinfo-20260927.json';installed=json.loads(installed_path.read_text())
    target='d658698bd8bcf4e05fc7b5991a701247ba0d744c'
    source_paths=[ROOT/'build/gf180-installed-openpdks-tree-20260927.json',ROOT/'build/wafer-space-pdk-target-tree-20260927.json']
    trees=[json.loads(p.read_text()) for p in source_paths]
    assert trees[0]['sha']==installed['commit']['open_pdks'] and trees[1]['sha']==target and all(not t['truncated'] for t in trees)
    maps=[{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'} for t in trees]
    changed=[p for p in sorted(maps[0].keys()|maps[1].keys()) if maps[0].get(p)!=maps[1].get(p)]
    assert [p for p in changed if p.startswith('gf180mcu/')]==['gf180mcu/gf180mcu.json']
    make=ROOT/'build/wafer-space-pdk-target-Makefile-20260927.in';node=ROOT/'build/wafer-space-pdk-target-node-template-20260927.json'
    for path,gitpath in [(make,'gf180mcu/Makefile.in'),(node,'gf180mcu/gf180mcu.json')]:
        content=path.read_bytes();assert hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()==maps[1][gitpath]
    assert 'GF180MCUD_DEFS += -DMETALS5 -DMIM -DTHICKMET1P1 -DHRPOLY1K' in make.read_text()
    assert '"MIM_2P0"' in node.read_text() and '2fF/um^2' in node.read_text()
    assert installed['node']=='gf180mcuD' and set(installed['options'])=={'MIM_2P0','METAL5'} and '1.1um thick top metal' in installed['description']
    refs=dict(re.findall(r'"([^"]+)": "([0-9a-f]{40})"',node.read_text().split('"reference":',1)[1]))
    comparisons=[];evidence={installed_path,make,node,*source_paths,Path(__file__).resolve()}
    for name,key,old in [('primitive','gf180mcu_fd_pr',installed['primitive']['gf180mcu_fd_pr']),('verification','gf180mcu_fd_pv',installed['verification']['gf180mcu_fd_pv'])]:
        path=ROOT/f'build/gf180-{name}-provider-compare-20260927.json';r=json.loads(path.read_text());evidence.add(path)
        assert r['status']=='ahead' and r['behind_by']==0 and r['base_commit']['sha']==r['merge_base_commit']['sha']==old
        assert r['commits'][-1]['sha']==refs[key] and len(r['files'])<300 and len(r['commits'])==r['total_commits']
        comparisons.append(dict(component=name,installed=old,provider_default=refs[key],commits=r['total_commits'],changed_files=[f['filename'] for f in r['files']]))
    assert comparisons[0]['changed_files']==['rules/klayout/macros/gf180mcu_options.lym']
    pvroot=ROOT/'build/gf180-provider-verification-20260927'
    # Check every changed archive file against its provider Git object ID.
    pv=json.loads((ROOT/'build/gf180-verification-provider-compare-20260927.json').read_text())
    for f in pv['files']:
        path=pvroot/f['filename'];content=path.read_bytes()
        assert hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()==f['sha']
    drc=ROOT/'build/compact-bank-c64-provider-drc-v2-20260927';database=drc/'main.lyrdb';log=drc/'main.log'
    tree=ET.parse(database);items=tree.findall('.//items/item')
    assert tree.getroot().tag=='report-database' and tree.findtext('top-cell')=='compact_bank'
    assert tree.findall('./categories/category') and tree.find('./items') is not None
    assert len(items)==len(tree.findall('.//item'))
    assert '# DRC Total Run time ' in log.read_text(), 'Require completed DRC log'
    assert not re.search(r'^ERROR:|Traceback|segmentation fault',log.read_text(),re.M|re.I)
    gds=ROOT/'build/compact-bank-c64-ground-grid-20260927/bank.gds'
    meta=json.loads((gds.parent/'verification.json').read_text());assert sha(gds)==meta['gds_sha256']
    evidence.update([ROOT/'build/compact-bank-c64-provider-drc-20260927/main.log',ROOT/'build/compact-bank-c64-provider-drc-20260927/main.lyrdb',database,log,gds,gds.parent/'verification.json',ROOT/'build/gf180-provider-verification-e766ad1-20260927.tar.gz'])
    evidence.update(p for p in (pvroot/'klayout/drc').rglob('*') if p.is_file())
    report=dict(checked_on='2026-09-27',provider_open_pdks_commit=target,installed_open_pdks_commit=installed['commit']['open_pdks'],
        exact_tree_changed_paths=changed,gf180_build_and_extraction_sources_unchanged=True,primitive_device_model_sources_unchanged=True,
        declared_options_match=dict(metals=5,top_metal_um=1.1,mim_fF_per_um2=2,mim_metal_pair=[4,5]),dependency_comparisons=comparisons,
        provider_verification_source=refs['gf180mcu_fd_pv'],block_main_drc_errors=len(items),block_main_drc_pass=len(items)==0,
        initial_drc_attempt='Rule execution reported zero violations, then KLayout cleanup raised a relative report-path error; the original log/database are retained. The accepted repeat uses absolute input/output paths.',
        exact_provider_precheck_completed=False,provider_build_binary_equivalence_established=False,optical_packaging_approval_established=False,
        scope='Provider-pinned source reconciliation and main DRC on the unchanged compact bank with the installed KLayout executable. Density, antenna, cup, full-chip dimensions/ID/pad checks and provider LVS/ERC are not covered.',
        sources=['https://github.com/wafer-space/gf180mcu-precheck/blob/main/Makefile',f'https://github.com/fossi-foundation/open-pdks/blob/{target}/gf180mcu/Makefile.in',f'https://github.com/fossi-foundation/open-pdks/blob/{target}/gf180mcu/gf180mcu.json',
                 'https://github.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/compare/'+comparisons[0]['installed']+'...'+comparisons[0]['provider_default'],
                 'https://github.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pv/compare/'+comparisons[1]['installed']+'...'+comparisons[1]['provider_default']],
        evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(evidence)})
    (ROOT/'simulations/wafer-space-pdk-reconciliation-20260927.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['declared_options_match','gf180_build_and_extraction_sources_unchanged','primitive_device_model_sources_unchanged','block_main_drc_errors']},indent=2))


if __name__=='__main__':main()
