from pathlib import Path
import pya
root=Path('/foss/designs')
v=pya.LayoutView();v.load_layout(str(root/'build/power-ring/power_ring.gds'),0)
v.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp')
v.add_missing_layers();v.set_config('text-visible','false');v.set_config('grid-visible','false');v.max_hier();v.zoom_box(pya.DBox(-10,-10,1120,1020))
v.save_image(str(root/'docs/assets/power-ring-layout.png'),1400,1300)

v=pya.LayoutView();v.load_layout(str(root/'build/power-ring/ring_sensor_power.gds'),0)
v.select_cell(v.active_cellview().layout().cell('ring_sensor_power').cell_index(),0)
v.load_layer_props('/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp');v.add_missing_layers();v.set_config('text-visible','false');v.set_config('grid-visible','false');v.max_hier();v.zoom_box(pya.DBox(-10,-10,1120,1020));v.save_image(str(root/'docs/assets/power-ring-sensor.png'),1400,1300)
