"""Conditional storage-area budget from installed model area coefficients.

This is not a process-option selection or a placed capacitor design. Fringing,
spacing, shields, routing, switches and buffers are excluded from area estimates.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
out = ROOT/'build/array-strip-storage-area-20260924'
out.mkdir(exist_ok=False)
model = Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064_mim.ngspice')
rules = Path('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/rule_decks/mim_b.rb')
sources = {}
for path in [model, rules]:
    data = path.read_bytes()
    (out/path.name).write_bytes(data)
    sources[str(path)] = hashlib.sha256(data).hexdigest()
text = model.read_text()
items = []
for option in ['1f0', '1f5', '2f0']:
    name = f'cap_mim_{option}_m4m5_noshield'
    block = text.split('.subckt '+name+' ', 1)[1].split('.ends', 1)[0]
    coefficient = float(re.search(r"\.param c_cox='([\deE.+-]+)\*", block)[1])
    area_um2 = 40e-12/coefficient*1e12
    items.append(dict(model=name, nominal_area_coefficient_F_per_m2=coefficient,
                      capacitor_pF=40, capacitor_area_only_um2=area_um2,
                      bank_64_area_only_mm2=64*area_um2/1e6,
                      bank_area_only_depth_at_5p12mm_width_mm=64*area_um2/1e6/5.12))
assert 'Maximum single MIM Cap area' in rules.read_text() and '10_000.um' in rules.read_text()
report = dict(scope=__doc__, source_hashes=sources, conditional_options=items,
              installed_rule_max_single_plate_um2=10000,
              implementation_note='Use parallel capacitor cells within the installed plate-area rule; verify selected process option and all actual geometry before implementation.',
              ideal_capacitors_used_in_current_transients=True)
(out/'runner.py').write_bytes(Path(__file__).read_bytes())
(out/'budget.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
