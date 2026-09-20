from pathlib import Path
import klayout.db as k,json
ROOT=Path(__file__).resolve().parents[1];l=k.Layout();l.read(str(ROOT/'build/ring-sections/fill20/full.gds'));c=l.cell('fill20');result={}
for z in [34,36,42,46,81]:
 r=k.Region(c.begin_shapes_rec(l.layer(z,0))).merged();b=r&k.Region(k.Box(9999,0,10001,350000));intervals=[(p.bbox().bottom*l.dbu,p.bbox().top*l.dbu) for p in b.each()];result[z]=intervals;print(z,len(intervals),intervals[:6])
Path(ROOT/'build/ring-sections/boundary-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
