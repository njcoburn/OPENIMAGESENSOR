"""Bounded compact-pixel reset-shunt experiment in the pinned EDA container.

Preserves raw evidence; uses the existing signed-total port/gate approximation.
This development screen does not qualify distributed extraction or startup.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, log):
    with log.open('w') as handle:
        result = subprocess.run([sys.executable, *map(str, command)], cwd=ROOT,
                                stdout=handle, stderr=subprocess.STDOUT, timeout=1800)
    assert result.returncode == 0, f'Failed: {log}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    snapshots = out/'scripts'
    snapshots.mkdir()
    for name in ['qualify-compact-reset.py', 'audit-array-strip-rc.py',
                 'prepare-array-strips.py', 'simulate-array-strips.py',
                 'diagnose-functional-camera.py', 'run-tools.sh']:
        shutil.copyfile(ROOT/'scripts'/name, snapshots/name)
    shutil.copyfile(ROOT/'circuits/output-buffer.spice', out/'output-buffer.spice')
    models = out/'models'
    shutil.copytree(source, models)
    run([ROOT/'scripts/audit-array-strip-rc.py', models], out/'audit.log')
    audits = {}
    for case in ['r1c1', 'r2c2']:
        d = models/case
        audit = json.loads((d/'rc-audit.json').read_text())
        assert sha(d/'rc.spice') == sha(source/case/'rc.spice')
        original = (d/'rc.spice').read_text().splitlines()
        removed = {r[0] for correction in audit['corrections']
                   for r in correction['original_shunts']}
        for mode in ['rc-port', 'rc-gate']:
            updated = (d/f'{mode}.spice').read_text().splitlines()
            assert [line for line in original if not line or line.split()[0] not in removed] == [
                line for line in updated if not line.startswith('CFIX')]
            assert sha(d/f'{mode}.spice') == audit['models_sha256'][f'{mode}.spice']
        audits[case] = audit
    assert audits['r1c1']['negative_capacitors'] == 1
    assert audits['r2c2']['negative_capacitors'] == 0
    # The unchanged 2x2 raw extraction is the boundary control.
    conditions = [('r1c1', ['rc-port', 'rc-gate']), ('r2c2', ['rc'])]
    results = {}
    for temperature in [27, 125]:
        for step in [200, 100]:
            for case, modes in conditions:
                name = f'{case}-{temperature}-{step}'
                command = [ROOT/'scripts/simulate-array-strips.py', '--source', models,
                           '--output', out/name, '--cases', case, '--modes', *modes,
                           '--fixture', 'imaging', '--temperature', temperature,
                           '--step-ns', step, '--timeout', 120, '--dc-timeout', 120]
                run(command, out/f'{name}.log')
                for mode in modes:
                    path = out/name/f'{case}-{mode}'/'result.json'
                    result = json.loads(path.read_text())
                    assert result['completed'] and result['tracking_screen_pass'], path
                    assert result['model_sha256'] == sha(models/case/f'{mode}.spice')
                    results[case, temperature, step, mode] = result
                print(f'Completed {name}: {", ".join(modes)}', flush=True)
                if step == 100:
                    # Identical transient replay, independent five-times-longer DC solve.
                    extended = command.copy()
                    extended[extended.index('--output')+1] = out/f'{name}-ref1000'
                    extended += ['--reuse-transients', out/name, '--dc-op-us', 1000]
                    run(extended, out/f'{name}-ref1000.log')
                    for mode in modes:
                        path = out/f'{name}-ref1000'/f'{case}-{mode}'/'result.json'
                        result = json.loads(path.read_text())
                        assert result['completed'] and result['tracking_screen_pass'], path
                        results[case, temperature, 'ref1000', mode] = result

    def difference(a, b, field):
        assert len(a['samples']) == len(b['samples']) == a['rows']*a['columns']
        values = []
        for x, y in zip(a['samples'], b['samples']):
            assert (x['row'], x['column'], x['time_s']) == (y['row'], y['column'], y['time_s'])
            values.append(abs(x[field[0]][field[1]]-y[field[0]][field[1]]))
        return max(values)*1e6

    rows = []
    for case, modes in conditions:
        for temperature in [27, 125]:
            for mode in modes:
                coarse, fine, extended = [results[case, temperature, step, mode]
                                          for step in [200, 100, 'ref1000']]
                refinement = difference(coarse, fine, ('capture', 'HOLD'))
                reference = difference(fine, extended, ('dc', 'v(hold)'))
                assert difference(fine, extended, ('capture', 'HOLD')) == 0
                assert refinement < 10 and reference < 10
                rows.append(dict(case=case, temperature_C=temperature, mode=mode,
                                 max_tracking_error_uV=max(r['max_tracking_error_V'] for r in
                                                           [coarse, fine, extended])*1e6,
                                 timestep_difference_uV=refinement,
                                 reference_extension_difference_uV=reference))
    placements = []
    for temperature in [27, 125]:
        for step in [200, 100]:
            a, b = [results['r1c1', temperature, step, mode] for mode in ['rc-port', 'rc-gate']]
            delta = difference(a, b, ('capture', 'HOLD'))
            assert delta < 10
            placements.append(dict(temperature_C=temperature, step_ns=step, difference_uV=delta))
    report = dict(scope=__doc__, source=str(source), audits=audits, electrical=rows,
                  placement_sensitivity=placements, unique_transients=12,
                  extended_reference_runs=6, passed=True,
                  limits=['Raw isolated extraction retains its negative shunt.',
                          'Conserved shunt total approximates physical capacitance distribution.',
                          'Schematic periphery and imposed controls; no compact capture bank, physical join or startup qualification.'])
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    manifest = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
