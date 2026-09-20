"""Package the self-contained KiCad review projects and their reproducible tooling."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent;root=R.parents[1]
checks=json.loads((R/'reports/checks.json').read_text())
for name,c in checks.items():
 for ext,key in [('kicad_pcb','pcb_sha256'),('kicad_sch','schematic_sha256')]:
  assert hashlib.sha256((R/'kicad'/name/(name+'.'+ext)).read_bytes()).hexdigest()==c[key], 'Checks stale'
 assert c['error_count']==0 and c['warning_count']==0 and c['schematic_pin_net_match']
files=[p for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.zip','.kicad_prl','.pyc','.log'] and p.name!='openimagesensor-kicad-review.sha256']
files += [root/'scripts/run-kicad.sh',root/'tools/kicad/Dockerfile',root/'docs/routed-pad-map.csv',root/'docs/carrier-fixture.html']
out=R/'openimagesensor-kicad-review.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):z.write(f,'OPENIMAGESENSOR/'+str(f.relative_to(root)))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
(R/'openimagesensor-kicad-review.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n')
print(out.name, len(files),'files',out.stat().st_size,'bytes; archive integrity and checked file hashes pass')
