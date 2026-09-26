"""Prepare a schematic contract and conditional MIM banks; no EDA tools required.

Checks every repeated peripheral device against the accepted 64-column deck.
This does not generate physical layout or run DRC, LVS, extraction or simulation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PORTS = 'COL STORE CBUF BUF SC SCB SEL SELB BIAS PREF VDD GND'
DEVICES = ('Xbias', 'Xholdn', 'Xholdp', 'Xstoreload', 'Xstorefollow',
           'Xmuxn', 'Xmuxp')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def column_records(deck):
    records = {}
    for line in deck.split('.control', 1)[0].splitlines()[1:]:
        fields = line.split()
        if fields and not fields[0].startswith(('*', '.')):
            if fields[0] in records:
                raise ValueError(f'Duplicate element: {fields[0]}')
            records[fields[0]] = fields
    template = []
    for index in range(64):
        mapping = {f'{name}{index}': name for name in ('COL', 'STORE', 'CBUF', 'SEL', 'SELB')}
        mapping['0'] = 'GND'
        column = []
        for name in (*DEVICES, 'Cstore'):
            fields = records[f'{name}{index}']
            terminal_count = 4 if name.startswith('X') else 2
            column.append([name] + [mapping.get(n, n) for n in fields[1:1+terminal_count]]
                          + fields[1+terminal_count:])
        if index == 0:
            template = column
        if column != template:
            raise ValueError(f'Column {index} differs from column 0')
    assert template[-1] == ['Cstore', 'STORE', 'GND', '40p']
    assert sum(r[5] == 'nfet_03v3' for r in template[:-1]) == 3
    assert sum(r[5] == 'pfet_03v3' for r in template[:-1]) == 4
    # The two reference transistors are shared, not repeated per column.
    shared = []
    for name in ('Xref', 'Xstorage_ref', 'Rbias', 'Rpref', 'Cbias', 'Cpref'):
        fields = records[name].copy()
        count = 4 if name.startswith('X') else 2
        fields[1:1+count] = ['GND' if n == '0' else n for n in fields[1:1+count]]
        shared.append(' '.join(fields))
    assert records['Rbias'] == ['Rbias', 'VDD', 'BIAS', '500000']
    assert records['Rpref'] == ['Rpref', 'PREF', '0', '12400']
    return template, shared


def coefficients(text, option):
    name = f'cap_mim_{option}_m4m5_noshield'
    block = text.split('.subckt ' + name + ' ', 1)[1].split('.ends', 1)[0]
    def number(parameter):
        return float(re.search(r'(?m)^\.param ' + parameter + r"='?([\deE.+-]+)", block)[1])
    assert '\nc_cap 1 2 ' in block and '\n+ cap=c_c0' in block
    assert '\n+ tc1=c_tc1' in block and '\n+ tc2=c_tc2' in block
    assert not re.search(r'(?m)^c_cap.*v\(', block)
    return name, {key: number(key) for key in ('c_cox', 'c_capsw', 'c_tc1', 'c_tc2', 'c_tnom')}, block


def bank(text, option):
    name, values, block = coefficients(text, option)
    # Eight separately bounded plates; 64 um width reserves pitch for routes.
    count, width, grid = 8, 64.0, .005
    area_coeff = values['c_cox'] * 1e-12
    fringe_coeff = values['c_capsw'] * 1e-6
    length_exact = (40e-12/count - 2*fringe_coeff*width) / (area_coeff*width + 2*fringe_coeff)
    length = round(length_exact/grid)*grid
    plate_area = width*length
    assert 25 <= plate_area <= 10000
    nominal = count*(area_coeff*plate_area + fringe_coeff*2*(width+length))
    assert abs(nominal/40e-12 - 1) < 1e-4
    capacitance = {}
    for temperature in (25, 27, 125):
        delta = temperature-values['c_tnom']
        capacitance[str(temperature)] = nominal*(1+values['c_tc1']*delta+values['c_tc2']*delta**2)*1e12
    leakage = None
    if option == '2f0':
        assert ".param gleak='9.51e-10/5*10000'" in block
        assert "r_leak 1 2 r='1/(gleak*c_area)'" in block
        leakage = 1/((9.51e-10/5*10000)*count*plate_area*1e-12)
    else:
        assert not re.search(r'(?m)^[rRbB]', block)
    lines = [f'* Conditional {option} MIM candidate; manufacturing option unselected.',
             '* Requires the original PDK model and its corner/Monte Carlo parameters.',
             '* Separate bottom-metal islands; join with upper-metal routes.',
             f'.subckt capture_storage_{option} STORE GND']
    lines += [f'Xplate{i} STORE GND {name} c_width={width:g}u c_length={length:.3f}u'
              for i in range(count)]
    lines += [f'.ends capture_storage_{option}', '']
    return '\n'.join(lines), dict(model=name, plates=count, width_um=width,
        length_um=length, plate_area_um2=plate_area,
        total_plate_area_um2=count*plate_area,
        bank_64_plate_area_mm2=64*count*plate_area/1e6,
        nominal_error_ppm=(nominal/40e-12-1)*1e6,
        model_capacitance_pF_by_temperature_C=capacitance,
        model_parallel_leakage_ohm_at_25C=leakage,
        voltage_dependence_active_in_saved_model=False,
        coefficients=values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'build/grid-readout-20260924/27-100/r1c64-rc-port/transient/test.spice')
    parser.add_argument('--model', type=Path, default=ROOT/'build/array-strip-storage-area-20260924/sm141064_mim.ngspice')
    parser.add_argument('--rules', type=Path, default=ROOT/'build/array-strip-storage-area-20260924/mim_b.rb')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    template, shared = column_records(args.source.read_text())
    rules = args.rules.read_text()
    assert 'MIMTM.11' in rules and '10_000' in rules and 'MIMTM.10' in rules
    outputs = {}
    transistors = '\n'.join(' '.join(r) for r in template[:-1])
    outputs['capture-column.spice'] = (
        '* Seven-transistor capture/readout column; storage is a separate two-terminal block.\n'
        '* STORE and CBUF are exposed for extraction and matched-terminal checks.\n'
        f'.subckt capture_column {PORTS}\n{transistors}\n.ends capture_column\n\n'
        '* Ideal storage control used by the accepted full-row simulation.\n'
        '.subckt capture_storage_ideal STORE GND\nCstore STORE GND 40p\n.ends capture_storage_ideal\n\n'
        '* Shared reference devices; instantiate once for the bank.\n'
        '.subckt capture_references BIAS PREF VDD GND\n' + '\n'.join(shared[:2]) + '\n.ends capture_references\n\n'
        '* External bias fixture, not on-chip resistor implementation.\n'
        '.subckt capture_bias_fixture BIAS PREF VDD GND\n' + '\n'.join(shared[2:]) + '\n.ends capture_bias_fixture\n')
    candidates = {}
    for option in ('1f0', '1f5', '2f0'):
        outputs[f'capture-storage-{option}.spice'], candidates[option] = bank(args.model.read_text(), option)
    report = dict(scope='Schematic preparation and model arithmetic only; no physical or transient qualification.',
        source_sha256={key: digest(getattr(args, key)) for key in ('source', 'model', 'rules')},
        matching_columns=64, matched_column_elements=512,
        per_column_transistors=dict(nmos=3, pmos=4),
        shared_reference_transistors=dict(nmos=1, pmos=1),
        conditional_storage_candidates=candidates,
        physical_layout_complete=False, drc_pass=None, lvs_pass=None,
        extracted_transient_pass=None,
        next_checks=['PDK capacitor geometry and terminal mapping',
                     'Magic and KLayout DRC including shared-bottom-plate rule',
                     'Device and resistor-collapsed LVS',
                     'Capacitance extraction versus model without double counting',
                     'Matched-terminal column transients and numerical refinement'])
    args.out.mkdir(parents=True, exist_ok=False)
    for filename, content in outputs.items():
        (args.out/filename).write_text(content)
    for key, filename in (('source', 'source.spice'), ('model', 'model.ngspice'), ('rules', 'rules.rb')):
        (args.out/filename).write_bytes(getattr(args, key).read_bytes())
    report['artifact_sha256'] = {name: digest(args.out/name) for name in outputs}
    (args.out/'preparation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
