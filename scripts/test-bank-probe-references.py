"""Regenerate archived qualified reference decks and require exact equality."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layout', type=Path, required=True)
    parser.add_argument('--run', type=Path, action='append', required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('probe', ROOT / 'scripts/probe-bank-readout.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    reader = probe.module('reader', 'diagnose-capture-transient.py')
    bank = probe.module('bank', 'simulate-compact-bank.py')
    meta = json.loads((args.layout / 'verification.json').read_text())
    count = 0
    for directory in args.run:
        result = json.loads((directory / 'result.json').read_text())
        assert result['completed'] and result['references_requested'] and result['columns'] == meta['columns']
        ix, data = reader.trace(directory / 'transient/stream.raw')
        at = bank.trace_sampler(ix, data)
        source = (directory / 'transient/test.spice').read_text()
        cases = [(f'capture{c}-reference', .0014 - 1e-9, c, False) for c in range(meta['columns'])]
        cases += [(f'{s["slot"]}{s["column"]}-output-reference', s['time_s'], s['column'], True) for s in result['samples']]
        for name, t, column, stores in cases:
            generated = probe.reference_deck(source, meta, at, t, column, stores)
            assert generated == (directory / name / 'test.spice').read_text(), str(directory / name)
            count += 1
    print(f'All {count} regenerated references match archived decks byte-for-byte.')


if __name__ == '__main__':
    main()
