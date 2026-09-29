"""Check that the distributed-return candidate adds only its recorded metal/vias."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import klayout.db as k

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--revised', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'runner.py').write_bytes(Path(__file__).read_bytes())
    layouts, metadata = [], []
    for directory in [args.original, args.revised]:
        layout = k.Layout(); layout.read(str(directory / 'bank.gds')); layouts.append(layout)
        meta = json.loads((directory / 'verification.json').read_text()); metadata.append(meta)
        assert meta['columns'] == 64 and meta['ground_bus_width_um'] == 8
        assert meta['magic_drc_errors'] == meta['klayout_main_drc_errors'] == 0
        assert meta['direct_and_resistor_collapsed_lvs'] and sha(directory / 'bank.gds') == meta['gds_sha256']
        assert (meta['mos'], meta['mim'], meta['diodes']) == (642, 512, 64)
    assert not metadata[0].get('ground_return_grid') and metadata[1]['ground_return_grid']
    assert layouts[0].dbu == layouts[1].dbu
    assert (args.original / 'reference.spice').read_bytes() == (args.revised / 'reference.spice').read_bytes()
    assert set(map(str, layouts[0].layer_infos())) == set(map(str, layouts[1].layer_infos()))
    additions = {}
    records = metadata[1]['ground_grid_added_rectangles_um']
    assert len(records) == 647 and {r[0] for r in records} == {41, 46, 81}
    assert sum(r[0] == 41 for r in records) == 192
    for layer, *box in records:
        additions.setdefault(layer, k.Region()).insert(k.Box(*[round(v / layouts[0].dbu) for v in box]))
    changed = []
    for info in layouts[0].layer_infos():
        regions, labels = [], []
        for layout in layouts:
            cell = layout.top_cell(); layer = layout.layer(info)
            regions.append(k.Region(cell.begin_shapes_rec(layer)))
            labels.append(sorted(str(shape.text) for shape in cell.shapes(layer).each() if shape.is_text()))
        assert labels[0] == labels[1], str(info)
        expected = regions[0] | (additions.get(info.layer, k.Region()) if info.datatype == 0 else k.Region())
        assert (expected ^ regions[1]).is_empty(), str(info)
        if not (regions[0] ^ regions[1]).is_empty():
            changed.append(str(info))
    assert set(changed) == {'41/0', '46/0', '81/0'}
    x0, y0, x1, y1 = map(float, re.findall(r'-?\d+(?:\.\d+)?', metadata[1]['bbox_um']))
    size = [x1 - x0, y1 - y0]
    assert size[0] < 2700 and size[1] < 1100
    files = [directory / name for directory in [args.original, args.revised]
             for name in ['bank.gds', 'verification.json', 'reference.spice']] + [args.out / 'runner.py']
    report = dict(scope=__doc__, original=str(args.original), revised=str(args.revised),
                  only_recorded_ground_additions=True, labels_identical=True, reference_identical=True,
                  changed_layers=changed, added_rectangles=647, via4_cuts=192,
                  size_um=size, budget_margin_um=[2700 - size[0], 1100 - size[1]],
                  evidence_hashes={str(f.resolve().relative_to(ROOT)): sha(f) for f in files})
    (args.out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
