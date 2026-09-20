"""Prepare exact Manhattan geometry for independent finite-volume DC stitching checks."""
from pathlib import Path
import json,hashlib,re
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/filler-stitch';out.mkdir(exist_ok=True,parents=True)
source=ROOT/'build/ring-sections/fill20/metal.gds';l=k.Layout();l.read(str(source));c=l.cell('fill20_metal');regions={};rects={}
for z in [34,36,42,46,81,35,38,40,41]:
 r=k.Region(c.begin_shapes_rec(l.layer(z,0))).merged();regions[z]=r;rects[z]=[]
 for poly in r.each():
  for part in poly.decompose_trapezoids():
   b=part.bbox();assert part.area()==b.area(),('non-Manhattan rectangle',z,b)
   rects[z].append([b.left,b.bottom,b.right,b.top])
 # Reconstruct independently to establish no shape loss in the rectangular representation.
 check=k.Region();[check.insert(k.Box(*b)) for b in rects[z]];assert (r^check.merged()).is_empty()
left=k.Region(k.Box(-10000,-1000,10000,351000));right=k.Region(k.Box(10000,-1000,30000,351000))
for z,r in regions.items():assert (((r&left)|(r&right))^r).is_empty()
# Via cuts must not be bisected; otherwise their ownership and interface stamping need extension.
assert all(not (a<10000<b) for z in [35,38,40,41] for a,y,b,t in rects[z])
tech=Path('/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech');s=tech.read_text();start=s.index('# Resistances are in milliohms per square');s=s[start:s.index('variants (hrhc)',start)]
sheet={z:float(re.search(r'resist \(allm'+str(i)+r'\)/metal'+str(i)+r'\s+(\d+)',s)[1])/1000 for i,z in enumerate([34,36,42,46,81],1)}
via={z:float(re.search(r'contact '+n+r'\s+(\d+)',s)[1])/1000 for z,n in [(35,'m2c'),(38,'m3c'),(40,'via3'),(41,'via4')]}
meta=json.loads((ROOT/'build/ring-sections/fill20/geometry.json').read_text())
data={'dbu_um':l.dbu,'rects':rects,'sheet_ohm_per_square':sheet,'via_ohm_per_cut':via,'ports':meta['ports'],'seam_dbu':10000,'gds_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'tech_sha256':hashlib.sha256(tech.read_bytes()).hexdigest(),'region_reconstruction_exact':True,'partition_union_exact':True,'no_split_vias':True}
(out/'geometry.json').write_text(json.dumps(data,indent=2)+'\n')
print('Rectangles per layer:',{z:len(b) for z,b in rects.items()});print('Metal sheets',sheet,'via resistances',via)
xs={x for rs in rects.values() for a,y,b,t in rs for x in [a,b]};ys={y for rs in rects.values() for a,y,b,t in rs for y in [y,t]};print('Exact coordinate counts',len(xs),len(ys),'base grid cells',(len(xs)-1)*(len(ys)-1))
