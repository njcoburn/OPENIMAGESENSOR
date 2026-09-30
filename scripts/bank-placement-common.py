"""Independent exact-netlist and sample comparisons for conserved shunt placement."""
import hashlib


def check_variant(layout, meta):
    original = (layout / 'rc-port.spice').read_text().splitlines()
    expected = original.copy()
    shunts = meta['shunt_approximations']
    assert len(shunts) == meta['columns'] + 3
    for index, shunt in enumerate(shunts):
        assert shunt['total_F'] > 0 and shunt['far_node'] != shunt['net']
        before = f'CFIX{index} {shunt["net"]} GND {shunt["total_F"]:.17g}'
        after = f'CFIX{index} {shunt["far_node"]} GND {shunt["total_F"]:.17g}'
        assert expected.count(before) == 1
        expected[expected.index(before)] = after
    for model in ('rc-port', 'rc-far'):
        assert hashlib.sha256((layout / (model + '.spice')).read_bytes()).hexdigest() == meta['hashes'][model + '.spice']
    assert expected == (layout / 'rc-far.spice').read_text().splitlines(), 'Unintended device, RC value or connection change'
    return [shunt['net'] for shunt in shunts]


def sample_delta(base, placed):
    for key in ('columns', 'lights_pA', 'temperature_C', 'step_ns', 'acquisition_us', 'sample_offset_s', 'layout_gds_sha256'):
        assert base[key] == placed[key], key
    count = base['columns']
    assert len(base['samples']) == len(placed['samples']) == 2 * count
    differences = []
    for a, b in zip(base['samples'], placed['samples']):
        assert (a['slot'], a['column'], a['time_s']) == (b['slot'], b['column'], b['time_s'])
        for name in ['HOLD'] + [f'STORE{c}' for c in range(count)]:
            differences.append(dict(node=name, scan=a['slot'], column=a['column'],
                                    difference_uV=abs(a['values'][name] - b['values'][name]) * 1e6))
    worst = lambda rows: max(rows, key=lambda x: x['difference_uV'])
    hold = worst([d for d in differences if d['node'] == 'HOLD'])
    store = worst([d for d in differences if d['node'] != 'HOLD'])
    return dict(hold_max_uV=hold['difference_uV'], store_max_uV=store['difference_uV'],
                hold_worst=hold, store_worst=store, limit_uV=10)
