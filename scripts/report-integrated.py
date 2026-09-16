"""Archive checked integrated layout and render actual geometry."""
from pathlib import Path
import json,re,hashlib,shutil,xml.etree.ElementTree as ET
import pya
root=Path('/foss/designs');check=root/'build/integrated'
count=int(re.search(r'INTEGRATED_DRC_COUNT=(\d+)',(check/'magic.log').read_text())[1])
items=ET.parse(check/'klayout.lyrdb').findall('.//items/item')
match='Circuits match uniquely.' in (check/'lvs.log').read_text()
assert count==0 and not items and match,(count,len(items),match)
gds=check/'sensor_3x3.gds'
report={'magic_drc_count':count,'klayout_drc_count':len(items),'lvs_unique_match':match,'gds_sha256':hashlib.sha256(gds.read_bytes()).hexdigest(),'transistors':37,'photodiodes':9,'scope':'Connected 3x3 array, column bias/mux and PMOS buffer with common metal supply/ground and floating density fill. No pads, ESD, reference generators or digital control.'}
(root/'simulations/integrated-verification.json').write_text(json.dumps(report,indent=2)+'\n')
dest=root/'checkpoints/integrated'
for name in ['sensor_3x3.gds','sensor-functional.gds','placement.json','integrated_extracted.spice','lvs.log','magic.log','klayout.lyrdb']:shutil.copyfile(check/name,dest/name)
for name,img in [('sensor_3x3.gds','integrated-layout.png'),('sensor-functional.gds','integrated-functional.png')]:
 view=pya.LayoutView();view.load_layout(str(check/name),0);view.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp');view.add_missing_layers();view.max_hier();view.zoom_box(pya.DBox(-42,0,302,252));view.save_image(str(root/'docs/assets'/img),1500,1100)
print(report)
