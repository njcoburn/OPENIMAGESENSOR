"""Audit and archive the exact readout layout verified by both DRC engines and LVS."""
from pathlib import Path
import json,re,hashlib,shutil,xml.etree.ElementTree as ET
import pya
root=Path('/foss/designs');check=root/'build/readout-check'
log=(check/'magic.log').read_text();count=int(re.search(r'READOUT_DRC_COUNT=(\d+)',log)[1])
items=ET.parse(check/'klayout.lyrdb').findall('.//items/item')
match='Circuits match uniquely.' in (check/'lvs.log').read_text()
assert count==0 and len(items)==0 and match,(count,len(items),match)
gds=root/'build/column_readout.gds'
report={'magic_drc_count':count,'klayout_drc_count':len(items),'lvs_unique_match':match,'gds_sha256':hashlib.sha256(gds.read_bytes()).hexdigest(),'scope':'Standalone bias/mux block, 7 NMOS; includes density fill. Not connected physically to array. No pad ring, output buffer or readout RC extraction yet.'}
(root/'simulations/readout-verification.json').write_text(json.dumps(report,indent=2)+'\n')
dest=root/'checkpoints/readout';dest.mkdir(exist_ok=True)
for p in [gds,check/'readout_extracted.spice',check/'lvs.log',check/'magic.log',check/'klayout.lyrdb']:
 shutil.copyfile(p,dest/p.name)
for src,name in [('column_readout.gds','readout-layout.png'),('column_readout-functional.gds','readout-functional.png')]:
 view=pya.LayoutView();view.load_layout(str(root/'build'/src),0);view.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp');view.add_missing_layers()
 it=view.begin_layers()
 while not it.at_end():
  prop=it.current()
  if prop.source_layer==0 and prop.source_datatype==0:prop.visible=False;view.set_layer_properties(it,prop)
  it.next()
 view.max_hier();view.zoom_fit();view.save_image(str(root/'docs/assets'/name),1600,650)
print(report)
