"""Compare the extracted distributed-ground return with the 8 µm-bus control."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--revised', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    assert not args.out.exists()
    spec = importlib.util.spec_from_file_location('network', ROOT / 'scripts/diagnose-bank-ground-network.py')
    network = importlib.util.module_from_spec(spec); spec.loader.exec_module(network)
    cases = [network.measure(directory) for directory in [args.original, args.revised]]
    for case in cases:
        assert case['columns'] == 64 and case['ground_width_um'] == 8
    assert not json.loads((args.original / 'verification.json').read_text()).get('ground_return_grid')
    assert json.loads((args.revised / 'verification.json').read_text())['ground_return_grid']
    change = np.array(cases[0]['transfer_resistance_ohm']) - np.array(cases[1]['transfer_resistance_ohm'])
    eigenvalue = float(np.min(np.linalg.eigvalsh((change + change.T) / 2)))
    report = dict(scope=__doc__, cases=cases,
                  original_far_self_ohm=cases[0]['per_column_self_resistance_ohm'][-1],
                  revised_far_self_ohm=cases[1]['per_column_self_resistance_ohm'][-1],
                  original_max_uniform_uV=max(cases[0]['uniform_1uA_per_column_ground_uV']),
                  revised_max_uniform_uV=max(cases[1]['uniform_1uA_per_column_ground_uV']),
                  minimum_eigenvalue_old_minus_new_ohm=eigenvalue,
                  all_test_current_patterns_nonincreasing_resistive_energy=eigenvalue >= -1e-8,
                  limits='Artificial unit-current resistor-network diagnosis, not the operating device currents or a transient accuracy result.',
                  evidence_hashes={str(f.resolve().relative_to(ROOT)): network.sha(f) for f in [Path(__file__), ROOT / 'scripts/diagnose-bank-ground-network.py']})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['cases', 'evidence_hashes']}, indent=2))


if __name__ == '__main__':
    main()
