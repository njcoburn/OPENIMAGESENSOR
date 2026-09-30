"""Preserve the reviewed five-device preparation and portable physical checkpoint."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def main():
    layout=ROOT/'build/compact-bank-c64-stack5-grid-20260930'
    control=ROOT/'build/stack5-controls-20260930-overnight/result.json'
    diagnostic=ROOT/'build/stack-retention-review-overnight-20260930/result.json'
    physical=ROOT/'simulations/compact-bank-physical-stack5-20260930.json'
    controls=json.loads(control.read_text());assert controls['passed'] and controls['fresh_transients']==12
    full=json.loads((layout/'physical-audit.json').read_text());assert full['physical_checks_pass']
    for report,key in [(controls,'source_hashes'),(full,'evidence_hashes')]:
        for name,digest in report[key].items():assert sha(ROOT/name)==digest,name
    for src,name in [(control,'stack5-controls-20260930.json'),(diagnostic,'stack-retention-review-overnight-20260930.json')]:
        dest=ROOT/'simulations'/name;assert not dest.exists();shutil.copyfile(src,dest)
    checkpoint=ROOT/'checkpoints/compact-bank-stack5-64';checkpoint.mkdir(exist_ok=False)
    artifacts={}
    for name in ['bank.gds','rc-port.spice','rc-far.spice']:
        raw=(layout/name).read_bytes();dest=checkpoint/(name+'.gz');dest.write_bytes(gzip.compress(raw,mtime=0))
        assert gzip.decompress(dest.read_bytes())==raw
        artifacts[dest.name]=dict(sha256=sha(dest),uncompressed_sha256=sha(layout/name),source=str((layout/name).relative_to(ROOT)))
    for name in ['verification.json','physical-audit.json','reference.spice']:
        shutil.copyfile(layout/name,checkpoint/name);artifacts[name]=dict(sha256=sha(checkpoint/name),source=str((layout/name).relative_to(ROOT)))
    shutil.copyfile(ROOT/'circuits/capture-column-stack5.spice',checkpoint/'capture-column-stack5.spice')
    artifacts['capture-column-stack5.spice']=dict(sha256=sha(checkpoint/'capture-column-stack5.spice'),source='circuits/capture-column-stack5.spice')
    save(checkpoint/'manifest.json',dict(scope='Separate physical candidate only; electrical full-bank verification pending. Unfilled development bank, not a full chip.',artifacts=artifacts,full_bank_accuracy_qualified=False,full_chip_qualified=False))
    profile=dict(scope='Fixed five-device candidate; 13 us acquisition, ADC reset at 15.5 us, 20 us slots. Small extracted controls passed; full-bank process queue pending.',
        layout=str(layout.relative_to(ROOT)),column='build/compact-capture-stack5-v5-20260930',small_bank='build/compact-bank-c2-stack5-v1-20260930',
        physical_audit=str(physical.relative_to(ROOT)),full_physical_audit=str((layout/'physical-audit.json').relative_to(ROOT)),controls='simulations/stack5-controls-20260930.json',
        model_only_diagnostic='simulations/stack-retention-review-overnight-20260930.json',checkpoint=str(checkpoint.relative_to(ROOT)),
        rerun_command='python3 scripts/rerun-bank-stack5.py --tag new-tag',plan_only_command='python3 scripts/rerun-bank-stack5.py --tag new-tag --plan-only',
        changed_layout_policy='Rebuild column/pixel/bank, DRC/LVS and extraction, update versioned layout profile and guards, then rerun controls and full queue. This fixed-source command does not automatically qualify a changed pixel.',
        limits_uV=dict(total=500,tracking=500,refinement=10,placement=10),full_bank_accuracy_qualified=False,full_chip_qualified=False,
        failed_physical_attempts=[dict(path=f'build/compact-capture-stack5-v{i}-20260930',reason=reason) for i,reason in [(1,'Metal2 spacing'),(2,'Metal2 spacing'),(3,'HN4 short to STORE, rejected by circuit audit'),(4,'HN4 short to GND, rejected by circuit audit')]])
    save(ROOT/'verification/compact-bank-stack5.json',profile)
    rows=''.join(f'<tr><td>{c["model"]}</td><td>{c["corner"]}</td><td>{c["total_uV"]:.3f}</td><td>{c["tracking_uV"]:.3f}</td><td>PASS</td></tr>' for c in controls['cases'])
    fragment=f'''<!-- BEGIN STACK5_PREPARATION -->
<div id="stack5-preparation"><h3>Five-device correction — physical and small-bank checks</h3>
<p>The longer-age two-column model experiment compared three, four and five series NMOS capture devices with 13 µs acquisition. Fast-corner totals were 604.318, 468.926 and 396.116 µV respectively. All 12 diagnostic transients and 72 references were independently reviewed; these model-only results selected the five-device physical experiment.</p>
<p>The new physical column contains 11 MOS devices and preserves the 40 µm pitch, outline, MIM plates and upper storage routing. The two-column bank has 30 MOS devices; the separate 64-column bank has 898 MOS, 512 MIM plates and 64 photodiodes. Both physical banks pass Magic/KLayout main DRC and direct/resistor-collapsed LVS. All 64 five-device capture chains are checked. Earlier routing attempts failed spacing or connectivity checks and remain saved.</p>
<table><caption>Extracted two-column controls at 125 °C, inverse illumination: worst across fresh 100/50 ns transients, µV. Total/tracking limit 500 µV.</caption><thead><tr><th>Placement</th><th>MOS corner</th><th>Total</th><th>Tracking</th><th>Result</th></tr></thead><tbody>{rows}</tbody></table>
<p>Twelve physical-control transients and 72 fresh references pass independent raw-data checks. Numerical, capacitor/private-node event, contrast and placement checks pass. Maximum sampled port/far HOLD/STORE change: {controls['max_port_far_hold_store_difference_uV']:.4f} µV. These controls use the unmodified extracted circuit. The new timing samples at 14.999 µs, ends acquisition at 15.01 µs and resets the ADC at 15.5 µs within each 20 µs slot.</p>
<p>Full-bank electrical results remain pending. The detached queue uses three concurrent jobs, an eight-hour transient watchdog, twelve-hour job limit and a 48-hour limit on starting subsequent stages. Every stage requires independent passing audits; failures preserve evidence and stop progression. Density, antenna, CUP, other diode/MIM/supply/wire corners and full-chip qualification remain open.</p>
<p><a href="../verification/compact-bank-stack5.json">Reproduction profile and failed-attempt record</a> · <a href="../simulations/stack5-controls-20260930.json">Physical control evidence</a> · <a href="../simulations/stack-retention-review-overnight-20260930.json">Model-only diagnostic review</a> · <a href="../checkpoints/compact-bank-stack5-64/manifest.json">Portable physical checkpoint</a></p>
<p>Fixed-candidate replay: <code>python3 scripts/rerun-bank-stack5.py --tag new-tag</code>. Add <code>--plan-only</code> to inspect the commands. A changed pixel first requires rebuilding and requalifying its physical extraction and updating the versioned profile.</p></div>
<!-- END STACK5_PREPARATION -->'''
    (ROOT/'docs/stack5-preparation-fragment.html').write_text(fragment+'\n')
    for name in ['64x64-first-silicon-section.html','verification-journal.html']:
        p=ROOT/'docs'/name;text=p.read_text();assert '<!-- BEGIN STACK5_PREPARATION -->' not in text
        text=text.replace('<!-- BEGIN STACK3_INTERRUPTED_REVIEW -->',fragment+'\n<!-- BEGIN STACK3_INTERRUPTED_REVIEW -->',1);p.write_text(text)
    catalog=ROOT/'verification/compact-bank-suite.json';data=json.loads(catalog.read_text())
    data['history'].append(dict(date='2026-09-30',title='Five-device candidate passes physical and small-bank preflight',detail='Model-only extended-age screen: FF 604.318 → 396.116 uV. Implement separate five-device column and banks; physical DRC/LVS and unchanged storage geometry pass. Twelve extracted port/far transients and 72 references pass. Full-bank electrical coverage remains pending; new gated runner uses 3 workers and an 8-hour transient watchdog.',evidence='verification/compact-bank-stack5.json'));save(catalog,data)
    for name in ['update-overview-sections.py','update-verification-journal.py']:subprocess.run([sys.executable,str(ROOT/'scripts'/name)],check=True)
if __name__=='__main__':main()
