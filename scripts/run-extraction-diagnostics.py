"""Controlled via-array edits and matched-version Magic export investigation."""
from pathlib import Path
import json,subprocess
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/extraction-diagnostics';base.mkdir(exist_ok=True)
src=ROOT/'build/rail-faces/m5-to-m4';original=json.loads((src/'geometry.json').read_text());cuts=original['rects']['41'];xs=sorted(set(b[0] for b in cuts));ys=sorted(set(b[1] for b in cuts))
variants={'two_end_cuts':[b for b in cuts if b[0] in [xs[0],xs[-1]] and b[1]==ys[len(ys)//2]],'two_end_columns':[b for b in cuts if b[0] in [xs[0],xs[-1]]],'missing_one_cut':[b for b in cuts if b!=cuts[len(cuts)//2]],'all_cuts':cuts}
for name,selected in variants.items():
 d=base/name;d.mkdir(exist_ok=True);g=json.loads(json.dumps(original));g['rects']['41']=selected
 layout=k.Layout();layout.dbu=.001;cell=layout.create_cell('rail')
 for z,boxes in g['rects'].items():
  for b in boxes:cell.shapes(layout.layer(int(z),0)).insert(k.Box(*b))
 layout.write(str(d/'rail.gds'));(d/'geometry.json').write_text(json.dumps(g,indent=2)+'\n')
 t=(src/'extract.tcl').read_text().replace(str(src),str(d));(d/'extract.tcl').write_text(t)
 with (d/'magic.log').open('w') as f:subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(d/'extract.tcl')],cwd=d,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
 assert 'Usage:' not in (d/'magic.log').read_text()
 for step in [.1,.05]:
  out=d/f'mesh-{step}';out.mkdir(exist_ok=True)
  with (out/'driver.log').open('w') as f:subprocess.run(['python3',str(ROOT/'scripts/compare-filler-stitch.py'),'--geometry-file',str(d/'geometry.json'),'--output-dir',str(out),'--step-um',str(step),'--electrode-model','equipotential','--align-vias','--skip-spice'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 print(name,len(selected),'cuts complete',flush=True)
