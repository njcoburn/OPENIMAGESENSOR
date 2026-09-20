"""Keep coupon geometry fixed; place full-width electrode faces at Magic label x positions."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
g=json.loads((ROOT/'build/filler-stitch/geometry.json').read_text())
for p in g['ports']:
 p.update(x=-2.15 if p['name'].endswith('_A') else 22.05,half_x_um=.05 if p['name'].endswith('_A') else .15,half_y_um=.2)
out=ROOT/'build/geometry-controls';out.mkdir(exist_ok=True)
(out/'filler-matched.json').write_text(json.dumps(g,indent=2)+'\n')
