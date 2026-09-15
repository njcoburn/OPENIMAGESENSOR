# Run with klayout -b -r scripts/render-array.py
import pya
from pathlib import Path
root=Path('/foss/designs')
for src,dest in [('array_3x3.gds','array-layout.png'),('array-functional.gds','array-functional.png'),('pixel_physical.gds','pixel-layout.png')]:
 if not (root/'build'/src).exists():continue
 view=pya.LayoutView()
 view.load_layout(str(root/'build'/src),0)
 view.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp')
 view.add_missing_layers()
 it=view.begin_layers()
 while not it.at_end():
  prop=it.current()
  if prop.source_layer==0 and prop.source_datatype==0:
   prop.visible=False;view.set_layer_properties(it,prop)
  it.next()
 view.max_hier();view.zoom_fit()
 view.save_image(str(root/'docs/assets'/dest),1500,1000)
