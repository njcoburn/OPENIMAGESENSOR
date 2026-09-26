"""Publish and checkpoint the compact isolated capture-column evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True)
    p.add_argument('--matrix',type=Path,required=True)
    p.add_argument('--capacitance',type=Path,required=True)
    p.add_argument('--placement',type=Path,required=True)
    p.add_argument('--checkpoint',type=Path)
    a=p.parse_args()
    layout,matrix,capacitance,placement=[v.resolve() for v in [a.layout,a.matrix,a.capacitance,a.placement]]
    load=lambda path:json.loads(path.read_text())
    physical=load(layout/'verification.json');checks=load(layout/'compact-checks.json')
    build=load(layout/'build.json');output_width=build['output_width_um']
    x0,y0,x1,y1=map(float,re.findall(r'-?\d+(?:\.\d+)?',build['bbox_um']))
    vdd_width=build.get('vdd_width_um',2)
    electrical=load(matrix/'report.json');audit=load(matrix/'audit.json')
    cap=load(capacitance/'report.json');sensitivity=load(placement/'report.json')
    for name,digest in physical['hashes'].items():assert sha(layout/name)==digest,name
    for name,digest in physical['placement_model_hashes'].items():assert sha(layout/(name+'.spice'))==digest,name
    for name,digest in checks['hashes'].items():assert sha(layout/name)==digest,name
    for name,digest in electrical['model_sha256'].items():assert sha(matrix/(name+'.spice'))==digest,name
    for model,file,sub in [('rc','rc-port.spice','flat'),('rcfar','rc-far.spice','flat'),('physical','reference.spice','reference')]:
        expected=(layout/file).read_text().replace('.subckt '+sub+' ','.subckt '+model+' ').replace('.ends '+sub,'.ends '+model)
        assert (matrix/(model+'.spice')).read_text()==expected
    for net in ['col','bias']:
        expected=(layout/f'rc-{net}-far.spice').read_text().replace('.subckt flat ','.subckt rc ').replace('.ends flat','.ends rc')
        assert (placement/net/'rc.spice').read_text()==expected
    assert cap['source_sha256']==sha(layout/'direct.spice') and cap['passed']
    assert all(checks[key] for key in ['main_drc_pass','direct_and_rc_collapsed_lvs_pass','abutment_main_drc_pass',
                                      'default_geometry_xor_empty_all_layers','default_direct_netlist_byte_identical'])
    assert all(electrical[key] for key in ['complete','tracking_pass','timestep_pass','placement_pass','reference_duration_pass','schematic_shift_under_500uV'])
    assert audit['samples_recomputed_exactly'] and audit['max_steps_verified']
    assert sensitivity['passed'] and sensitivity['transient_runs']==12
    assert electrical['transient_runs']==48
    m=electrical['maxima']
    report=dict(scope='Isolated compact seven-MOS/eight-MIM capture column; conditional 2 fF option; no pixel join or shared bank.',
                physical=physical,geometry_checks=checks,electrical=electrical,fixture_audit=audit,
                capacitor_control=cap,independent_placement=sensitivity,
                total_transients=60,dc_references=36,build=build,
                selected_layout=str(layout.relative_to(ROOT)),selected_matrix=str(matrix.relative_to(ROOT)),
                source_hashes={str(path.relative_to(ROOT)):sha(path) for path in
                    [layout/'verification.json',layout/'compact-checks.json',matrix/'report.json',matrix/'audit.json',
                     capacitance/'report.json',placement/'report.json']})
    (ROOT/'simulations/compact-capture.json').write_text(json.dumps(report,indent=2)+'\n')
    rows=[]
    for temp in [27,125]:
        values=[r for r in electrical['comparisons'] if r['temperature_C']==temp]
        maxima=[max(abs(r[key]) for r in values)*1e6 for key in
                ['rc_tracking_error_V','rc_minus_ideal_V','max_timestep_difference_V','placement_difference_V']]
        rows.append(f'| {temp} | '+' | '.join(f'{v:.4f}' for v in maxima)+' |')
    table='\n'.join(rows)
    captable='\n'.join(f'| {r["temperature_C"]} | {r["measured_pF"]:.9f} | {abs(r["measured_leakage_A"])*1e15:.6f} |' for r in cap['results'])
    shunts=', '.join(f'{r["net"]}: {r["total_fF"]:.5f} fF' for r in physical['capacitance_approximations'])
    fallback=sum(r['uses_transient_fallback'] for r in audit['references'])
    doc=ROOT/'docs/compact-capture.md'
    doc.write_text(f'''# Compact 40 pF capture column — 2026-09-26

**Follow-up:** the [physically joined tile](compact-tile.md) now passes its
single-capture/two-read development screen. Shared multi-column work is next.

**A 40 µm-pitch isolated capture column now passes scoped physical and electrical
checks.** The candidate occupies {x1-x0:g} × {y1-y0:g} µm, with seven unchanged transistor
devices and eight 32 × 77.76 µm MIM plates. All 60 bounded transients and
36 DC reference solves complete. This is an isolated-column result; the pixel
join, shared bank and full 64×64 camera remain unimplemented.

## Geometry and fit

- Magic and KLayout main DRC: zero violations. Direct and resistor-collapsed LVS
  both match the independently constructed transistor/MIM reference.
- Two columns at 40 µm pitch also pass KLayout main DRC. They have no shared
  routing; this is an abutment-spacing control, not a two-column bank.
- Bounds: ({x0:g}, {y0:g})–({x1:g}, {y1:g}) µm. A 64-column pitch envelope would be
  2560 × {y1-y0:g} µm, inside the 2700 × 1100 µm bank planning rectangle before
  shared routes, references, controls and margin. Actual bank fit is still open.
- Each plate retains 2488.32 µm² area; the changed perimeter slightly changes
  modeled capacitance. Eight separate bottom-plate islands pass the overlap
  audit, with no lower via overlapping the capacitor plate.
- Ground and VDD trunks are 2 and {vdd_width:g} µm wide with distributed branch contacts;
  buffer/output rails are {output_width:g} µm. Device placement and routing are repacked, not scaled.
- The original generator mode reproduces the earlier qualified column: empty
  polygon XOR on every layer and byte-identical direct-device extraction.

The first compact attempt failed plate-to-routing clearance checks and is
excluded. The accepted candidate raises the plate stack by 20 µm.
The initial 2 µm VDD / 0.6 µm output revision passed tracking but missed the
separate transfer-comparison band (649.315 µV). Narrowing the output alone
reduced the limiting nominal shift to 606.466 µV. A halved-ground-resistance
diagnostic barely changed it; doubling VDD resistance brought both nominal
input extremes inside the band. These modified-netlist controls are diagnostic,
not physical passes. The accepted VDD trunk revision is newly extracted and
qualified with its actual device, resistor and capacitor records. This balance
must be reassessed with the joined tile and full-bank supply network.
Main DRC excludes density, antenna and CUP. No optical device is inside this cell.
The 2 fF MIM option is still conditional on the selected manufacturing run.

## Electrical checks

The inherited single-column fixture uses imposed inputs 1.2/1.6/2.0 V, 27/125 °C,
nominal wire RC, SPARSE, unchanged tolerances, capture at 1.4 ms, first/last
20 µs output slots, 10 µs acquisition, 100 pF board and 20 pF sample loads.
Every main-matrix waveform is finite, monotonic and complete to 2.7 ms; its
maximum timestep and recorded samples were independently audited.

| °C | Tracking (µV) | Layout–ideal schematic (µV) | 100→50 ns (µV) | Both shunts near→far (µV) |
|---|---:|---:|---:|---:|
{table}

Tracking compares the physical output to its own DC reference; its limit is
500 µV. Layout–schematic shift is a separate transfer comparison with the ideal
40 pF schematic. Its additional 500 µV screen passes: **{electrical['schematic_shift_under_500uV']}**.
Timestep and shunt-placement limits are 10 µV.

The 36 DC controls use 200/400 µs optran fallback limits; {fallback} invoke transient
fallback. Direct convergence does not exercise those durations and is not a
longer-settling test. Maximum reference difference is
{m['reference_duration_difference_V']*1e6:.9f} µV against 0.01 µV.

### Extraction approximation

The raw extraction contains {len(physical['negative_parasitic_capacitors'])} negative COL/BIAS shunt corrections and remains
diagnostic. Four models conserve each positive signed net total ({shunts}),
placing each at its port or far resistor node. All {physical['resistors']} resistors, devices,
other shunts and coupling records are retained. The collapsed capacitance
matrix is conserved within 1e−25 F.

The main matrix compares both-near with both-far. Twelve additional 50 ns
transients move COL alone or BIAS alone, covering all four combinations at every
temperature/input condition. Maximum independent output shift:
{sensitivity['max_output_difference_uV']:.6f} µV; maximum over output, storage and buffer nodes:
{sensitivity['max_any_observed_difference_uV']:.6f} µV. This bounds sampled sensitivity
for this fixture, not arbitrary distributed behavior or startup.

### Independent capacitor control

| °C | Measured model capacitance (pF) | Leakage magnitude (fA) |
|---|---:|---:|
{captable}

AC and DC measurements agree with independent area/perimeter/temperature
calculations. These are simulator measurements, not fabricated-device results.
The installed model's voltage-dependent expressions remain inactive.
The capacitor control was run on the first DRC-clean compact revision; its
direct-device netlist is byte-identical to the selected routing revision and
the report checks that hash before reusing the result.

## Next and reproduction

Physically join a compact pixel and capture column, extract the joining wires,
and test coupled reset/capture before scaling. Recheck shunt placement with the
new boundary conditions. Real drivers, repeated/multirow operation, full-column
loading, process/wire corners, noise and manufacturing qualification remain open.
Milestone 1 is still open until the joined tile passes.

Use fresh directories. The selected layout is `{layout.relative_to(ROOT)}`;
the selected matrix is `{matrix.relative_to(ROOT)}`.

```sh
bash scripts/run-tools.sh python3 scripts/build-capture-column.py \\
  --out build/compact-capture-new --compact --wide-power --wide-output \\
  --output-width-um {output_width:g} --vdd-width-um {vdd_width:g}
bash scripts/run-tools.sh python3 scripts/check-compact-capture.py --run build/compact-capture-new
bash scripts/run-tools.sh python3 scripts/check-capture-capacitance.py \\
  --extraction build/compact-capture-new --out build/compact-capacitance-new
bash scripts/run-tools.sh python3 scripts/qualify-capture-column.py \\
  --extraction build/compact-capture-new --out build/compact-matrix-new
bash scripts/run-tools.sh python3 scripts/audit-capture-column-matrix.py --run build/compact-matrix-new
bash scripts/run-tools.sh python3 scripts/check-compact-capture-placement.py \\
  --extraction build/compact-capture-new --matrix build/compact-matrix-new --out build/compact-placement-new
```

[Machine-readable results](../simulations/compact-capture.json) ·
[Checkpoint](../checkpoints/compact-capture/README.md) ·
[Current plan](../COMPLETION_PLAN.md).
''')
    if a.checkpoint:
        checkpoint=a.checkpoint.resolve();checkpoint.mkdir(parents=True,exist_ok=False)
        roots=[layout,matrix,capacitance,placement,ROOT/'build/capture-column-default-regression-20260926']
        roots+=list((ROOT/'build').glob('compact-capture-v*-20260926'))
        roots+=list((ROOT/'build').glob('compact-capture-matrix-v*-20260926'))
        roots+=list((ROOT/'build').glob('compact-capture-screen-v*-20260926'))
        roots+=list((ROOT/'build').glob('compact-capture-ground-*-20260926'))
        roots+=list((ROOT/'build').glob('compact-capture-vdd-*-20260926'))
        roots+=list((ROOT/'build').glob('compact-capture-placement-v*-20260926'))
        files={p for base in roots for p in base.rglob('*') if p.is_file()}
        names=['layout/capture-primitives.tcl','checkpoints/capture-column-preparation/capture-column.spice',
               'build/capture-column-screen-v2-singlethread-20260925/27-1.6-100/test.spice',
               'build/capture-column-routed-v8-20260925/column.gds',
               'build/capture-column-routed-v8-20260925/direct.spice',
               'build/readout-primitives/bias_nfet.gds','build/layout-probe-verified/nfet_probe.gds',
               'build/buffer-primitives/mirror_pfet.gds','build/buffer-primitives/buffer_pfet.gds',
               'docs/compact-capture.md','simulations/compact-capture.json',
               'PICK_UP_HERE.md','NEXT_STEPS.md','COMPLETION_PLAN.md']
        names += ['scripts/'+name for name in ['build-capture-column.py','verify-capture-column.py',
                  'check-compact-capture.py','check-capture-capacitance.py','qualify-capture-column.py',
                  'diagnose-capture-transient.py','audit-capture-column-matrix.py',
                  'check-compact-capture-placement.py','report-compact-capture.py','run-tools.sh']]
        files.update(ROOT/name for name in names)
        manifest={str(path.relative_to(ROOT)):sha(path) for path in sorted(files)}
        archive=checkpoint/'evidence.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            tar.dereference=True
            for name in manifest:tar.add(ROOT/name,arcname=name,recursive=False)
        actual={}
        with tarfile.open(archive,'r|gz') as tar:
            for member in tar:
                assert member.isfile() and member.name not in actual
                handle=tar.extractfile(member)
                actual[member.name]=hashlib.file_digest(handle,'sha256').hexdigest()
        assert manifest==actual
        (checkpoint/'manifest.json').write_text(json.dumps(dict(files=manifest,archive_sha256=sha(archive)),indent=2)+'\n')
        (checkpoint/'README.md').write_text('''# Compact capture-column checkpoint — 2026-09-26

Includes accepted isolated-column and abutment GDS/DRC/LVS, all 60 completed
transients and 36 references, capacitor controls, raw and audited extraction,
the excluded first layout, default-generator regression, source snapshots,
primitive inputs and handoff. Every archive member was read back and SHA-256
checked. Extract into an empty scratch directory.

[Report and scope](../../docs/compact-capture.md). No physical pixel join,
shared bank, startup or full-chip qualification is implied.
''')
        print(f'Verified {len(actual)} checkpoint files')
    print(f'Published {doc.relative_to(ROOT)}')


if __name__=='__main__':main()
