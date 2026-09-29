"""Compare extracted ground transfer resistance at physical MIM terminals.

Unit test currents diagnose only the extracted resistor network. They are not
the bank's operating currents, a transient replacement, or an accuracy pass.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import splu

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def measure(directory):
    meta = json.loads((directory / 'verification.json').read_text())
    model = directory / 'rc-port.spice'
    assert sha(model) == meta['hashes'][model.name]
    lines = [line.split() for line in model.read_text().splitlines() if line and not line.startswith(('*', '.'))]
    resistors = [r for r in lines if r[0].startswith('R')]
    graph = defaultdict(list)
    for _, a, b, resistance in resistors:
        assert float(resistance) > 0
        graph[a].append(b)
        graph[b].append(a)
    seen, pending = {'GND'}, ['GND']
    while pending:
        node = pending.pop()
        for other in graph[node]:
            if other not in seen:
                seen.add(other)
                pending.append(other)
    nodes = sorted(seen - {'GND'})
    index = {node: i for i, node in enumerate(nodes)}
    rows, cols, values = [], [], []
    count = 0
    for _, a, b, resistance in resistors:
        if a not in seen:
            continue
        assert b in seen
        count += 1
        g = 1 / float(resistance)
        for source, target in [(a, b), (b, a)]:
            if source == 'GND':
                continue
            rows.append(index[source]); cols.append(index[source]); values.append(g)
            if target != 'GND':
                rows.append(index[source]); cols.append(index[target]); values.append(-g)
    laplacian = csc_matrix((values, (rows, cols)), shape=(len(nodes), len(nodes)))
    injection = np.zeros((len(nodes), meta['columns']))
    plate_nodes = []
    for c in range(meta['columns']):
        plates = [r for r in lines if r[0].startswith('X') and r[3].startswith('cap_mim_') and re.fullmatch(f'STORE{c}(?:[.].*)?', r[1])]
        assert len(plates) == 8 and all(r[2] in seen for r in plates)
        plate_nodes.append([r[2] for r in plates])
        for plate in plates:
            assert plate[2] != 'GND'
            injection[index[plate[2]], c] += 1 / 8
    voltages = splu(laplacian).solve(injection)
    residual = float(np.max(np.abs(laplacian @ voltages - injection)))
    assert residual < 1e-8
    transfer = injection.T @ voltages
    assert np.allclose(transfer, transfer.T, rtol=1e-9, atol=1e-9)
    assert float(np.min(transfer)) >= -1e-9 and float(np.min(np.linalg.eigvalsh(transfer))) > 0
    return dict(layout=str(directory), columns=meta['columns'], ground_width_um=meta.get('ground_bus_width_um', 2),
                ground_nodes=len(nodes) + 1, ground_resistors=count, kcl_residual_A_for_1A_tests=residual,
                terminal_nodes=plate_nodes, transfer_resistance_ohm=transfer.tolist(),
                per_column_self_resistance_ohm=np.diag(transfer).tolist(),
                uniform_1uA_per_column_ground_uV=transfer.sum(axis=1).tolist(),
                evidence_hashes={str(f.resolve().relative_to(ROOT)): sha(f) for f in [model, directory / 'verification.json']})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout', type=Path, action='append', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    results = [measure(directory) for directory in a.layout]
    comparisons = []
    for columns in sorted({r['columns'] for r in results}):
        old, = [r for r in results if r['columns'] == columns and r['ground_width_um'] == 2]
        new, = [r for r in results if r['columns'] == columns and r['ground_width_um'] == 8]
        change = np.array(old['transfer_resistance_ohm']) - np.array(new['transfer_resistance_ohm'])
        eigenvalues = np.linalg.eigvalsh((change + change.T) / 2)
        comparisons.append(dict(columns=columns,
            original_far_self_ohm=old['per_column_self_resistance_ohm'][-1], revised_far_self_ohm=new['per_column_self_resistance_ohm'][-1],
            original_max_uniform_uV=max(old['uniform_1uA_per_column_ground_uV']), revised_max_uniform_uV=max(new['uniform_1uA_per_column_ground_uV']),
            minimum_eigenvalue_old_minus_new_ohm=float(min(eigenvalues)),
            all_test_current_patterns_nonincreasing_resistive_energy=bool(min(eigenvalues) >= -1e-8)))
    report = dict(scope=__doc__, cases=results, comparisons=comparisons,
                  interpretation='1 A is distributed equally among each column\'s eight MIM grounds to compute transfer resistance. The plotted uniform profile scales this to 1 µA per column. Actual device return currents differ.',
                  electrical_accuracy_qualified=False,
                  evidence_hashes={str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__))})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    assert not a.out.exists(), 'Preserve previous diagnostics'
    a.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(comparisons, indent=2))


if __name__ == '__main__':
    main()
