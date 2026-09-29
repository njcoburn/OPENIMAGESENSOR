"""Audit the 16-column reference qualification and render its overview section."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def dc_values(path):
    with path.open('rb') as handle:
        header=b''
        while True:
            line=handle.readline();assert line, 'Incomplete DC trace'
            if line==b'Binary:\n':break
            header+=line
        assert b'Flags: real' in header
        names=[line.split()[1].lower() for line in header.decode().split('Variables:\n')[1].splitlines() if line.strip()]
        values=struct.unpack(f'{len(names)}d',handle.read())
        assert all(math.isfinite(v) for v in values)
        return dict(zip(names,values))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--control',type=Path,required=True)
    p.add_argument('--original-control',type=Path,required=True)
    p.add_argument('--refined',type=Path,required=True)
    p.add_argument('--events',type=Path,required=True)
    p.add_argument('--settling',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--candidate-layout',type=Path,required=True)
    p.add_argument('--candidate-events',type=Path,required=True)
    p.add_argument('--geometry-audit',type=Path,required=True)
    a=p.parse_args();evidence=set()
    def read(d):
        evidence.update(f for f in d.rglob('*') if f.is_file())
        return json.loads((d/'result.json').read_text())
    r=read(a.run);control=read(a.control);original=read(a.original_control)
    assert r['completed'] and r['columns']==16 and r['references_requested']
    assert r['reference_progress']==dict(completed=48,expected=48)
    assert len(r['capture_references'])==16 and len(r['samples'])==32
    audit=r['transient_reuse'];manifest=ROOT/audit['evidence_manifest']
    assert sha(manifest)==audit['evidence_manifest_sha256']
    evidence.add(manifest)
    hashes=json.loads(manifest.read_text())['evidence_hashes'];source=ROOT/audit['source_directory']
    for name,digest in audit['source_hashes'].items():
        assert sha(source/name)==digest==hashes[str((source/name).relative_to(ROOT))]
        evidence.add(source/name)
    for name in ['test.spice','execution.json','ngspice.log','stream.raw']:
        assert sha(a.run/'transient'/name)==audit['source_hashes']['transient/'+name]
    assert sha(a.run/'tile.spice')==r['model_sha256']==audit['source_hashes']['tile.spice']
    old=json.loads((source/'result.json').read_text())
    assert old['capture_state']==r['capture_state']
    for x,y in zip(old['samples'],r['samples']):assert x['values']==y['values']
    def check_reference(directory,ref):
        ex=ref['execution'];assert ex['completed'] and not ex['timed_out'] and not ex['errors'] and ex['returncode']==0
        assert ex==json.loads((directory/'execution.json').read_text())
        assert sha(directory/'test.spice')==ex['deck_sha256']
        values=dc_values(directory/'op.raw')
        for name,v in ref['values'].items():assert values[f'v({name.lower()})']==v
    for c,ref in enumerate(r['capture_references']):check_reference(a.run/f'capture{c}-reference',ref)
    rows=[]
    for s in r['samples']:
        check_reference(a.run/f'{s["slot"]}{s["column"]}-output-reference',s['output_reference'])
        capture=r['capture_references'][s['column']]['values']['HOLD']
        assert s['total_capture_readout_error_V']==s['values']['HOLD']-capture
        assert s['output_tracking_error_V']==s['values']['HOLD']-s['output_reference']['values']['HOLD']
        rows.append(dict(column=s['column'],scan=s['slot'],hold_V=s['values']['HOLD'],
            capture_readout_error_uV=s['total_capture_readout_error_V']*1e6,
            output_tracking_error_uV=s['output_tracking_error_V']*1e6))
    worst=max(abs(s['capture_readout_error_uV']) for s in rows)
    tracking=max(abs(s['output_tracking_error_uV']) for s in rows)
    assert abs(worst-r['max_total_capture_readout_error_V']*1e6)<1e-12
    assert abs(tracking-r['max_output_tracking_error_V']*1e6)<1e-12
    assert r['capture_readout_pass']==(worst<500) and r['tracking_pass']==(tracking<500)
    assert control['completed'] and original['completed']
    assert control['capture_state']==original['capture_state']
    for x,y in zip(control['capture_references'],original['capture_references']):assert x['values']==y['values']
    for x,y in zip(control['samples'],original['samples']):
        assert x['values']==y['values'] and x['output_reference']['values']==y['output_reference']['values']
    fine=read(a.refined);events=read(a.events);settling=read(a.settling)
    assert fine['completed'] and fine['reference_progress']==dict(completed=48,expected=48)
    for key in ['columns','model_sha256','layout_gds_sha256','solver','method','driver_form','temperature_C','lights_pA','readout_slots','stop_s']:
        assert fine[key]==r[key], key
    assert r['step_ns']==200 and fine['step_ns']==100
    for c,ref in enumerate(fine['capture_references']):check_reference(a.refined/f'capture{c}-reference',ref)
    for sample in fine['samples']:
        check_reference(a.refined/f'{sample["slot"]}{sample["column"]}-output-reference',sample['output_reference'])
        capture=fine['capture_references'][sample['column']]['values']['HOLD']
        assert sample['total_capture_readout_error_V']==sample['values']['HOLD']-capture
        assert sample['output_tracking_error_V']==sample['values']['HOLD']-sample['output_reference']['values']['HOLD']
    changes=[]
    for old,new in zip(r['samples'],fine['samples']):
        assert (old['slot'],old['column'],old['time_s'])==(new['slot'],new['column'],new['time_s'])
        changes.extend(abs(v-new['values'][n])*1e6 for n,v in old['values'].items())
    refinement=max(changes)
    fine_worst=max(abs(s['total_capture_readout_error_V'])*1e6 for s in fine['samples'])
    fine_tracking=max(abs(s['output_tracking_error_V'])*1e6 for s in fine['samples'])
    assert fine['capture_readout_pass']==(fine_worst<500) and fine['tracking_pass']==(fine_tracking<500)
    assert events['physical_mim_probes'] and events['source']==str(a.refined)
    assert settling['all_completed'] and settling['source']==str(a.run)
    for diagnostic in [events,settling]:
        for path,digest in diagnostic['evidence_hashes'].items():
            assert sha(ROOT/path)==digest
            evidence.add(ROOT/path)
    last=events['columns'][14];assert last['column']==14
    event_values={event['event']:event['values'] for event in last['events']}
    row_shift={n:(event_values['after_row_off'][n]-event_values['before_row_off'][n])*1e6
               for n in ['STORE14','mim_average_ground_V','mim_average_differential_V']}
    settling_change=max(ref['max_saved_voltage_change_uV'] for ref in settling['references'])
    candidate=read(a.candidate);candidate_events=read(a.candidate_events)
    geometry=read(a.geometry_audit)
    assert geometry['only_ground_bus_rectangle_changed'] and geometry['reference_identical']
    assert geometry['revised']==str(a.candidate_layout) and geometry['changed_layers']==['46/0']
    for path,digest in geometry['evidence_hashes'].items():
        assert sha(ROOT/path)==digest;evidence.add(ROOT/path)
    layout=json.loads((a.candidate_layout/'verification.json').read_text())
    evidence.update(f for f in a.candidate_layout.rglob('*') if f.is_file())
    assert candidate['completed'] and candidate['reference_progress']==dict(completed=48,expected=48)
    assert layout['ground_bus_width_um']==8 and layout['direct_and_resistor_collapsed_lvs']
    assert layout['magic_drc_errors']==layout['klayout_main_drc_errors']==0
    assert (layout['mos'],layout['mim'],layout['diodes'])==(162,128,16)
    assert sha(a.candidate_layout/'bank.gds')==layout['gds_sha256']==candidate['layout_gds_sha256']
    assert sha(a.candidate/'tile.spice')==candidate['model_sha256']==sha(a.candidate_layout/'rc-port.spice')
    for key in ['columns','solver','method','driver_form','temperature_C','lights_pA','readout_slots','stop_s','step_ns']:
        assert candidate[key]==fine[key], key
    for c,ref in enumerate(candidate['capture_references']):check_reference(a.candidate/f'capture{c}-reference',ref)
    for sample in candidate['samples']:
        check_reference(a.candidate/f'{sample["slot"]}{sample["column"]}-output-reference',sample['output_reference'])
        capture=candidate['capture_references'][sample['column']]['values']['HOLD']
        assert sample['total_capture_readout_error_V']==sample['values']['HOLD']-capture
        assert sample['output_tracking_error_V']==sample['values']['HOLD']-sample['output_reference']['values']['HOLD']
    candidate_worst=max(abs(s['total_capture_readout_error_V'])*1e6 for s in candidate['samples'])
    candidate_tracking=max(abs(s['output_tracking_error_V'])*1e6 for s in candidate['samples'])
    assert candidate['capture_readout_pass']==(candidate_worst<500) and candidate['tracking_pass']==(candidate_tracking<500)
    candidate_pass=candidate['capture_readout_pass'] and candidate['tracking_pass']
    assert candidate_events['physical_mim_probes'] and candidate_events['source']==str(a.candidate)
    for path,digest in candidate_events['evidence_hashes'].items():
        assert sha(ROOT/path)==digest;evidence.add(ROOT/path)
    ce={event['event']:event['values'] for event in candidate_events['columns'][14]['events']}
    candidate_row_shift={n:(ce['after_row_off'][n]-ce['before_row_off'][n])*1e6 for n in row_shift}
    reference_seconds=sum(ref['execution']['seconds'] for ref in r['capture_references'])+sum(s['output_reference']['execution']['seconds'] for s in r['samples'])
    report=dict(scope=__doc__,selected_run=str(a.run),transient_reuse=audit,
        temperature_C=r['temperature_C'],step_ns=r['step_ns'],lights_pA=r['lights_pA'],
        references=48,samples=rows,max_capture_readout_error_uV=worst,max_output_tracking_error_uV=tracking,
        nominal_alternating_screen_pass=bool(r['capture_readout_pass'] and r['tracking_pass']),
        two_column_reuse_regression_exact=True,source_transient_seconds=r['transient']['seconds'],
        reference_workers=r['reference_workers'],sum_reference_execution_seconds=reference_seconds,
        refined_run=str(a.refined),refined_capture_readout_error_uV=fine_worst,
        refined_output_tracking_error_uV=fine_tracking,max_sample_timestep_change_uV=refinement,
        refined_nominal_screen_pass=bool(fine['capture_readout_pass'] and fine['tracking_pass']),
        event_diagnosis=events,reference_settling=settling,
        ground_bus_revision=dict(layout=str(a.candidate_layout),run=str(a.candidate),width_um=8,
            bbox_um=layout['bbox_um'],main_drc_and_both_lvs_pass=True,
            max_capture_readout_error_uV=candidate_worst,max_output_tracking_error_uV=candidate_tracking,
            nominal_screen_pass=candidate_pass,column14_row_off_changes_uV=candidate_row_shift,
            samples=[dict(column=s['column'],scan=s['slot'],hold_V=s['values']['HOLD'],
                          capture_readout_error_uV=s['total_capture_readout_error_V']*1e6,
                          output_tracking_error_uV=s['output_tracking_error_V']*1e6) for s in candidate['samples']],
            events=candidate_events,geometry_audit=geometry,full_qualification=False),
        full_16_column_qualification=False,full_64_column_qualification=False,
        limits=['One capture, two reads per column','Typical process, 27 C, alternating 0/240 pA only',
                'Hot, shunt-placement and other-pattern checks still required for 16 columns',
                'No 64x64 assembly, repeated rows, real decoder/driver or tapeout qualification'],
        evidence_hashes={str(f.resolve().relative_to(ROOT)):sha(f) for f in sorted(evidence)})
    (ROOT/'simulations/compact-bank-16-qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    table=''
    for c in range(16):
        first,last=[s for s in rows if s['column']==c]
        assert first['scan']=='first' and last['scan']=='last'
        table+=f'<tr><th>{c}</th><td>{r["lights_pA"][c]:g}</td><td>{first["capture_readout_error_uV"]:.3f}</td><td>{last["capture_readout_error_uV"]:.3f}</td><td>{max(abs(first["output_tracking_error_uV"]),abs(last["output_tracking_error_uV"])):.3f}</td></tr>'
    outcome='passes' if report['nominal_alternating_screen_pass'] else 'fails'
    candidate_outcome='passes' if candidate_pass else 'fails'
    next_action=('Qualify the revised bank at hot temperature, refine its timestep and test other patterns/shunt placements.'
                 if candidate_pass else 'Continue correcting shared-ground movement; the first routing revision still fails nominal accuracy.')
    html=f'''<section id="compact-bank-16"><h2>16-column trace: independent reference qualification</h2>
<p><strong>Later follow-up:</strong> <a href="#compact-bank-16-screen">the expanded thermal/pattern screen</a> records subsequent checks and current remaining gates. The measurements below retain the original routing-correction scope.</p>
<p><strong>Latest physical revision: the 8 µm M4 ground bus {candidate_outcome} the nominal alternating-pattern screen.</strong> Its 100 ns transient and 48 independent references give <strong>{candidate_worst:.3f} µV</strong> worst total capture/readout error and <strong>{candidate_tracking:.3f} µV</strong> output tracking. Both main DRC checks and both LVS paths pass with the same 162 MOS, 128 MIM plates and 16 diodes. Only the shared ground-bus width changes, from 2 to 8 µm; all extracted parasitics remain in the new simulation.</p>
<p>A direct GDS layer-difference audit confirms that only the intended M4 rectangle changes; all labels and other geometry match, and the independent reference netlist is byte-identical. The 16-column bounding box grows by 1.8 µm in width to 709.56 × 978.28 µm. Pixel pitch, optical openings and storage-plate geometry are unchanged. This revision has not yet been applied to the 64-column bank.</p>
<p><strong>Original 2 µm ground bus, 27 September 2026: the nominal alternating-pattern screen {outcome}.</strong> All 16 capture references and 32 output references complete. Worst total capture/readout error is <strong>{worst:.3f} µV</strong>; worst output tracking error is <strong>{tracking:.3f} µV</strong>. Both criteria use a 500 µV limit.</p>
<figure><img src="assets/compact-bank-16-ground.png" alt="Per-column accuracy and storage-plate ground movement for the original and wider ground buses at 100 ns" style="max-width:100%"><figcaption>Controlled physical routing comparison. Only the M4 ground bus is widened; the layout is re-extracted and its full parasitics are retained.</figcaption></figure>
<p>The previously completed 3 ms transient is reused without rerunning its {r['transient']['seconds']:.1f}-second scan. Prior manifest hashes verify the original trace, model, deck, settings and logs; the regenerated fixture must match apart from its tile-file location. The trace is copied, rechecked for finite/monotonic samples and complete duration, and its selection controls are checked again. Independent DC references are newly simulated, with four separate solves at a time and unchanged devices, parasitics, drivers and tolerances.</p>
<p>The two-column reuse regression reproduces every saved sample and all six reference results exactly. Eight corruption/compatibility tests and six schedule/partial-trace regressions pass. The first control attempt correctly rejected an older report's missing method field; support for its implicit trapezoidal default was added while retaining exact deck comparison.</p>
<details><summary>Original 2 µm bus: all 16 columns, signed error in both scans</summary><table><thead><tr><th>Column</th><th>Light, pA</th><th>First scan, µV</th><th>Late scan, µV</th><th>Worst output tracking, µV</th></tr></thead><tbody>{table}</tbody></table></details>
<p><strong>Original-layout refinement:</strong> a fresh 100 ns transient and all 48 new references give {fine_worst:.3f} µV worst total error and {fine_tracking:.3f} µV output tracking. The maximum difference at matching saved sample terminals is {refinement:.3f} µV. Extending three selected reference fallback endpoints from 400 µs to 1 ms changes saved voltages by at most {settling_change:.6f} µV; the capture reference converges directly. These checks do not resolve the nominal accuracy failure.</p>
<p><strong>Event diagnosis:</strong> the largest storage shift coincides with row deselection at 1.402 ms. In the original layout at column 14, STORE shifts {row_shift['STORE14']:.3f} µV across that window; the mean physical MIM ground moves {row_shift['mim_average_ground_V']:.3f} µV, while voltage across the plates changes {row_shift['mim_average_differential_V']:.3f} µV. With the wider bus, the corresponding STORE/ground/across-plate changes are {candidate_row_shift['STORE14']:.3f} / {candidate_row_shift['mim_average_ground_V']:.3f} / {candidate_row_shift['mim_average_differential_V']:.3f} µV. Both traces include actual extracted storage-plate terminals.</p>
<p><strong>Scope:</strong> typical process, 27 °C, alternating 0/240 pA, one capture and two reads per column. The original layout's columns 12 and 14 fail the 500 µV capture/readout limit in both scans. This is not full 16-column qualification or a 64×64 tapeout pass. At this checkpoint, hot operation, revised-bank timestep/pattern/placement and supply/reference-drop checks remained open; the later follow-up records subsequent results.</p>
<p>Next at this checkpoint: {next_action} Then advance to full-bank accuracy. The earlier 900-second 64-column attempt reached only 14 of 128 scheduled readout instants. Real addressing/drivers, repeated rows, full-chip assembly and manufacturing gates follow.</p>
<p><a href="../simulations/compact-bank-16-qualification.json">Per-sample results and evidence hashes</a> · <a href="compact-bank-16.md">Reproduction and limits</a> · <a href="../NEXT_STEPS.md">Next steps</a>. Raw traces remain local in <code>build/</code>; no purchase, submission or full-chip qualification is implied.</p></section>'''
    (ROOT/'docs/compact-bank-16-section.html').write_text(html+'\n')
    print(json.dumps({k:report[k] for k in ['references','max_capture_readout_error_uV','max_output_tracking_error_uV','nominal_alternating_screen_pass']},indent=2))
    print(json.dumps(dict(revised_capture_readout_error_uV=candidate_worst,
                          revised_output_tracking_error_uV=candidate_tracking,revised_nominal_screen_pass=candidate_pass),indent=2))


if __name__=='__main__':main()
