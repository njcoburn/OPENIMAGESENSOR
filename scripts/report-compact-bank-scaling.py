"""Record a compact 64-column physical check and bounded electrical attempts.

Completion of a transient alone is not an electrical accuracy qualification.
Raw evidence remains in build/; this report records its content hashes.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def last_trace_time(path, expected_points):
    """Read the time of the last complete real-valued ngspice binary record."""
    if not expected_points:
        return None
    with path.open('rb') as handle:
        header = []
        while True:
            line = handle.readline()
            assert line, 'Missing binary trace header'
            if line == b'Binary:\n':
                break
            header.append(line)
        fields = b''.join(header).decode()
        names = [line.split()[1].lower() for line in fields.split('Variables:\n')[1].splitlines() if line.strip()]
        assert names[0] == 'time' and 'Flags: real' in fields
        offset = handle.tell()
        assert (path.stat().st_size - offset) // (8 * len(names)) == expected_points
        handle.seek(offset + (expected_points - 1) * 8 * len(names))
        return struct.unpack('d', handle.read(8))[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layout', type=Path, required=True)
    parser.add_argument('--run', type=Path, action='append', default=[])
    parser.add_argument('--regression', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    layout = args.layout.resolve()
    physical = json.loads((layout / 'verification.json').read_text())
    assert physical['columns'] == 64
    assert physical['gds_sha256'] == sha(layout / 'bank.gds')
    assert physical['magic_drc_errors'] == physical['klayout_main_drc_errors'] == 0
    assert len(ET.parse(layout / 'main-drc.lyrdb').getroot().find('items')) == 0
    assert physical['direct_and_resistor_collapsed_lvs']
    for name in ['direct', 'collapsed']:
        assert 'Circuits match uniquely' in (layout / f'{name}-lvs.log').read_text()
    for name, digest in physical['hashes'].items():
        assert sha(layout / name) == digest

    old_path = ROOT / 'build/compact-bank-c2-matrix-v1-20260926/125-0,240-100-rc-port/result.json'
    new_path = args.regression.resolve() / 'result.json'
    old, new = [json.loads(p.read_text()) for p in [old_path, new_path]]
    assert old['completed'] and new['completed']
    assert [(s['slot'], s['column'], s['time_s']) for s in old['samples']] == [
        (s['slot'], s['column'], s['time_s']) for s in new['samples']]
    change = max(abs(a['values'][node] - b['values'][node])
                 for a, b in zip(old['samples'], new['samples']) for node in a['values'])
    assert change == 0

    attempts = []
    for directory in args.run:
        directory = directory.resolve()
        result = json.loads((directory / 'result.json').read_text())
        assert result['columns'] == 64 and result['layout_gds_sha256'] == physical['gds_sha256']
        assert result['model_sha256'] == sha(directory / 'tile.spice')
        assert result['transient']['deck_sha256'] == sha(directory / 'transient/test.spice')
        assert not result['references_requested'], 'This report only summarizes bounded transient attempts'
        last = last_trace_time(directory / 'transient/stream.raw', result['transient']['points'])
        attempts.append(dict(directory=str(directory.relative_to(ROOT)), result=result,
                             last_complete_trace_time_s=last))

    inputs = [*layout.glob('*'), old_path, new_path]
    inputs += [path for directory in args.run for path in directory.rglob('*')]
    inputs += list(args.regression.rglob('*'))
    report = dict(scope=__doc__, physical=physical, attempts=attempts,
                  physical_screen_pass=True, electrical_accuracy_qualified=False,
                  schedule_regression_max_sample_change_V=change,
                  selected_layout=str(layout.relative_to(ROOT)),
                  evidence_storage='Raw artifacts retained locally; hashes do not imply an external backup.',
                  evidence_hashes={str(path.resolve().relative_to(ROOT)): sha(path)
                                   for path in sorted(set(inputs)) if path.is_file()})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Physical screen passed; recorded {len(attempts)} bounded electrical attempts.')


if __name__ == '__main__':
    main()
