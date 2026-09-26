"""Verify, publish and optionally checkpoint the compact reset experiment."""
from pathlib import Path
import argparse
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--raw-control', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path)
    args = parser.parse_args()
    run, raw = args.run.resolve(), args.raw_control.resolve()
    manifest = json.loads((run/'manifest.json').read_text())
    for name, digest in manifest.items():
        assert sha(run/name) == digest, name
    report = json.loads((run/'report.json').read_text())
    assert report['passed'] and len(report['electrical']) == 6
    baseline = json.loads((raw/'r1c1-rc/result.json').read_text())
    assert not baseline['completed'] and not baseline['execution']['timed_out']
    assert any('Timestep too small; time = 0.00022001' in e for e in baseline['execution']['errors'])
    assert baseline['model_sha256'] == sha(run/'models/r1c1/rc.spice')
    def normalized(path):
        # Every fixture statement is identical apart from its local include directory.
        text = path.read_text()
        directory = next(line.split()[1].rsplit('/', 1)[0] for line in text.splitlines()
                         if line.startswith('.include ') and line.endswith('/array.spice'))
        return text.replace(directory, '/CASE')
    for mode in ['rc-port', 'rc-gate']:
        d = run/f'r1c1-125-100/r1c1-{mode}'
        assert normalized(raw/'r1c1-rc/transient/test.spice') == normalized(d/'transient/test.spice')
        result = json.loads((d/'result.json').read_text())
        assert result['simulator_sha256'] == baseline['simulator_sha256']
        assert result['tolerances'] == baseline['tolerances']
    report['raw_control'] = baseline
    report['evidence_manifest_sha256'] = sha(run/'manifest.json')
    report['run_directory'] = str(run.relative_to(ROOT))
    target = ROOT/'simulations/compact-reset.json'
    target.write_text(json.dumps(report, indent=2)+'\n')
    table = '\n'.join(f'| {r["case"]} | {r["mode"]} | {r["temperature_C"]} | '
                      f'{r["max_tracking_error_uV"]:.3f} | {r["timestep_difference_uV"]:.6f} | '
                      f'{r["reference_extension_difference_uV"]:.6f} |' for r in report['electrical'])
    placement = max(r['difference_uV'] for r in report['placement_sensitivity'])
    doc = ROOT/'docs/compact-reset.md'
    doc.write_text(f'''# Compact pixel reset follow-up — 2026-09-26

**Next stage completed:** the [compact capture column](compact-capture.md)
now passes isolated checks; the physically joined tile remains next.

**All 12 nominal/hot development transients pass with the audited shunt models
and unchanged 2×2 boundary control.** Six independent extended-reference runs
also pass. The untouched isolated raw model reproduces its reset-edge abort.
This closes the small-cell electrical screen using an explicit capacitance
placement approximation; it does not qualify the raw distributed extraction.

## Controlled change

The isolated reset net contains a +6.29159 fF port shunt and a −0.51561 fF
local-gate correction. The existing strip audit conserves their **5.77598 fF**
signed total, placing it at the reset port or local reset gate in two models.
All resistors, devices, other shunts and coupling capacitors remain identical.
The resistor-collapsed capacitance matrix is conserved to the audit's 1e−25 F
tolerance. The 2×2 raw model contains no negative capacitor and is unchanged.
The physical GDS, aperture audit and previous DRC/LVS evidence are unchanged.

The repeated 125 °C, 100 ns raw control aborts at 220.01 µs. Both positive-shunt
variants complete with identical fixture statements, simulator binary and
tolerances. This isolates the reset-shunt representation as the discriminating
change for this failure; it does not validate the extractor's physical distribution.
The source netlist and failed trace are preserved.

## Electrical checks

Conditions: 27/125 °C, 200/100 ns maximum timestep, existing 50 µs read slots
and 30 µs acquisition. Tracking limit: 500 µV; timestep, placement and reference
duration comparison limits: 10 µV. The 100 ns traces are reused unchanged for
independent matched DC references with optran extended from 200 to 1000 µs.
These are six additional reference sets, not six additional transients.

| Cell | Model | °C | Worst tracking (µV) | 200→100 ns (µV) | 200→1000 µs reference (µV) |
|---|---|---:|---:|---:|---:|
{table}

Worst port-versus-gate sampled output difference: **{placement:.6f} µV**.
All expected samples are present and paired by row, column and sample time.

## Scope and next step

The electrical screen retains schematic readout periphery and imposed controls.
It does not exercise a physical capture column, joined routing, real drivers,
full-column loading, repeated frames, startup, process corners or manufacturing
requirements. The raw isolated model remains diagnostic. Placement sensitivity
must be checked again after physical joining; these results cannot be inherited
by the future 64-column assembly without requalification.

Next: repack the 40 pF capture column to the slot-fit budget, qualify it, then
physically join a small pixel/capture tile. Milestone 1 remains open.
[Original compact layout evidence](compact-pixel.md) ·
[Current plan](../COMPLETION_PLAN.md) ·
[Machine-readable results](../simulations/compact-reset.json).

## Reproduce

Use fresh output directories in the pinned EDA container:

```sh
bash scripts/run-tools.sh python3 scripts/qualify-compact-reset.py \\
  --source build/compact-pixel-v1-20260926 --out build/compact-reset-new
bash scripts/run-tools.sh python3 scripts/simulate-array-strips.py \\
  --source build/compact-pixel-v1-20260926 --output build/compact-reset-raw-new \\
  --cases r1c1 --modes rc --fixture imaging --temperature 125 \\
  --step-ns 100 --timeout 120 --dc-timeout 120
python3 scripts/report-compact-reset.py --run build/compact-reset-new \\
  --raw-control build/compact-reset-raw-new
```

The raw-control command is expected to record the reproduced abort. The report
checks that failure and compares normalized raw/approximated fixture decks.
The completed dated run is `{run.relative_to(ROOT)}`.
Archived evidence: [compact reset checkpoint](../checkpoints/compact-reset/README.md).
''')
    if args.checkpoint:
        checkpoint = args.checkpoint.resolve()
        checkpoint.mkdir(parents=True, exist_ok=False)
        files = {p for base in [run, raw] for p in base.rglob('*') if p.is_file()}
        files.update([Path(__file__).resolve(), ROOT/'scripts/qualify-compact-reset.py',
                      target, doc, ROOT/'PICK_UP_HERE.md', ROOT/'NEXT_STEPS.md',
                      ROOT/'COMPLETION_PLAN.md'])
        expected = {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}
        archive = checkpoint/'evidence.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            tar.dereference = True
            for name in expected:
                tar.add(ROOT/name, arcname=name, recursive=False)
        actual = {}
        with tarfile.open(archive, 'r:gz') as tar:
            for member in tar:
                assert member.isfile() and member.name not in actual
                actual[member.name] = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
        assert actual == expected
        (checkpoint/'manifest.json').write_text(json.dumps(dict(files=expected,
            archive_sha256=sha(archive)), indent=2)+'\n')
        (checkpoint/'README.md').write_text('''# Compact reset checkpoint — 2026-09-26

The archive contains the copied physical/extraction evidence, raw and audited
models, 12 completed transients, six extended-reference sets, the reproduced
raw failure, source snapshots and reports. Every member was read back and
SHA-256 checked. Extract into an empty scratch directory.

Read [the report](../../docs/compact-reset.md) for the approximation and limits.
This is small-cell development evidence, not full-chip or startup qualification.
''')
        print(f'Checkpoint verified: {len(expected)} files')
    print(f'Published {doc.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
