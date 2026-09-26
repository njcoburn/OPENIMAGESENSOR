"""Audit and publish the 2026-09-26 compact pixel and bounded solver evidence."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/'build/compact-pixel-v1-20260926'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    physical = json.loads((BUILD/'verification.json').read_text())
    rows = []
    for case in physical['cases']:
        name = f'r{case["rows"]}c{case["columns"]}'
        d = BUILD/name
        assert digest(d/'strip.gds') == case['gds_sha256']
        assert len(ET.parse(d/'main-drc.lyrdb').getroot().find('items')) == 0
        for model in ['devices','direct-devices']:
            assert 'Circuits match uniquely' in (d/f'{model}-lvs.log').read_text()
        for file,sha in case['hashes'].items():
            assert digest(d/file) == sha
        caps = [line.split() for line in (d/'rc.spice').read_text().splitlines() if line.startswith('C')]
        negative = [c for c in caps if c[3].startswith('-')]
        case['negative_capacitance_records'] = negative
        case['raw_rc_passivity_qualified'] = not negative
        for temperature in [27,125]:
            runs = []
            for step in [200,100]:
                result_path = ROOT/f'build/compact-pixel-imaging-{temperature}-{step}-20260926/{name}-rc/result.json'
                result = json.loads(result_path.read_text())
                assert result['model_sha256'] == digest(d/'rc.spice')
                assert result['temperature_C'] == temperature and result['step_ns'] == step
                if result['completed']:
                    assert result['tracking_screen_pass']
                    assert len(result['samples']) == case['rows']*case['columns']
                else:
                    assert negative, 'Unexpected failure in the positive-capacitance 2x2 control'
                runs.append(result)
            if not all(r['completed'] for r in runs):
                rows.append(dict(case=name,temperature_C=temperature,completed=False,
                                 max_tracking_error_uV=None,max_timestep_difference_uV=None,
                                 samples_per_run=0,raw_rc_passivity_qualified=False,
                                 failures=[dict(step_ns=r['step_ns'],execution=r['execution'])
                                           for r in runs if not r['completed']]))
                continue
            differences = []
            for coarse,fine in zip(runs[0]['samples'],runs[1]['samples']):
                assert (coarse['row'],coarse['column'],coarse['time_s']) == (fine['row'],fine['column'],fine['time_s'])
                differences.append(abs(coarse['capture']['HOLD']-fine['capture']['HOLD']))
            difference = max(differences)
            assert difference < 10e-6
            rows.append(dict(case=name,temperature_C=temperature,completed=True,
                             max_tracking_error_uV=max(r['max_tracking_error_V'] for r in runs)*1e6,
                             max_timestep_difference_uV=difference*1e6,
                             samples_per_run=len(differences), raw_rc_passivity_qualified=not negative))
    bank = []
    for model in ['raw','equivalent']:
        for analysis in ['op','reset']:
            path = ROOT/f'build/bank-{model}-{analysis}-20260926/result.json'
            result = json.loads(path.read_text())
            assert 'seconds' in result, f'Run unfinished: {path}'
            bank.append(dict(model=model,analysis=analysis,completed=result['completed'],
                             timed_out=result['timed_out'],seconds=result['seconds'],
                             points=result.get('points',0),result_sha256=digest(path)))
    report = dict(physical=physical,electrical=rows,bank_solver=bank,
                  scope='Small unfilled compact-pixel development evidence; schematic readout and ideal controls, no physical capture bank or full-chip qualification.',
                  limits=['Isolated r1c1 raw RC has a negative RST shunt and remains diagnostic.',
                          'No density, antenna, cup, foundry aperture approval or optical qualification.',
                          'No compact capture column, physical row-bank join, real decoder or full-array loading.',
                          'Matched output references use the existing 200 us optran-assisted DC fixture; independent reference-duration extension remains open.'])
    (ROOT/'simulations/compact-pixel.json').write_text(json.dumps(report,indent=2)+'\n')
    table = '\n'.join((f'| {r["case"]} | {r["temperature_C"]} | {r["max_tracking_error_uV"]:.3f} | {r["max_timestep_difference_uV"]:.6f} |'
                       if r['completed'] else f'| {r["case"]} | {r["temperature_C"]} | Incomplete | 100 ns transient aborts |') for r in rows)
    banktable = '\n'.join(f'| {r["model"]} | {r["analysis"]} | {r["seconds"]:.2f} | {r["completed"]} | {r["points"]} |' for r in bank)
    document = f'''# Compact 40 µm pixel — 2026-09-26

**Follow-up:** [compact reset qualification](compact-reset.md) passes the isolated
screen with conserved-total shunt models and extends both cells' references.
The raw-model failure below remains diagnostic evidence.

**The first 40 × 40 µm pixel and 2×2 boundary control pass scoped physical checks.**
Docker access is restored. The existing 20 × 20 µm diode and three W=1 µm,
L=0.5 µm transistors are imported unchanged; only placement and routing change.
Both cells pass Magic DRC, KLayout main DRC, direct-device LVS and
resistor-collapsed LVS against independently constructed circuit references.
The 2×2 control contains 12 MOSFETs and four diodes, with distinct row and column nets.

The pixel's fabricated geometry bounds are (−0.2, 2.2)–(40.2, 38.7) µm.
The 0.2 µm overhang joins horizontal buses at 40 µm pitch; this is not a
strictly contained 40 µm square. External supply trunks add 10.3 µm on the left
of the control array. The central 18 × 18 µm region is free of M1–M5 metal.
This geometric aperture audit does not establish legal passivation openings,
fill treatment or optical performance. Density, antenna and cup decks are excluded.

## Extracted electrical screen

Seven of eight imaging transients complete with matched settled output references.
The 2×2 control completes all four 27/125 °C, 200/100 ns runs and passes both
screens. The isolated pixel completes three runs; its hot 100 ns run aborts.
These retain the existing schematic mux/output/ADC fixture and ideal control
sources; there is no physical capture bank in this test. Readout slots are
50 µs, with 30 µs acquisition. Limits are 500 µV tracking and 10 µV refinement.

| Cell | Temperature (°C) | Worst tracking (µV) | 200→100 ns sample difference (µV) |
|---|---:|---:|---:|
{table}

**Isolated-cell limitation:** the r1c1 extraction contains
`C35 RST0.t0 GND -0.51561f`. It is retained unchanged in the diagnostic runs;
passivity is not qualified. Its 125 °C, 100 ns run aborts at the reset edge
(220.01 µs) with a timestep-too-small error. The coarser hot run completes with
24.204 µV tracking error, but is not refinement-qualified. The negative term
is a candidate cause, not an established diagnosis.
The 2×2 extraction has no negative capacitor records.
The output-reference fixture uses its existing 200 µs optran-assisted DC solve;
an independent longer-reference comparison remains open. These results establish
a small development screen, not completion of the compact joined-tile milestone.

## Bounded full-bank solver comparison

| Model | Analysis | Elapsed (s) | Completed | Saved points |
|---|---|---:|---|---:|
{banktable}

The raw and audited resistor-reduced banks retain identical device/capacitor
records and unchanged SPICE tolerances. Each attempt has a 180 s limit; reset
controls request 0.25 ms. The reduction does not resolve initialization in
these attempts. Some independent layout/simulation jobs overlapped, so elapsed
times are timeout evidence, not an isolated performance benchmark. No completed
terminal-voltage comparison or improved convergence is claimed. Use a small
coupled tile next; avoid another open-ended full-bank attempt.

## Reproduce

Use fresh output directories. Physical build:

```sh
bash scripts/run-tools.sh python3 scripts/build-compact-pixel.py --out build/compact-pixel-new
```

Run this for temperatures 27 and 125 and steps 200 and 100, each with a fresh output:

```sh
bash scripts/run-tools.sh python3 scripts/simulate-array-strips.py \\
  --source build/compact-pixel-new --output build/compact-imaging-new \\
  --cases r1c1 r2c2 --modes rc --fixture imaging --temperature 27 \\
  --step-ns 200 --timeout 120 --dc-timeout 120
```

The dated evidence is under `build/compact-pixel-v1-20260926` and
`build/compact-pixel-imaging-*-20260926`. The audit/report command is
`python3 scripts/report-compact-pixel.py`; it validates the dated GDS/netlist
hashes, physical results, sample correspondence and numerical screens.
Machine-readable results: [compact-pixel.json](../simulations/compact-pixel.json).
The [checkpoint](../checkpoints/compact-pixel/README.md) retains source snapshots,
GDS, models, logs, raw traces, references and failed bank attempts.

Next: review isolated reset capacitance; repack the 40 pF capture column;
qualify a small physically joined tile before scaling to 64 columns.
Run-specific MIM and optical requirements remain open.
'''
    (ROOT/'docs/compact-pixel.md').write_text(document)
    print(json.dumps(dict(electrical=rows,bank_solver=bank),indent=2))


if __name__ == '__main__':
    main()
