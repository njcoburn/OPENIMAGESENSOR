from pathlib import Path
import pya
root=Path('/foss/designs')
for name,image,bounds,size in [('secondary-functional.gds','pad-secondary-layout.png',(-7,0,27,25),(1400,1000)),('analog_pad_interface.gds','pad-interface-layout.png',(-15,-5,90,393),(700,1600))]:
 view=pya.LayoutView();view.load_layout(str(root/'build/pad-layout'/name),0);view.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp');view.add_missing_layers();view.max_hier();view.zoom_box(pya.DBox(*bounds));view.save_image(str(root/'docs/assets'/image),*size)
