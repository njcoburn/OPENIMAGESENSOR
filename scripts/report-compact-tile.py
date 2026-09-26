"""Publish and preserve the physically joined compact tile's scoped results."""
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
    physical=json.loads((layout/'verification.json').read_text())
    electrical=json.loads((matrix/'report.json').read_text())
    assert electrical['all_checks_pass']
    assert physical['gds_sha256']==electrical['layout_gds_sha256']==sha(layout/'tile.gds')
    for name,digest in physical['hashes'].items():assert sha(layout/name)==digest,name
    assert len(ET.parse(layout/'main-drc.lyrdb').getroot().find('items'))==0
    for name in ['direct','collapsed']:
        assert 'Circuits match uniquely' in (layout/f'{name}-lvs.log').read_text()
    results=list(matrix.glob('*/result.json'));assert len(results)==54
    fallback=0;reference_count=0
    for path in results:
        result=json.loads(path.read_text());assert result['completed']
        assert sha(path.parent/'tile.spice')==result['model_sha256']
        for directory in [path.parent/'transient',*path.parent.glob('*reference')]:
            execution=json.loads((directory/'execution.json').read_text())
            assert execution['completed'] and execution['deck_sha256']==sha(directory/'test.spice')
            log=(directory/'ngspice.log').read_text()
            assert not re.search(r'timestep too small|aborted|^Error|no such command',log,re.M|re.I)
            if directory.name!='transient':
                reference_count+=1;fallback+=execution['transient_fallback']
    assert reference_count==72
    rows=electrical['rows']
    maxima={key:max(abs(r[key]) for r in rows) for key in rows[0] if key.endswith('_uV')}
    report=dict(scope='One physical pixel and capture column with extracted COL/VDD/GND joins; unfilled conditional-MIM development tile.',
                physical=physical,electrical=electrical,maxima=maxima,reference_transient_fallbacks=fallback,
                selected_layout=str(layout.relative_to(ROOT)),selected_matrix=str(matrix.relative_to(ROOT)),
                source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [layout/'verification.json',matrix/'report.json']})
    (ROOT/'simulations/compact-tile.json').write_text(json.dumps(report,indent=2)+'\n')
    table='\n'.join(f'| {r["temperature_C"]} | {r["light_pA"]} | {r["captured_column_V"]:.6f} | '
                    f'{r["max_total_capture_readout_error_uV"]:.3f} | {r["physical_timestep_difference_uV"]:.3f} | '
                    f'{r["max_output_placement_difference_uV"]:.4f} | {r["physical_minus_schematic_magnitude_uV"]/1000:.3f} |' for r in rows)
    doc=ROOT/'docs/compact-tile.md'
    doc.write_text(f'''# Physically joined compact pixel/capture tile — 2026-09-26

**The first joined tile passes its scoped physical, capture/readout and numerical
checks.** All 54 transients and 72 independent DC reference solves complete.
Worst total capture/readout error is {maxima['max_total_capture_readout_error_uV']:.3f} µV
against 500 µV. This is one capture followed by two reads, not a demonstrated
64-column bank, repeated-frame camera or manufacturing pass.

![Actual joined GDS and pixel-to-column routing](assets/compact-tile.png)

## Physical evidence

The unchanged 40 µm pixel and selected compact 40 pF column are physically
connected through COL, VDD and GND routes. Their links are part of the same
flattened extraction, rather than ideal connections between separate models.
The tile contains 10 MOS devices, eight MIM devices and one 20 × 20 µm diode.
Both Magic and KLayout main DRC report zero errors; direct-device and
resistor-collapsed LVS match an independently assembled circuit reference.
The extraction retains all 133 resistors and the audited capacitance network.

Bounds are (−11, −77.8)–(40.2, 860.48) µm: 51.2 × 938.28 µm including
external feed trunks and the pixel. The building blocks retain their 40 µm
pitch; this single tile is not an implemented 64-column floorplan.
The central 18 × 18 µm pixel region remains free of M1–M5 metal. This geometric
audit is not foundry approval for passivation openings, optical fill or packaging.
Density, antenna and CUP decks are excluded; the 2 fF MIM option is conditional.

## Coupled electrical test

The fixture uses schematic shared references, 100 Ω behavioral control drivers,
a 3.3 V source with 2 Ω supply resistance, 100 pF board load and 20 pF ADC sample
capacitance. Typical device models use nominal wire RC at 27/125 °C. Imposed
photocurrents are 0/80/240 pA; no measured optical sensitivity is assumed.

Reset releases at 220 µs. Row selection starts at 1.2 ms; capture opens at
1.4 ms. The pixel is deselected at 1.402 ms and reset at 1.403 ms while the
column retains its captured value. Reads sample at 1.421999 and 2.681999 ms,
using 20 µs slots and 10 µs acquisition. All expected controls and samples pass.
Increasing photocurrent decreases the measured output at both temperatures.

| °C | Photocurrent (pA) | COL before capture (V) | Total capture/readout (µV) | 200→100 ns (µV) | Placement (µV) | Layout–schematic response (mV) |
|---|---:|---:|---:|---:|---:|---:|
{table}

For each physical run, the capture reference freezes the local diode's
differential voltage immediately before capture opens, closes the row/capture/
output paths, and independently solves the settled output. The reported total
error compares both later sampled outputs with that target. Separate references
freeze each sampled STORE voltage and measure output tracking alone; its worst
error is {maxima['max_output_tracking_error_uV']:.3f} µV. All 72 references converge
directly ({fallback} use transient fallback). The 400 µs fallback setting therefore
does not establish an independent longer-settling comparison.

The matched schematic includes the same MIM device models but omits extracted
interconnect. **Its integrated response differs from the physical tile by up to
{maxima['physical_minus_schematic_magnitude_uV']/1000:.3f} mV.** This comparison includes differing integrated
pixel states as well as readout transfer; it is distinct from the same-physical-
circuit capture/readout accuracy test. Absolute schematic equivalence within
500 µV is not demonstrated. Preserve this difference when extending the model
or planning calibration.

The hot late output moves by as much as {max(abs(r['late_minus_first_output_uV']) for r in rows if r['temperature_C']==125):.3f} µV
relative to the first read over the 1.26 ms interval. The total-error limit still
passes. The observed STORE change across the 1.4025–1.405 ms reset window is
at most {maxima['storage_reset_window_change_uV']:.3f} µV; this includes natural drift and is
not an isolated causal measurement of reset feedthrough.

## Extraction and numerical limits

The raw extraction retains five negative local shunt corrections and is
diagnostic. Derived models conserve the positive signed totals separately on
BIAS, COL0, RST0 and VRESET, retaining every resistor, device and other coupling
record. The resistor-collapsed capacitance matrix is conserved within 1e−25 F.

The 24 main transients cover physical and schematic models at both timesteps.
Thirty additional 100 ns transients test all-four-far and each single-net-far
placement. Six placements are tested per temperature/photocurrent, including
the main all-port model; the full 16-combination placement set is not tested.
Worst observed placement differences are {maxima['max_output_placement_difference_uV']:.4f} µV at the output
and {maxima['max_storage_placement_difference_uV']:.4f} µV at storage, against 10 µV.
Both physical and schematic timestep checks pass 10 µV. All raw traces were
independently checked for finiteness, monotonic time, completion, maximum step,
and exact reproduction of stored sample/capture records.

## Next and reproduction

This completes the small joined-tile development screen. The subsequent
[two-column shared-bank control](compact-bank.md) is documented separately.
Continue to the compact 1×64 bank after that shared-control screen. Recheck shared supplies/references, all outputs and
capacitance placement before repeated/multirow operation, full-column loading
and real decoders/drivers. Run-specific MIM/aperture and final-chip release gates
remain open; no tapeout readiness is implied.

Selected geometry: `{layout.relative_to(ROOT)}`.
Selected matrix: `{matrix.relative_to(ROOT)}`. Use fresh directories:

```sh
bash scripts/run-tools.sh python3 scripts/build-compact-tile.py --out build/compact-tile-new
bash scripts/run-tools.sh python3 scripts/qualify-compact-tile.py \\
  --layout build/compact-tile-new --out build/compact-tile-matrix-new
python3 scripts/report-compact-tile.py \\
  --layout build/compact-tile-new --matrix build/compact-tile-matrix-new
```

[Machine-readable evidence](../simulations/compact-tile.json) ·
[Checkpoint](../checkpoints/compact-tile/README.md) ·
[Isolated column](compact-capture.md) · [Current plan](../COMPLETION_PLAN.md).
''')
    if a.checkpoint:
        checkpoint=a.checkpoint.resolve();checkpoint.mkdir(parents=True,exist_ok=False)
        roots=[layout,matrix,ROOT/'build/compact-tile-dark-rc-20260926',ROOT/'build/compact-tile-dark-reference-20260926']
        files={p for base in roots for p in base.rglob('*') if p.is_file()}
        names=['scripts/build-compact-tile.py','scripts/simulate-compact-tile.py','scripts/qualify-compact-tile.py',
               'scripts/report-compact-tile.py','scripts/plot-compact-tile.py','scripts/check-compact-capture.py',
               'scripts/diagnose-capture-transient.py','scripts/run-tools.sh','scripts/split-checkpoint.py',
               'build/compact-capture-v4-20260926/column.gds','build/compact-capture-v4-20260926/verification.json',
               'build/compact-pixel-v1-20260926/pixel.gds','checkpoints/capture-column-preparation/capture-column.spice',
               'docs/compact-tile.md','docs/assets/compact-tile.png','simulations/compact-tile.json',
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
        (checkpoint/'README.md').write_text('''# Physically joined compact tile — 2026-09-26

Contains the joined GDS and physical checks, raw/audited RC models, all 54
matrix transients and 72 references, initial dark controls, source snapshots,
input geometry and handoff. Every archive member was read back and SHA-256
checked. Read [the report](../../docs/compact-tile.md) for scope and limitations.
This is one capture/two reads on one tile, not a full bank or tapeout pass.
''')
        subprocess.run([sys.executable,str(ROOT/'scripts/split-checkpoint.py'),str(checkpoint)],check=True)
        print(f'Verified {len(actual)} archive members')
    print(f'Published {doc.relative_to(ROOT)}')


if __name__=='__main__':main()
