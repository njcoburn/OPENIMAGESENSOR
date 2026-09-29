"""Audit bounded compact-bank scaling and resistor-reduction experiments.

This records initialization/readout completion, not electrical accuracy or
startup qualification. Generated evidence remains local in build/.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'scaling', ROOT / 'scripts/report-compact-bank-scaling.py')
scaling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaling)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout', type=Path, action='append', required=True)
    p.add_argument('--run', type=Path, action='append', required=True)
    p.add_argument('--control', type=Path, required=True)
    p.add_argument('--reduced-control', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    evidence = set()

    def relative(path):
        return str(path.resolve().relative_to(ROOT))

    def read(path):
        evidence.add(path)
        return json.loads(path.read_text())

    layouts = {}
    for directory in a.layout:
        meta = read(directory / 'verification.json')
        assert meta['gds_sha256'] == scaling.sha(directory / 'bank.gds')
        assert meta['magic_drc_errors'] == meta['klayout_main_drc_errors'] == 0
        assert len(ET.parse(directory / 'main-drc.lyrdb').getroot().find('items')) == 0
        assert meta['direct_and_resistor_collapsed_lvs']
        for name in ['direct', 'collapsed']:
            assert 'Circuits match uniquely' in (directory / f'{name}-lvs.log').read_text()
        for name, digest in meta['hashes'].items():
            assert scaling.sha(directory / name) == digest
        layouts[meta['gds_sha256']] = dict(directory=relative(directory),
            columns=meta['columns'], bbox_um=meta['bbox_um'],
            main_drc_and_both_lvs_pass=True,
            devices={n: meta[n] for n in ['mos', 'mim', 'diodes', 'resistors', 'capacitors']})
        evidence.update(f for f in directory.iterdir() if f.is_file())

    attempts = []
    for directory in a.run:
        result = read(directory / 'result.json')
        assert result['layout_gds_sha256'] in layouts
        assert result['columns'] == layouts[result['layout_gds_sha256']]['columns']
        assert result['model_sha256'] == scaling.sha(directory / 'tile.spice')
        assert result['transient']['deck_sha256'] == scaling.sha(directory / 'transient/test.spice')
        assert not result['references_requested']
        last = scaling.last_trace_time(directory / 'transient/stream.raw', result['transient']['points'])
        if result['transient']['completed']:
            assert abs(last - result['stop_s']) < 1e-12
            assert len(result['samples']) == 2 * result['columns']
        attempts.append(dict(directory=relative(directory),
            **{n: result[n] for n in ['columns', 'model', 'temperature_C', 'lights_pA',
                                      'step_ns', 'stop_s', 'transient']},
            last_complete_trace_time_s=last,
            equivalent_model_audit=result.get('equivalent_model_audit'),
            electrical_accuracy_qualified=False))
        evidence.update(f for f in directory.rglob('*') if f.is_file())

    original = read(a.control / 'result.json')
    reduced = read(a.reduced_control / 'result.json')
    assert original['completed'] and reduced['completed']
    for key in ['columns', 'temperature_C', 'lights_pA', 'step_ns', 'layout_gds_sha256', 'model']:
        assert original[key] == reduced[key]
    assert reduced['equivalent_model_audit']['source_sha256'] == original['model_sha256']
    assert len(original['samples']) == len(reduced['samples']) == 2 * original['columns']
    differences = {}
    for old, new in zip(original['samples'], reduced['samples']):
        for key in ['slot', 'column', 'time_s']:
            assert old[key] == new[key]
        assert old['values'].keys() == new['values'].keys()
        for node in old['values']:
            differences[node] = max(differences.get(node, 0), abs(old['values'][node] - new['values'][node]))
    assert max(differences.values()) < 10e-6
    report = dict(scope=__doc__, layouts=list(layouts.values()), attempts=attempts,
        two_column_reduction_control=dict(original=relative(a.control),
            reduced=relative(a.reduced_control), max_sample_difference_V=max(differences.values()),
            sample_differences_by_node_V=differences, sample_comparison_pass=True,
            scope='One hot alternating-pattern transient; sampled terminal comparison only.'),
        full_bank_electrical_accuracy_qualified=False,
        evidence_storage='Local build files; recorded hashes are not an external backup.',
        evidence_hashes={relative(f): scaling.sha(f) for f in sorted(evidence)})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(attempts=len(attempts),
        control_max_difference_V=max(differences.values())), indent=2))


if __name__ == '__main__':
    main()
