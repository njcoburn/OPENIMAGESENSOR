import gdsfactory as gf


import gf180mcu


def photo_diode():
    # corresponds to 8um in gf180mcu
    photo_sensitive_width_and_height = 5
    photo_diode_rect = gf.Component()
    photo_diode_nwell = gf.components.rectangle(
        size = (photo_sensitive_width_and_height, photo_sensitive_width_and_height), 
        layer= gf180mcu.LAYER.nwell)
    
    photo_diode_rect << photo_diode_nwell

    rinner = 100
    router = 100
    n = 300 # points in circle
    # Round corners for all layers.
    photo_diode_rounded = gf.Component("photo_sensitve_area")
    for layer, polygons in photo_diode_rect.get_polygons().items():
        for p in polygons:
            p_round = p.round_corners(rinner, router, n)
            photo_diode_rounded.add_polygon(p_round, layer=layer)

    

    contact_layer = photo_diode_rounded.add_ref(gf180mcu.cells.via_stack(x_range=(0,0.5), y_range=(0,1)))
    
    rounded_corner_width_and_height = gf.kcl.dbu * router
    nplus = photo_diode_rounded.add_ref(gf.components.rectangle(size = (0.4, contact_layer.ysize + (0.4 - contact_layer.xsize)), layer=gf180mcu.LAYER.nplus))
    nplus.dxmax = photo_diode_rounded.dxmax 
    nplus.dymax = photo_diode_rounded.dymax - rounded_corner_width_and_height

    contact_layer.center = nplus.center

    return photo_diode_rounded


gf.kcl.dbu = 5e-3  # set 1 DataBase Unit to 5 nm


gf180mcu.PDK.activate()

component = photo_diode()
component.pprint_ports()

component.show()
