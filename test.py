import gdsfactory as gf


import gf180mcu


@gf.cell
def nwell_psub_photodiode(width: int = 5):
    """Defines a nwell p-substrate photo diode

    Args:
        width: The width and height of the photo diode in microns
    """
    # corresponds to 8um in gf180mcu
    photo_diode_rect = gf.Component()
    photo_diode_nwell = gf.components.rectangle(
        size = (width, width), 
        layer= gf180mcu.LAYER.nwell)
    
    photo_diode_rect << photo_diode_nwell

    rinner = 100
    router = 100
    n = 300 # points in circle
    # Round corners for all layers.
    photo_diode_rounded = gf.Component()
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
    photo_diode_rounded.add_ports(contact_layer.ports)

    return photo_diode_rounded


gf.kcl.dbu = 5e-3  # set 1 DataBase Unit to 5 nm


gf180mcu.PDK.activate()

parent_com = gf.Component()


component = nwell_psub_photodiode()
parent_com << component

nfet = parent_com << gf180mcu.cells.nfet(w_gate=0.36, l_gate=0.36)
nfet.center = component.ports["e1"].center
nfet.dxmin = component.dxmax + 0.4

metal1_diode_con = parent_com << gf.components.rectangle(size = (1.1,component.ports["e1"].width), layer=gf180mcu.LAYER.metal1)
metal1_diode_con.center = component.ports["e1"].center
metal1_diode_con.xmin = component.ports["e1"].dx

component.pprint_ports()
parent_com.pprint_ports()
parent_com.show()
