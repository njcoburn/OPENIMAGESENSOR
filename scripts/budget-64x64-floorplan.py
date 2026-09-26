"""Check slot-fit arithmetic and draw the proposed block budgets; no GDS signoff."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def fits(size, boundary):
    w, h = size
    a, b = boundary
    return (w <= a and h <= b) or (h <= a and w <= b)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, default=ROOT/'layout/64x64-floorplan-budget.json')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    cfg = json.loads(a.config.read_text())
    bankfile = ROOT/cfg['existing_bank_verification']
    bank = json.loads(bankfile.read_text())
    x0, y0, x1, y1 = map(float, re.findall(r'-?\d+(?:\.\d+)?', bank['bbox_um']))
    bank_size = [x1-x0, y1-y0]
    array = [cfg['columns']*cfg['existing_pitch_um'][0], cfg['rows']*cfg['existing_pitch_um'][1]]
    blocks = cfg['candidate_blocks_um']
    assert blocks['pixel_array'][2:] == [cfg['columns']*cfg['candidate_pitch_um'][0], cfg['rows']*cfg['candidate_pitch_um'][1]]
    cw, ch = cfg['default_core_um']
    for name, (x, y, w, h) in blocks.items():
        assert min(x, y) >= 0 and min(w, h) > 0
        assert x+w <= cw and y+h <= ch, name
    pairs = list(blocks.items())
    for i, (name, (x, y, w, h)) in enumerate(pairs):
        for other, (xx, yy, ww, hh) in pairs[i+1:]:
            assert x+w <= xx or xx+ww <= x or y+h <= yy or yy+hh <= y, (name, other)
    result = dict(config=cfg, config_sha256=hashlib.sha256(a.config.read_bytes()).hexdigest(),
                  bank_verification_sha256=hashlib.sha256(bankfile.read_bytes()).hexdigest(),
                  existing_array_um=array, existing_bank_um=bank_size,
                  existing_array_fits_inside_seal=fits(array, cfg['inside_seal_um']),
                  existing_bank_fits_inside_seal=fits(bank_size, cfg['inside_seal_um']),
                  existing_array_fits_default_core=fits(array, cfg['default_core_um']),
                  existing_array_plus_bank_area_mm2=(array[0]*array[1]+bank_size[0]*bank_size[1])/1e6,
                  default_core_area_mm2=cw*ch/1e6,
                  candidate_block_area_mm2=sum(w*h for _, _, w, h in blocks.values())/1e6,
                  remaining_core_budget_mm2=(cw*ch-sum(w*h for _, _, w, h in blocks.values()))/1e6,
                  candidate_rectangles_fit=True, physical_layout_qualified=False)
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out/'budget.json').write_text(json.dumps(result, indent=2)+'\n')
    # Same scale for the existing footprint and proposed core budget.
    scale = .11
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="690" viewBox="0 0 1120 690">',
           '<rect width="1120" height="690" fill="#f8fafc"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#172033} .small{font-size:13px}</style>',
           '<text x="30" y="32" font-size="23">64 × 64: slot-fit study</text>',
           '<text x="30" y="57" class="small">Planning rectangles only • candidate needs a new pixel and bank layout</text>']
    for ox, title in [(35, 'Existing array: does not fit'), (690, 'Compact candidate budget')]:
        svg.append(f'<text x="{ox}" y="91" font-size="17">{title}</text>')
        svg.append(f'<rect x="{ox}" y="110" width="{cw*scale}" height="{ch*scale}" fill="#e2e8f0" stroke="#334155" stroke-width="2"/>')
    svg += [f'<rect x="35" y="110" width="{array[0]*scale}" height="{array[1]*scale}" fill="#ef4444" fill-opacity=".2" stroke="#dc2626" stroke-width="2"/>',
            '<text x="50" y="145" font-size="16">5.120 × 3.200 mm pixel array</text>',
            '<text x="50" y="168" class="small">Bank, controls and joins still excluded</text>']
    for (name, (x,y,w,h)), color in zip(blocks.items(), ['#bfdbfe','#a7f3d0','#fcd34d']):
        svg.append(f'<rect x="{690+x*scale}" y="{110+y*scale}" width="{w*scale}" height="{h*scale}" fill="{color}" stroke="#334155"/>')
    svg += ['<text x="750" y="255" font-size="16">64 × 64 at 40 µm pitch</text>',
            '<text x="750" y="278" class="small">2.560 × 2.560 mm</text>',
            '<text x="727" y="458" font-size="15">Capture bank: 2.700 × 1.100 mm</text>',
            '<text x="727" y="480" class="small">Repacked circuit; not existing GDS</text>',
            '<text x="35" y="605" font-size="15">Gray outline: 3.048 × 4.238 mm default full-slot core (both panels use the same scale)</text>',
            '<text x="35" y="631" class="small">Yellow: row-driver budget. Remaining space: routing, references, output/control circuits and margins.</text>',
            '<text x="35" y="657" class="small">Source: wafer.space linked slot JSON, generated 2026-06-04; checked 2026-09-25. No purchased slot assumed.</text>', '</svg>']
    (a.out/'floorplan.svg').write_text('\n'.join(svg)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='config'}, indent=2))


if __name__ == '__main__':
    main()
