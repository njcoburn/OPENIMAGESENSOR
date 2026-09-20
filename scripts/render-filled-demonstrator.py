from pathlib import Path
import pya
R=Path('/foss/designs');v=pya.LayoutView();v.load_layout(str(R/'build/filled-demonstrator/demonstrator_filled.gds'),0)
v.select_cell(v.active_cellview().layout().cell('demonstrator_routed').cell_index(),0)
v.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp');v.add_missing_layers();v.set_config('text-visible','false');v.set_config('grid-visible','false');v.max_hier()
v.zoom_box(pya.DBox(-10,-10,1220,1220));v.save_image(str(R/'docs/assets/filled-demonstrator.png'),1500,1500)
v.zoom_box(pya.DBox(350,350,860,860));v.save_image(str(R/'docs/assets/filled-core-routing.png'),1500,1500)
