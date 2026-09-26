"""Read saved bank DC evidence and prepare selective wire-resistance controls.

Uses only Python's standard library. Preparation does not run a simulator.
Collapsed-net models are diagnostic counterfactuals, never qualified layouts.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import os
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_op(path):
    """Read exactly one real-valued native-endian ngspice binary OP record."""
    header, data = path.read_bytes().split(b'Binary:\n', 1)
    text = header.decode()
    assert re.search(r'(?m)^Flags:\s+real\s*$', text)
    assert int(re.search(r'No. Points:\s*(\d+)', text)[1]) == 1
    count = int(re.search(r'No. Variables:\s*(\d+)', text)[1])
    names = [line.split()[1].lower() for line in text.split('Variables:\n')[1].splitlines() if line.strip()]
    assert len(names) == count == len(set(names)) and len(data) == count * 8
    values = struct.unpack('=' + 'd' * count, data)
    assert all(math.isfinite(v) for v in values)
    return dict(zip(names, values))


def collapse(source, selected):
    """Contract only the selected complete resistor components, preserving devices."""
    lines = source.splitlines()
    ports = next(l.split()[2:] for l in lines if l.startswith('.subckt'))
    parent = {}

    def find(n):
        parent.setdefault(n, n)
        if parent[n] != n:
            parent[n] = find(parent[n])
        return parent[n]

    resistors = [l.split() for l in lines if l.startswith('R')]
    for r in resistors:
        assert float(r[3]) > 0
        parent[find(r[1])] = find(r[2])
    canonical = {find(p): p for p in ports}
    assert len(canonical) == len(ports)
    assert set(selected) <= set(ports)
    mapping = {n: canonical[find(n)] for n in list(parent) if canonical[find(n)] in selected}
    output, removed, discarded_caps = [], [], []
    for line in lines:
        f = line.split()
        if not f or f[0][0] not in 'XRC':
            output.append(line)
            continue
        kind = f[0][0]
        if kind == 'R' and f[1] in mapping:
            assert f[2] in mapping and mapping[f[1]] == mapping[f[2]]
            removed.append(line)
            continue
        count = (2 if f[3].startswith('cap_mim_') else 4) if kind == 'X' else 2
        f[1:count+1] = [mapping.get(n, n) for n in f[1:count+1]]
        if kind == 'C' and f[1] == f[2]:
            discarded_caps.append(line)
            continue
        output.append(' '.join(f))
    result = '\n'.join(output) + '\n'
    # Preserve all device names/models/parameters and every unselected resistor.
    before = [l.split() for l in lines if l.startswith('X')]
    after = [l.split() for l in output if l.startswith('X')]
    assert len(before) == len(after) == 962
    for old, new in zip(before, after):
        count = 2 if old[3].startswith('cap_mim_') else 4
        assert old[0] == new[0] and old[count+1:] == new[count+1:]
        assert new[1:count+1] == [mapping.get(n, n) for n in old[1:count+1]]
    assert [l for l in output if l.startswith('R')] == [l for l in lines if l.startswith('R') and l not in set(removed)]
    return result, mapping, dict(selected_nets=selected, removed_resistors=len(removed),
                                retained_resistors=len(resistors)-len(removed),
                                discarded_zero_voltage_capacitors=len(discarded_caps),
                                device_count=len(after), device_parameters_preserved=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank', type=Path, required=True)
    p.add_argument('--dc', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--run', action='store_true', help='Run prepared 27 C / 1.2 V DC controls inside the EDA container.')
    p.add_argument('--timeout', type=float, default=60)
    p.add_argument('--local-controls', action='store_true',
                   help='Also isolate remaining local COL/STORE/CBUF/BUF resistance contributions.')
    a = p.parse_args()
    assert a.timeout > 0
    bank, dc, out = a.bank.resolve(), a.dc.resolve(), a.out.resolve()
    meta = json.loads((bank/'verification.json').read_text())
    screen = json.loads((dc/'report.json').read_text())
    assert meta['columns'] == 64 and screen['all_completed']
    for name, digest in meta['hashes'].items():
        assert sha(bank/name) == digest, name
    for name, digest in screen['model_sha256'].items():
        assert sha(dc/(name+'.spice')) == digest
    assert sha(dc/'rc-port.spice') == meta['hashes']['rc-port.spice']
    source = (dc/'rc-port.spice').read_text()
    ports = next(l.split()[2:] for l in source.splitlines() if l.startswith('.subckt'))
    records, evidence, lookup = [], {}, {}
    for r in screen['results']:
        d = dc/f"{r['model']}-{r['temperature_C']}-{r['input_V']:g}"
        assert r['completed'] and not r['timed_out'] and r['returncode'] == 0 and not r['errors']
        assert sha(d/'test.spice') == r['deck_sha256']
        values = read_op(d/'op.raw')
        assert values == r['values']
        assert 'Transient op started' not in (d/'ngspice.log').read_text()
        for name in ['op.raw', 'result.json', 'test.spice', 'ngspice.log']:
            evidence[str(d/name)] = sha(d/name)
        lookup[r['model'], r['temperature_C'], r['input_V']] = values
    assert len(lookup) == 16
    for (model, temp, level), values in lookup.items():
        if model != 'rc-port':
            continue
        ideal = lookup['reference', temp, level]

        def voltage(n):
            return 0.0 if n == 'GND' else values['v(' + (n if n in ports else 'xbank.'+n).lower() + ')']

        columns = []
        for c in range(64):
            roles = meta['roles'][str(c)]
            columns.append(dict(column=c,
                buffer_shift_V=values[f'v(cbuf{c})']-ideal[f'v(cbuf{c})'],
                follower_vdd_drop_V=values['v(vdd)']-voltage(roles['follower']['body']),
                follower_ground_rise_V=voltage(roles['follower']['drain']),
                bias_source_ground_rise_V=voltage(roles['bias']['source']),
                bias_gate_minus_source_V=voltage(roles['bias']['gate'])-voltage(roles['bias']['source']),
                bias_gate_drop_V=values['v(bias)']-voltage(roles['bias']['gate']),
                storage_input_error_V=values[f'v(store{c})']-level))
        metrics = {}
        for name in columns[0]:
            if name == 'column':
                continue
            lo, hi = min(columns, key=lambda v:v[name]), max(columns, key=lambda v:v[name])
            metrics[name] = dict(min=lo[name], max=hi[name], span=hi[name]-lo[name],
                                 min_column=lo['column'], max_column=hi['column'])
        records.append(dict(temperature_C=temp, input_V=level, metrics=metrics, columns=columns))
    out.mkdir(parents=True, exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    (out/'original-model.spice').write_text(source)
    original = (dc/'rc-port-27-1.2/test.spice').read_text()
    (out/'original-deck.spice').write_text(original)
    variants = {'full': [], 'vdd': ['VDD'], 'ground': ['GND'],
                'supplies': ['VDD','GND'], 'bias': ['BIAS'], 'pref': ['PREF'],
                'references': ['BIAS','PREF'], 'supplies-references': ['VDD','GND','BIAS','PREF']}
    if a.local_controls:
        base=['VDD','GND','BIAS','PREF']
        for prefix in ['COL','STORE','CBUF','BUF']:
            variants['supplies-references-'+prefix.lower()]=base+[
                n for n in ports if re.fullmatch(prefix+r'\d*',n)]
        variants['all-wire-nets']=ports
    prepared = []
    for name, nets in variants.items():
        d = out/name
        d.mkdir()
        model, mapping, audit = collapse(source, nets)
        (d/'model.spice').write_text(model)
        node_map = {('xbank.'+n).lower(): ('0' if dest == 'GND' else dest) for n,dest in mapping.items() if n not in ports}
        lines = []
        for line in original.splitlines():
            if line.startswith('.include ') and line.endswith('/rc-port.spice'):
                line = '.include model.spice'
            elif line.startswith('.save '):
                line = re.sub(r'v\(([^)]+)\)', lambda m:'v('+node_map.get(m[1].lower(),m[1])+')', line, flags=re.I)
                line = '.save '+' '.join(dict.fromkeys(v for v in line.split()[1:] if v != 'v(0)'))
            lines.append(line)
        deck = '\n'.join(lines)+'\n'
        assert sum(l == '.include model.spice' for l in lines) == 1
        assert [l for l in original.splitlines() if not l.startswith(('.include ','.save '))] == [l for l in lines if not l.startswith(('.include ','.save '))]
        (d/'test.spice').write_text(deck)
        r = dict(name=name, **audit, model_sha256=sha(d/'model.spice'), deck_sha256=sha(d/'test.spice'),
                 status='prepared-not-run', completed=False)
        if a.run:
            start = time.monotonic()
            with (d/'ngspice.log').open('w') as log:
                try:
                    proc = subprocess.run(['ngspice','-b','test.spice'], cwd=d, stdout=log, stderr=subprocess.STDOUT,
                        env={**os.environ, 'SPICE_USERINIT_DIR':str(out), 'OMP_NUM_THREADS':'1'}, timeout=a.timeout)
                    r.update(returncode=proc.returncode, timed_out=False)
                except subprocess.TimeoutExpired:
                    r.update(returncode=None, timed_out=True)
            log = (d/'ngspice.log').read_text()
            r.update(seconds=time.monotonic()-start, errors=re.findall(r'(?im)^.*(?:aborted|error|timestep too small).*$',log),
                     transient_assisted_initialization='Transient op started' in log)
            if not r['timed_out'] and r['returncode'] == 0 and not r['errors'] and (d/'op.raw').exists():
                r['values'] = read_op(d/'op.raw')
                shifts = [r['values'][f'v(cbuf{c})']-lookup['reference',27,1.2][f'v(cbuf{c})'] for c in range(64)]
                r.update(completed=True, buffer_shifts_V=shifts, max_abs_buffer_shift_V=max(map(abs,shifts)), buffer_shift_span_V=max(shifts)-min(shifts))
            r['status'] = 'completed' if r['completed'] else 'incomplete'
        (d/'result.json').write_text(json.dumps(r,indent=2)+'\n')
        prepared.append(r)
    report = dict(scope=__doc__, source_bank=str(bank), source_dc=str(dc),
                  raw_op_readback_verified=True, direct_dc_without_transient_fallback=True,
                  source_hashes={str(bank/'verification.json'):sha(bank/'verification.json'),
                                 str(dc/'report.json'):sha(dc/'report.json'),
                                 str(dc/'rc-port.spice'):sha(dc/'rc-port.spice'), **evidence},
                  measurements=records, controls=prepared, full_readout_accuracy_qualified=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(saved_dc_records_verified=len(lookup), controls=len(prepared),
                          completed_controls=sum(r['completed'] for r in prepared), report=str(out/'report.json'))))


if __name__ == '__main__':
    main()
