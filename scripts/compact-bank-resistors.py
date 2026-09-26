"""Eliminate low-degree resistor-only nodes from a capture-bank model.

No device, capacitor, port, or non-resistive record changes. Star-mesh
equivalence is exact algebraically; the serialized result is checked by
reconstructing eliminated voltages and comparing currents in floating point.
This is model preparation, not transient or physical qualification.
Uses only the Python standard library so preparation also works without Docker.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
import random


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(text):
    lines = text.splitlines()
    keep = set()
    edges = []
    headers = ends = 0
    for line in lines:
        f = line.split()
        if not f or f[0].startswith('*'):
            continue
        kind = f[0][0]
        if f[0] == '.subckt':
            headers += 1
            assert f[1] == 'bank'
            keep.update(f[2:])
        elif f[0] == '.ends':
            ends += 1
            assert f[1:] == ['bank']
        elif kind == 'R':
            assert len(f) == 4
            value = float(f[3])
            assert math.isfinite(value) and value > 0 and f[1] != f[2]
            edges.append((f[1], f[2], 1 / value))
        elif kind == 'C':
            assert len(f) == 4
            keep.update(f[1:3])
        elif kind == 'X':
            if f[3].startswith('cap_mim_'):
                keep.update(f[1:3])
            else:
                assert f[5] in ('nfet_03v3', 'pfet_03v3')
                keep.update(f[1:5])
        else:
            raise ValueError('Unsupported record: ' + line)
    assert headers == ends == 1 and edges
    return lines, keep, edges


def compact(text, max_degree=4):
    lines, keep, edges = parse(text)
    graph = defaultdict(dict)

    def connect(x, y, g):
        graph[x][y] = graph[x].get(y, 0) + g
        graph[y][x] = graph[y].get(x, 0) + g

    for x, y, g in edges:
        connect(x, y, g)
    queue = deque(sorted(n for n in graph if n not in keep and len(graph[n]) <= max_degree))
    removed = []
    while queue:
        n = queue.popleft()
        if n not in graph or n in keep or len(graph[n]) > max_degree:
            continue
        neighbors = sorted(graph[n].items())
        assert neighbors, 'Floating resistor-only component'
        removed.append((n, neighbors))
        total = math.fsum(g for _, g in neighbors)
        for i, (x, gx) in enumerate(neighbors):
            for y, gy in neighbors[i+1:]:
                connect(x, y, gx * (gy / total))
        for x, _ in neighbors:
            del graph[x][n]
            if x not in keep and len(graph[x]) <= max_degree:
                queue.append(x)
        del graph[n]
    output = [l for l in lines if not l.startswith('R') and not l.startswith('.ends')]
    reduced = sorted((x, y, g) for x in graph for y, g in graph[x].items() if x < y)
    output += [f'REQ{i} {x} {y} {1/g:.17g}' for i, (x, y, g) in enumerate(reduced)]
    output += ['.ends bank']
    return '\n'.join(output) + '\n', removed


def audit(source, target, removed, probes=12):
    oldlines, keep, old = parse(source)
    newlines, newkeep, new = parse(target)
    assert [l for l in oldlines if not l.startswith('R')] == [l for l in newlines if not l.startswith('R')]
    assert keep == newkeep
    oldnodes = {n for x, y, _ in old for n in (x, y)}
    newnodes = {n for x, y, _ in new for n in (x, y)}
    assert keep & oldnodes <= newnodes
    assert oldnodes - newnodes == {n for n, _ in removed}
    rng = random.Random(640064)
    boundary_error = internal_error = 0.0
    for _ in range(probes):
        volts = {n: rng.uniform(-1, 1) for n in sorted(newnodes)}
        for n, neighbors in reversed(removed):
            volts[n] = (volts[neighbors[0][0]] if len(neighbors) == 1 else
                        math.fsum(volts[x] * g for x, g in neighbors) / math.fsum(g for _, g in neighbors))

        def currents(edges):
            contributions = defaultdict(list)
            for x, y, g in edges:
                value = (volts[x] - volts[y]) * g
                contributions[x].append(value)
                contributions[y].append(-value)
            return {n: math.fsum(v) for n, v in contributions.items()}, contributions

        before, incident = currents(old)
        after, _ = currents(new)
        scales = defaultdict(list)
        for x, y, g in old:
            scale = g * (abs(volts[x]) + abs(volts[y]))
            scales[x].append(scale)
            scales[y].append(scale)
        for n in newnodes:
            scale = max(math.fsum(abs(v) for v in incident[n]), abs(after[n]), 1e-14)
            boundary_error = max(boundary_error, abs(before[n] - after[n]) / scale)
        for n, _ in removed:
            scale = max(math.fsum(scales[n]), 1e-14)
            internal_error = max(internal_error, abs(before[n]) / scale)
    assert boundary_error < 1e-9, boundary_error
    assert internal_error < 1e-10, internal_error
    return dict(original_resistors=len(old), reduced_resistors=len(new),
                eliminated_resistor_only_nodes=len(removed),
                all_nonresistor_records_identical=True, protected_nodes=len(keep),
                random_voltage_probes=probes, boundary_current_relative_error=boundary_error,
                internal_kcl_scaled_error=internal_error,
                transient_qualified=False,
                scope='Algebraic star-mesh reduction only; existing shunt-placement approximation unchanged.')


def verify_files(source, target, max_degree=4):
    expected, removed = compact(source.read_text(), max_degree)
    assert target.read_text() == expected, 'Equivalent model differs from deterministic reduction'
    return audit(source.read_text(), target.read_text(), removed)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--max-degree', type=int, choices=[2, 3, 4], default=4)
    a = p.parse_args()
    model, removed = compact(a.source.read_text(), a.max_degree)
    # Audit in memory before creating output; read back the written model too.
    audit(a.source.read_text(), model, removed)
    a.out.mkdir(parents=True, exist_ok=False)
    target = a.out / 'bank.spice'
    target.write_text(model)
    report = verify_files(a.source, target, a.max_degree)
    report.update(max_degree=a.max_degree, source=str(a.source), source_sha256=digest(a.source),
                  model_sha256=digest(target), runner_sha256=digest(Path(__file__)))
    (a.out / 'runner.py').write_bytes(Path(__file__).read_bytes())
    (a.out / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
