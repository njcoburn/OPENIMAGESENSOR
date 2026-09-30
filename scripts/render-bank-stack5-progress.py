"""Publish live unattended-sequence status without changing baseline qualification."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):
    try:return json.loads(p.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);a=p.parse_args();plan=read(a.plan);state=read(ROOT/plan['output']/'status.json')
    phase=state.get('phase','prepared');reports=[]
    for stage in plan['stages']:
        for case in stage['cases']:
            result=read(ROOT/case['report'])
            if result:reports.append((case,result))
    rows=''.join(f'<tr><td>{escape(c["name"])}</td><td>{r["max_total_error_uV"]:.3f}</td><td>{r["max_tracking_error_uV"]:.3f}</td><td>{r["max_refinement_uV"]:.3f}</td><td><a href="../{escape(c["report"])}">{"PASS" if r["selected_screen_pass"] else "FAIL"}</a></td></tr>' for c,r in reports)
    queued=' → '.join(escape(s['name']) for s in plan['stages'])
    fragment=f'''<!-- BEGIN STACK5_SEQUENCE -->
<div id="stack5-sequence"><h3>64-column physical candidate — unattended verification</h3>
<p><strong>Status: {escape(phase)}.</strong> Current stage: {escape(state.get('stage','preparing'))}. Independently audited {len(reports)} / {sum(len(s['cases']) for s in plan['stages'])} planned cases. Completed stages: {len(state.get('completed_stages',[]))} / {len(plan['stages'])}. Updated {escape(state.get('updated_at_utc',plan['created_at_utc']))}.</p>
<p>Prior checkpoint commits <code>06889e5</code> and <code>ac7c3e1</code> are pushed. The interrupted three-device batch remains historical evidence. The new 64-column bank contains 898 MOS devices, 512 MIM plates and 64 pixel diodes, with five NMOS capture devices per column and the established ground grid. Its physical DRC/LVS and 64 capture chains are checked separately; the old checkpoint is preserved.</p>
<p>Acquisition is 13 µs with the ADC reset shifted to 15.5 µs within the unchanged 20 µs slots. Each case runs fresh 100/50 ns transients; the coarse run has 192 matched capture/output references. Both runs save physical capacitor terminals and the 256 internal switch nodes. Limits remain 500 µV total/tracking and 10 µV sample/event refinement. The fine transient must also stay below 500 µV against the coarse capture references. A completed simulator run alone does not authorize continuation.</p>
<p><strong>Queue:</strong> {queued}. Later stages launch only after every preceding case passes its independent audit. A measured failure, simulator/auditor failure, source mismatch, low disk reserve or deadline stops progression for review. Active runs in a failed batch finish and retain their evidence. The first batch may take roughly 6–10 hours; this is an estimate. The complete queue can run much longer; new stages stop launching after 48 hours, while an active stage is allowed to finish within its job limits.</p>
<table><caption>Audited results, errors in µV. Pending cases carry no pass claim.</caption><thead><tr><th>Case</th><th>Total</th><th>Tracking</th><th>Sample refinement</th><th>Result</th></tr></thead><tbody>{rows}</tbody></table>
<p>Failures: {escape(json.dumps(state.get('failures',{})))}. The original bank's process failures remain historical evidence; passing selected candidate cases does not establish full-chip or exhaustive process qualification. Diode/MIM, supply/wire and non-typical illumination coverage remain open.</p>
<p><a href="../{escape(str(a.plan.resolve().relative_to(ROOT)))}">Exact launch plan</a> · <a href="../{escape(plan['output'])}/status.json">Live progress</a> · <a href="../verification/compact-bank-stack5-sequence.json">Persistent profile</a> · <a href="../{escape(plan['layout'])}/physical-audit.json">New physical audit</a></p></div>
<!-- END STACK5_SEQUENCE -->'''
    (ROOT/'docs/compact-bank-stack5-sequence-fragment.html').write_text(fragment+'\n')
    for name in ['64x64-first-silicon-section.html','verification-journal.html']:
        p=ROOT/'docs'/name;text=p.read_text()
        if '<!-- BEGIN STACK5_SEQUENCE -->' in text:
            text,count=re.subn(r'<!-- BEGIN STACK5_SEQUENCE -->.*?<!-- END STACK5_SEQUENCE -->',lambda _:fragment,text,flags=re.S);assert count==1
        else:
            assert text.count('<!-- BEGIN STACK5_PREPARATION -->')==1
            text=text.replace('<!-- BEGIN STACK5_PREPARATION -->',fragment+'\n<!-- BEGIN STACK5_PREPARATION -->',1)
        p.write_text(text)
    profile=dict(scope=plan['scope'],plan=str(a.plan.resolve().relative_to(ROOT)),status=plan['output']+'/status.json',layout=plan['layout'],phase=phase,stage=state.get('stage'),completed_stages=state.get('completed_stages',[]),audited=state.get('audited',{}),failures=state.get('failures',{}),full_bank_accuracy_qualified=False,full_chip_qualified=False)
    (ROOT/'verification/compact-bank-stack5-sequence.json').write_text(json.dumps(profile,indent=2)+'\n')
    handoff=ROOT/'PICK_UP_HERE.md';text=handoff.read_text()
    status=f'''<!-- BEGIN STACK5_LIVE -->
## Current unattended 64-column sequence — {phase}

Five-device correction following the reviewed three-device timeout/FF failure. Live status:
`{plan['output']}/status.json`. Exact plan: `{a.plan.resolve().relative_to(ROOT)}`.
Stage: **{state.get('stage','preparing')}**; reviewed cases: **{len(reports)} / {sum(len(s['cases']) for s in plan['stages'])}**.
Controller container: `{plan['container']}`. Inspect this status and container
before launching anything else. Last update: {state.get('updated_at_utc',plan['created_at_utc'])}.

Physical candidate: `{plan['layout']}`, 898 MOS/512 MIM/64 diodes. The new v6
runner uses 13 µs acquisition and saves all four internal nodes of every capture
stack. New auditor: `report-bank-stack5.py`. Frozen dependencies are pinned in
the plan. Do not edit them while the sequence or its evidence is retained.
Queue: {queued}. Each stage must pass all independent audits to advance.
Failure stops later stages; running members of that batch finish. No full-chip
qualification is claimed. Twelve fresh small port/far controls and their references were independently
audited before launch. Read the overview section
`stack5-sequence` and persistent profile for results. Earlier handoff states below
are historical. Failures: `{json.dumps(state.get('failures',{}))}`.
<!-- END STACK5_LIVE -->
'''
    if '<!-- BEGIN STACK5_LIVE -->' in text:text=re.sub(r'<!-- BEGIN STACK5_LIVE -->.*?<!-- END STACK5_LIVE -->\n?',lambda _:status,text,flags=re.S)
    else:
        head,body=text.split('\n',1);text=head+'\n\n'+status+'\n'+body.lstrip()
    handoff.write_text(text)
    for name in ['update-overview-sections.py','update-verification-journal.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/name)],check=True)
if __name__=='__main__':main()
