"""Check the current bank bounding box against the retained planning rectangles."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    config_path = ROOT/'layout/64x64-floorplan-budget.json'
    layout = ROOT/'build/compact-bank-c64-ground-grid-20260927'
    cfg = json.loads(config_path.read_text())
    meta = json.loads((layout/'verification.json').read_text())
    assert sha(layout/'bank.gds') == meta['gds_sha256']
    assert meta['columns'] == 64 and meta['ground_return_grid']
    x0, y0, x1, y1 = map(float, re.findall(r'-?\d+(?:\.\d+)?', meta['bbox_um']))
    width, height = x1-x0, y1-y0
    blocks = dict(cfg['candidate_blocks_um'])
    bx, by, bw, bh = blocks.pop('capture_bank_budget')
    assert width <= bw and height <= bh
    blocks['current_joined_bank'] = [bx, by, width, height]
    cw, ch = cfg['default_core_um']
    for name, (x, y, w, h) in blocks.items():
        assert min(x, y) >= 0 and min(w, h) > 0
        assert x+w <= cw and y+h <= ch, name
    rectangles = list(blocks.items())
    for i, (name, (x, y, w, h)) in enumerate(rectangles):
        for other, (xx, yy, ww, hh) in rectangles[i+1:]:
            assert x+w <= xx or xx+ww <= x or y+h <= yy or yy+hh <= y, (name, other)
    area = sum(w*h for _, _, w, h in blocks.values())/1e6
    files = [Path(__file__).resolve(), config_path, layout/'bank.gds', layout/'verification.json']
    report = dict(checked_on='2026-09-27', layout=str(layout.relative_to(ROOT)),
                  bank_size_um=[width, height], bank_area_mm2=width*height/1e6,
                  bank_reservation_margin_um=[bw-width, bh-height],
                  planning_blocks_um=blocks, default_core_um=[cw, ch],
                  reserved_area_mm2=area, unreserved_area_mm2=cw*ch/1e6-area,
                  rectangles_fit=True, complete_chip_fit_verified=False,
                  scope='Bounding-box arithmetic only, without GDS assembly or routing. The full array reserve conservatively duplicates the one row already in the bank; final assembly must add only 63 rows. Unreserved area is fragmented and includes no guarantee that drivers, joins, pads and routes can be placed.',
                  evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in files})
    (ROOT/'simulations/wafer-space-current-bank-fit-20260927.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['bank_size_um','bank_area_mm2','bank_reservation_margin_um','unreserved_area_mm2','complete_chip_fit_verified']}, indent=2))


if __name__ == '__main__':
    main()
