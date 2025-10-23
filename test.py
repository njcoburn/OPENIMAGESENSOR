import gdsfactory as gf


import gf180mcu


def photo_diode():
    # corresponds to 8um in gf180mcu
    photo_sensitive_width_and_height = 8
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

    # Create the comp (active area) for the tap
    n_tap_comp = gf.components.rectangle(
        size=(2,2), layer=gf180mcu.LAYER.comp
    )
    #n_tap_comp.center = photo_diode_nwell.center
    photo_diode_rounded << n_tap_comp
    return photo_diode_rounded


gf.kcl.dbu = 5e-3  # set 1 DataBase Unit to 5 nm


gf180mcu.PDK.activate()

component = photo_diode()
component.pprint_ports()

component.show()
