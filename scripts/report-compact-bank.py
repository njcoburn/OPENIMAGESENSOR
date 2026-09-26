"""Publish and archive the compact two-column shared-bank development evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True);p.add_argument('--matrix',type=Path,required=True)
    p.add_argument('--checkpoint',type=Path)
    a=p.parse_args();layout=a.layout.resolve();matrix=a.matrix.resolve()
    physical=json.loads((layout/'verification.json').read_text());electrical=json.loads((matrix/'report.json').read_text())
    assert physical['columns']==2 and electrical['all_checks_pass']
    assert physical['gds_sha256']==electrical['layout_gds_sha256']==sha(layout/'bank.gds')
    for name,digest in physical['hashes'].items():assert sha(layout/name)==digest,name
    assert physical['magic_drc_errors']==0 and len(ET.parse(layout/'main-drc.lyrdb').getroot().find('items'))==0
    for name in ['direct','collapsed']:assert 'Circuits match uniquely' in (layout/f'{name}-lvs.log').read_text()
    results=list(matrix.glob('*/result.json'))
    assert len(results)==electrical['main_transients']+electrical['placement_transients']==100
    fallback=0;reference_count=0
    for path in results:
        result=json.loads(path.read_text());assert result['completed']
        assert result['layout_gds_sha256']==physical['gds_sha256']
        assert sha(path.parent/'tile.spice')==result['model_sha256']
        for directory in [path.parent/'transient',*path.parent.glob('*reference')]:
            execution=json.loads((directory/'execution.json').read_text())
            assert execution['completed'] and execution['deck_sha256']==sha(directory/'test.spice')
            log=(directory/'ngspice.log').read_text()
            assert not re.search(r'timestep too small|aborted|^Error|no such command',log,re.M|re.I)
            if directory.name!='transient':reference_count+=1;fallback+=execution['transient_fallback']
    assert reference_count==electrical['dc_references']==240
    rows=electrical['rows'];maxima={key:max(abs(r[key]) for r in rows) for key in rows[0] if key.endswith('_uV') and not isinstance(rows[0][key],list)}
    maxima['late_minus_first_output_uV']=max(abs(v) for r in rows for v in r['late_minus_first_output_uV'])
    maxima['neighbor_pattern_response_uV']=max(abs(v) for r in electrical['neighbor_pattern_response'] for v in r['neighbor_0_to_240_pA_output_changes_uV'])
    report=dict(scope='Two physically joined pixels/capture columns with shared reference MOS and extracted shared buses; conditional-MIM unfilled development control.',
                physical=physical,electrical=electrical,maxima=maxima,reference_transient_fallbacks=fallback,
                selected_layout=str(layout.relative_to(ROOT)),selected_matrix=str(matrix.relative_to(ROOT)),
                source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [layout/'verification.json',matrix/'report.json']})
    (ROOT/'simulations/compact-bank.json').write_text(json.dumps(report,indent=2)+'\n')
    table='\n'.join(f'| {r["temperature_C"]} | {r["lights_pA"][0]}, {r["lights_pA"][1]} | '
                    f'{r["max_total_capture_readout_error_uV"]:.3f} | {r["physical_timestep_difference_uV"]:.3f} | '
                    f'{r["max_output_placement_difference_uV"]:.4f} | {r["physical_minus_schematic_magnitude_uV"]/1000:.3f} |' for r in rows)
    doc=ROOT/'docs/compact-bank.md'
    doc.write_text(f'''# Compact shared two-column bank — 2026-09-26

**The small shared-bank development screen passes.** Both main DRC checks and
both LVS paths pass, along with 100 transients and 240 independent DC references.
Worst capture/readout error is {maxima['max_total_capture_readout_error_uV']:.3f} µV
against the 500 µV limit. This establishes one simultaneous capture and two
reads per column on a two-column bank. The compact 1×64 bank remains next.

![Actual two-column GDS, shared references and wiring](assets/compact-bank.png)

## Physical circuit

The unchanged 40 µm pixels and 40 pF compact capture columns now share actual
VDD/GND, BIAS/PREF, SC/SCB and BUF metal. Pixel row/reset/VRESET rails also
connect physically; each COL joins its own pixel to its capture column.
One diode-connected NMOS and one PMOS reference are placed outside the repeated
40 µm pitch. The reference resistors remain external fixtures.

Bounds: (−67.56, −117.8)–(80.2, 860.48) µm, or **147.76 × 978.28 µm**, including
reference devices, joins and both pixels. The independently assembled reference
matches 22 MOS, 16 MIM and two diode devices, including exact extracted device
parameters. The raw network contains 293 resistors and 257 capacitors.
Both Magic and KLayout main DRC report zero errors; direct and resistor-collapsed
LVS match. Each pixel's central 18 × 18 µm region is clear of M1–M5 metal.
Density, antenna, CUP and approved optical openings remain outside this screen;
the 2 fF MIM option still needs confirmation for the selected run.

## Shared capture and multiplexed readout

The matrix covers 27/125 °C, five imposed photocurrent pairs, 200/100 ns maximum
steps, and extracted/schematic controls. Patterns are dark/dark, dark/bright,
bright/dark, medium/medium and bright/bright (0/80/240 pA). Both columns give
the expected brightness order, including transitions in both contrast directions.
No measured optical response is assumed.

The fixture retains 3.3 V through 2 Ω, external 500 kΩ/12.4 kΩ bias resistors,
100 Ω behavioral control drivers, 100 pF board load and a 20 pF ADC sample
capacitor. Reference MOS are part of the physical bank extraction. Reset releases
at 220 µs; row selection starts at 1.2 ms and capture opens at 1.4 ms. Pixels are
deselected at 1.402 ms and reset at 1.403 ms. Column 0/1 first samples occur at
1.421999/1.441999 ms; late samples occur at 2.681999/2.701999 ms, with 20 µs
slots and 10 µs acquisition. The saved samples verify complementary controls
and that the other column is deselected.

| °C | Pixel photocurrents (pA) | Capture/readout (µV) | 200→100 ns (µV) | Placement (µV) | Layout–schematic response (mV) |
|---|---|---:|---:|---:|---:|
{table}

For each column, the capture reference freezes both pixels' local diode
voltages immediately before capture opens, closes row/capture and selects that
column's output, then solves DC. Separate output references freeze both STORE
voltages at each sampled time. Thus the total capture/readout metric and output
tracking metric use independently settled references for the same physical
circuit and imposed states. Worst output tracking is
{maxima['max_output_tracking_error_uV']:.3f} µV. All 240 references complete;
{fallback} require the available transient operating-point fallback.

The bare schematic's integrated response differs by up to
**{maxima['physical_minus_schematic_magnitude_uV']/1000:.3f} mV**. Changing only the neighbor from
0 to 240 pA changes a selected physical output by up to
**{maxima['neighbor_pattern_response_uV']:.3f} µV**. These comparisons include shared bias,
supply and integrated pixel-state changes; they are separate from same-state
capture/readout accuracy and are not isolated capacitive crosstalk measurements.
Retain them in model/calibration and bank-scaling work. The first-to-late output
change reaches {maxima['late_minus_first_output_uV']:.3f} µV over 1.26 ms. The observed
reset-window STORE change is at most {maxima['max_storage_reset_window_change_uV']:.3f} µV,
including natural drift rather than isolated causal reset feedthrough.

## Numerical and extraction limits

The raw extraction has 11 negative local shunt corrections. Audited models
conserve the signed total shunts on BIAS, COL0, COL1, SC and SCB while retaining
all resistors, devices and other capacitors. The collapsed capacitance matrix
is conserved within 1e−25 F. RST/VRESET need no negative-shunt approximation
in this two-column extraction. The raw model remains diagnostic.

Forty main transients include both timesteps and schematic controls. Sixty
additional 100 ns runs test all-five-far and each single-net-far placement.
Including the main all-port model, seven of the 32 binary placement combinations
are tested at each temperature/pattern. Worst output/storage placement changes
are {maxima['max_output_placement_difference_uV']:.4f}/{maxima['max_storage_placement_difference_uV']:.4f} µV;
physical/schematic timestep differences are
{maxima['physical_timestep_difference_uV']:.3f}/{maxima['schematic_timestep_difference_uV']:.3f} µV,
all below 10 µV. Every transient and DC trace was independently read back;
completion, finiteness, maximum step, capture/sample values and reference
errors were checked. No UIC initialization or relaxed tolerances were used.

## Next and reproduction

Extend to a compact 1×64 row/bank with actual shared routing. Recheck supply
and reference drops, bus loading, all 64 outputs, independent references,
numerical refinement and shunt sensitivity before repeated multirow operation
and real decoders/drivers. This two-column initialization result does not resolve
the old full-bank timeouts or qualify full-bank loading, startup ramps, repeated
frames, process/wire corners or manufacturing release.

Selected layout: `{layout.relative_to(ROOT)}`.
Selected matrix: `{matrix.relative_to(ROOT)}`. Use fresh directories:

```sh
bash scripts/run-tools.sh python3 scripts/build-compact-bank.py \\
  --columns 2 --out build/compact-bank-new
bash scripts/run-tools.sh python3 scripts/qualify-compact-bank.py \\
  --layout build/compact-bank-new --out build/compact-bank-matrix-new
python3 scripts/report-compact-bank.py \\
  --layout build/compact-bank-new --matrix build/compact-bank-matrix-new
```

The builder accepts 2–64 columns; only the two-column geometry is qualified by
this evidence. The simulation driver supports 2–4 columns and the matrix above
is explicitly two-column. Do not label a larger generated bank qualified until
its corresponding physical and electrical checks have completed.

Docker Desktop was restored by launching its Windows application directly;
the CLI restart had waited for the active Ubuntu WSL processes and was cancelled.
The pinned container then completed these checks without changing Docker settings.

[Machine-readable evidence](../simulations/compact-bank.json) ·
[Checkpoint](../checkpoints/compact-bank/README.md) ·
[Single tile](compact-tile.md) · [Current plan](../COMPLETION_PLAN.md).
''')
    if a.checkpoint:
        checkpoint=a.checkpoint.resolve();checkpoint.mkdir(parents=True,exist_ok=False)
        files={p for base in [layout,matrix] for p in base.rglob('*') if p.is_file()}
        names=['scripts/build-compact-bank.py','scripts/simulate-compact-bank.py','scripts/qualify-compact-bank.py',
               'scripts/report-compact-bank.py','scripts/plot-compact-bank.py','scripts/check-compact-capture.py',
               'scripts/diagnose-capture-transient.py','scripts/run-tools.sh','scripts/split-checkpoint.py',
               'build/compact-capture-v4-20260926/column.gds','build/compact-capture-v4-20260926/verification.json',
               'build/compact-pixel-v1-20260926/pixel.gds','checkpoints/capture-column-preparation/capture-column.spice',
               'docs/compact-bank.md','docs/assets/compact-bank.png','simulations/compact-bank.json',
               'PICK_UP_HERE.md','NEXT_STEPS.md','COMPLETION_PLAN.md']
        files.update(ROOT/name for name in names)
        manifest={str(path.relative_to(ROOT)):sha(path) for path in sorted(files)}
        archive=checkpoint/'evidence.tar.gz'
        with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
            tar.dereference=True
            for name in manifest:tar.add(ROOT/name,arcname=name,recursive=False)
        actual={}
        with tarfile.open(archive,'r|gz') as tar:
            for member in tar:
                assert member.isfile() and member.name not in actual
                actual[member.name]=hashlib.file_digest(tar.extractfile(member),'sha256').hexdigest()
        assert actual==manifest
        (checkpoint/'manifest.json').write_text(json.dumps(dict(files=manifest,archive_sha256=sha(archive)),indent=2)+'\n')
        (checkpoint/'README.md').write_text('''# Compact shared two-column bank — 2026-09-26

Contains the joined two-column GDS, physical audits, raw/audited models,
100 matrix transients and 240 references, input geometry, source snapshots
and handoff. Every archive member was read back and SHA-256 checked.
Read [the report](../../docs/compact-bank.md) for scope and limitations.
This is one capture/two reads per column, not a full bank or tapeout pass.
''')
        subprocess.run([sys.executable,str(ROOT/'scripts/split-checkpoint.py'),str(checkpoint)],check=True)
        print(f'Verified {len(actual)} archive members')
    print(f'Published {doc.relative_to(ROOT)}')


if __name__=='__main__':main()
