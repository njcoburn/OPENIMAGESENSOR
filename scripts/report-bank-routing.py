"""Audit and publish the shared-bank routing diagnosis and bounded reset controls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('routing', ROOT/'scripts/diagnose-bank-routing.py')
routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routing)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--resets', type=Path, nargs='+', required=True)
    a = p.parse_args()
    d = a.run.resolve()
    report = json.loads((d/'report.json').read_text())
    source = (d/'original-model.spice').read_text()
    assert source == (ROOT/'build/capture-bank-c64-v2-20260925/rc-port.spice').read_text()
    for source_path, digest in report['source_hashes'].items():
        path = Path(source_path)
        if source_path.startswith('/foss/designs/'):
            path = ROOT/source_path.removeprefix('/foss/designs/')
        assert routing.sha(path) == digest, path
    assert len(report['controls']) == 8
    for r in report['controls']:
        run = d/r['name']
        assert r['completed'] and not r['transient_assisted_initialization']
        assert routing.sha(run/'test.spice') == r['deck_sha256']
        assert routing.sha(run/'model.spice') == r['model_sha256']
        assert routing.read_op(run/'op.raw') == r['values']
        model, _, audit = routing.collapse(source, r['selected_nets'])
        assert model == (run/'model.spice').read_text()
        assert all(r[k] == v for k,v in audit.items())
        ideal = json.loads((ROOT/'build/capture-bank-dc-matrix-20260925/reference-27-1.2/result.json').read_text())['values']
        shifts = [r['values'][f'v(cbuf{c})']-ideal[f'v(cbuf{c})'] for c in range(64)]
        assert shifts == r['buffer_shifts_V']
        assert max(map(abs,shifts)) == r['max_abs_buffer_shift_V']
        assert max(shifts)-min(shifts) == r['buffer_shift_span_V']
    old = json.loads((ROOT/'build/capture-bank-dc-matrix-20260925/rc-port-27-1.2/result.json').read_text())
    full = report['controls'][0]
    assert full['name'] == 'full' and full['values'] == old['values']
    report['control_audit'] = dict(all_raw_results_read_back=True, baseline_bit_exact=True,
        all_selected_contractions_reproduced=True, all_device_parameters_preserved=True)
    report['reset_controls'] = []
    for path in a.resets:
        r = json.loads((path/'result.json').read_text())
        assert 'timed_out' in r, 'Run has not finished'
        for name, digest in r['source_sha256'].items():
            assert routing.sha(path/name) == digest
        original = (path/'original-fixture.spice').read_text()
        deck = (path/'test.spice').read_text()
        for line in original.split('.save ',1)[0].splitlines():
            f = line.split()
            if not f or f[0] in ['.include','.temp'] or line in r['removed_fixture_elements']:
                continue
            expected = line.replace('method=trap','method='+r['method']) if f[0] == '.options' else line
            assert expected in deck.splitlines(), (path, line)
        report['reset_controls'].append(dict(path=str(path), result=r))
    report['interpretation'] = (
        'At 27 C and imposed 1.2 V inputs, selective VDD and PREF contractions reduce '
        'spatial spread. Ground/BIAS-only contractions do not. Combined supply/reference '
        'contraction removes spatial spread but leaves a common physical/ideal offset. '
        'These are static diagnostic counterfactuals; they neither qualify a layout nor '
        'establish transient accuracy, causality at other operating points, or startup.')
    (ROOT/'simulations/bank-routing.json').write_text(json.dumps(report,indent=2)+'\n')
    rows = ['| Idealized wire nets | Largest buffer shift (mV) | Shift span (mV) |',
            '|---|---:|---:|']
    for r in report['controls']:
        rows.append(f"| {', '.join(r['selected_nets']) or 'None (full RC)'} | {r['max_abs_buffer_shift_V']*1e3:.6f} | {r['buffer_shift_span_V']*1e3:.9f} |")
    reset_rows = ['| Bank / integration | Complete to 0.25 ms | Last time (ms) | Runtime (s) |',
                  '|---|---|---:|---:|']
    for entry in report['reset_controls']:
        r = entry['result']
        last = f"{r['last_time_s']*1e3:.9f}" if 'last_time_s' in r else 'No transient data'
        reset_rows.append(f"| {r['model']} / {r['method']} | {r['completed']} | {last} | {r['seconds']:.1f} |")
    md = '''# Shared-bank routing diagnosis — 2026-09-25

**Eight controlled DC experiments identify VDD and PREF routing as contributors
to the nominal equal-input spatial spread.** Every experiment completes by
direct DC solution. All 16 earlier static raw records were independently read
back; repeating the unchanged full-RC control reproduces every saved value
exactly. No layout or transient accuracy pass is claimed.

![Selective routing controls](assets/bank-routing.png)

## Measured local voltages

At 27 °C with every COL imposed at 1.2 V, the original physical bank has
up to **8.059 mV local VDD loss** and **9.023 mV follower ground rise**.
Both are smallest near the center supply feed. The BIAS gate line drops at
most 0.260 mV, while local bias gate–source voltage varies by 5.735 mV.
These are bank-only static measurements, with ideal column sources and the
previous 1 TΩ output load. They do not include the coupled row's switching load.

## Controlled resistance contractions

Each experiment shorts only the selected extracted resistor components, remaps
their device/capacitor terminals, and retains all other resistors and devices.
Capacitors across a contracted node are removed because their voltage is zero.
The 450 MOS and 512 physical MIM devices and parameters are preserved. The
fixture, solver and accuracy tolerances remain unchanged. These diagnostic
models are electrically altered controls, not proposed physical layouts.

'''+ '\n'.join(rows) + '''

The shift span compares the 64 physical-minus-ideal buffer voltages; it is not
a matched capture/readout error. VDD and PREF effects interact, so the changes
in these rows are not additive contributions. Shorting supplies and references
together makes the shifts uniform to about 0.03 nV but leaves a **2.199 mV
common offset**. Remaining local signal/output routing therefore still needs
investigation. The finite loaded output-0 fixture is not translationally
symmetric; this table does not establish calibration or noise performance.
These contraction experiments cover only 27 °C / 1.2 V. The saved local-voltage
analysis also covers all eight earlier temperature/input conditions.

## Coupled reset-edge controls

'''+ '\n'.join(reset_rows) + '''

These bounded controls stop before the 1.4 ms capture event and cannot qualify
readout accuracy. Gear changes the integration method only; circuit sources,
loads and error tolerances are audited against the original fixture. The
reference control retains physical MIM devices with ideal bank wiring and
the full extracted row. Earlier aborted and timed-out runs remain preserved.

The ideal-wire bank crosses reset release and row enable to reach 0.25 ms in
107.8 s. The physical-bank Gear attempt times out after 120 s during operating
point initialization, with no complete transient records. It does not establish
whether Gear can resolve the later reset-edge slowdown. The earlier physical
bank with trapezoidal integration reached only 0.200255 ms in its 600 s budget.
These results narrow the runtime investigation but do not prove a circuit fault.

## Next experiment

Revise the shared VDD distribution and reference feed paths, including the
reference device supply connection and PREF path to the external resistor.
Re-run physical checks and compare the resulting extracted bank with these
static controls. Investigate the remaining common offset and coupled runtime
separately. Then retain the independent capture/output targets, all 64 outputs,
27/125 °C, timestep and shunt-placement gates before claiming qualification.
Row-to-bank joining routes, repeated/multirow operation and real drivers remain
open. No release GDS, carrier, commit or push changed.

## Reproduction and evidence

The diagnosis script uses the Python standard library; omit `--run` to audit
saved results and prepare decks without Docker. Use a fresh output directory:

```sh
bash scripts/run-tools.sh python3 scripts/diagnose-bank-routing.py \\
  --bank build/capture-bank-c64-v2-20260925 \\
  --dc build/capture-bank-dc-matrix-20260925 \\
  --out build/capture-bank-routing-reproduce --run --timeout 60
```

Machine-readable measurements, control audits and exact reset statuses:
`simulations/bank-routing.json`. Evidence: `checkpoints/bank-routing/`.
The earlier [physical-bank checkpoint](capture-bank.md) is unchanged.
'''
    (ROOT/'docs/bank-routing.md').write_text(md)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11,5), layout='constrained')
    labels = {'full':'None (full RC)', 'vdd':'VDD', 'ground':'GND',
              'pref':'PREF', 'supplies-references':'VDD, GND, BIAS, PREF'}
    for name in ['full','vdd','ground','pref','supplies-references']:
        r = next(r for r in report['controls'] if r['name'] == name)
        ax.plot(range(64), [v*1e3 for v in r['buffer_shifts_V']], label=labels[name])
    ax.set(xlabel='Column', ylabel='Physical − ideal buffer voltage (mV)',
           title='Static routing controls: 27 °C, all inputs at 1.2 V')
    ax.grid(alpha=.2)
    ax.legend(title='Idealized wire nets')
    fig.savefig(ROOT/'docs/assets/bank-routing.png',dpi=160)
    plt.close(fig)
    section = '''<section id="bank-routing"><h2>Shared-bank routing diagnosis</h2>
<p>Eight direct-DC controls identify VDD and PREF resistance as contributors to
nominal spatial spread. Combined supply/reference contraction removes the
spread but leaves a 2.199 mV common offset. These are diagnostic altered models;
full readout accuracy remains open.</p>
<img src="assets/bank-routing.png" alt="Static buffer shifts under selective routing controls">
<p><a href="bank-routing.md">Measurements, reset controls and reproduction</a></p></section>
'''
    (ROOT/'docs/bank-routing-section.html').write_text(section)
    print('Audited eight DC controls and reset fixtures; wrote routing report and plot.')


if __name__ == '__main__':
    main()
