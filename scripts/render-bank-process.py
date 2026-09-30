"""Publish process-case progress separately from the completed typical baseline."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    plan=json.loads(a.plan.read_text());rows=[];plots=[]
    status_path=ROOT/plan.get('watcher',{}).get('path','missing')/'status.json'
    state=json.loads(status_path.read_text()) if status_path.exists() else {}
    for case in plan['cases']:
        path=ROOT/'simulations'/case['report'];name=case['name']
        if path.exists():
            r=json.loads(path.read_text())
            assert (r['mos_corner'],r['temperature_C'],r['pattern'])==(case['mos_corner'],case['temperature'],case['pattern'])
            assert r['selected_screen_pass']==all(r['checks'].values())
            assert not r['full_bank_accuracy_qualified'] and not r['full_chip_qualified']
            values=f'<td><a href="../simulations/{case["report"]}">{"PASS" if r["selected_screen_pass"] else "FAIL"}</a></td><td>{r["max_total_error_uV"]:.3f}</td><td>{r["max_tracking_error_uV"]:.3f}</td><td>{r["max_refinement_uV"]:.3f}</td>'
            asset=Path(case['report']).stem+'.png';module('plots','render-bank-full.py').plot(r,ROOT/'docs/assets'/asset)
            plots.append(f'<figure><img src="assets/{asset}" alt="{case["mos_corner"].upper()} transistor corner, 125 C inverse, independent accuracy audit"></figure>')
        else:
            status='Simulation/audit failed' if name in state.get('failures',{}) else 'Watcher expired; inspect jobs' if state.get('watcher_expired') else 'Pending audit'
            values=f'<td>{status}</td><td>—</td><td>—</td><td>—</td>'
        rows.append(f'<tr><td>{case["mos_corner"].upper()} / {case["temperature"]} °C / {case["pattern"]}</td>{values}</tr>')
    fragment=f'''<!-- BEGIN BANK_PROCESS -->
<div id="compact-bank-process"><h3>Process variation — first MOS-corner batch</h3>
<p>Slow/slow (SS) and fast/fast (FF) transistor models at 125 °C with inverse illumination: four fresh 100/50 ns transients and 384 matched references. This starts with the smallest-margin typical-process case. Diodes, MIM capacitors, supply and extracted wiring retain their nominal settings; mixed MOS and other operating corners remain open.</p>
<table><thead><tr><th>Case</th><th>Audited status</th><th>Total error, µV</th><th>Tracking, µV</th><th>Sample refinement, µV</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>Limits remain 500 µV total/tracking and 10 µV sample/event refinement; contrast ordering is required. Every matched reference uses the same MOS corner as its transient. Pending is not a pass. No later batch starts automatically.</p>
{''.join(plots)}
<p><a href="verification-journal.html#process">Journal: process work</a> · <a href="../{a.plan.as_posix()}">Launch plan</a> · <a href="../PICK_UP_HERE.md">Current handoff</a></p></div>
<!-- END BANK_PROCESS -->'''
    (ROOT/'docs/compact-bank-process-fragment.html').write_text(fragment+'\n')
    section=ROOT/'docs/64x64-first-silicon-section.html';s=section.read_text();pattern=r'<!-- BEGIN BANK_PROCESS -->.*?<!-- END BANK_PROCESS -->'
    if re.search(pattern,s,re.S):s,count=re.subn(pattern,lambda _:fragment,s,flags=re.S);assert count==1
    else:s=s.replace('</section>',fragment+'\n</section>')
    section.write_text(s)
    journal=ROOT/'docs/verification-journal.html';s=journal.read_text()
    # Keep overview-relative paths valid on the standalone journal too.
    jf=fragment.replace('id="compact-bank-process"','id="process"')
    if re.search(pattern,s,re.S):s,count=re.subn(pattern,lambda _:jf,s,flags=re.S);assert count==1
    else:s=s.replace('<section id="remaining">',jf+'\n<section id="remaining">')
    journal.write_text(s)
    module('overview','update-overview-sections.py').main()
    subprocess.run([sys.executable,str(ROOT/'scripts/update-verification-journal.py')],check=True)

if __name__=='__main__':main()
