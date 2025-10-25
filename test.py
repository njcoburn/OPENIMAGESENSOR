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
        size=(width, width),
        layer=gf180mcu.LAYER.nwell)

    photo_diode_rect << photo_diode_nwell

    rinner = 100
    router = 100
    n = 300  # points in circle
    # Round corners for all layers.
    photo_diode_rounded = gf.Component()
    for layer, polygons in photo_diode_rect.get_polygons().items():
        for p in polygons:
            p_round = p.round_corners(rinner, router, n)
            photo_diode_rounded.add_polygon(p_round, layer=layer)

    contact_layer = photo_diode_rounded.add_ref(
        gf180mcu.cells.via_stack(x_range=(0, 0.5), y_range=(0, 1)))

    rounded_corner_width_and_height = gf.kcl.dbu * router
    nplus = photo_diode_rounded.add_ref(gf.components.rectangle(size=(
        0.4, contact_layer.ysize + (0.4 - contact_layer.xsize)), layer=gf180mcu.LAYER.nplus))
    nplus.dxmax = photo_diode_rounded.dxmax
    nplus.dymax = photo_diode_rounded.dymax - rounded_corner_width_and_height

    contact_layer.center = nplus.center
    photo_diode_rounded.add_ports(contact_layer.ports)

    return photo_diode_rounded


gf.kcl.dbu = 5e-3  # set 1 DataBase Unit to 5 nm


gf180mcu.PDK.activate()

parent_com = gf.Component()


component = nwell_psub_photodiode()
photodiode_ref = parent_com << component

nfet_component = gf180mcu.cells.nfet(
    w_gate=0.36, l_gate=0.36, label=True, sd_label=['S', 'D']).copy()
gf.add_ports.add_ports_from_labels(component=nfet_component, port_width=0.36,
                                   port_layer=gf180mcu.LAYER.metal1, layer_label=gf180mcu.LAYER.metal1_label, port_type="electrical")
source_port_ref = nfet_component.add_ref(gf.components.rectangle(size = (component.ports["e1"].width, component.ports["e1"].width), layer=gf180mcu.LAYER.metal1))
source_port_ref.center = nfet_component.ports["e1"].center


nfet_component.pprint_ports()
nfet_ref = parent_com.add_ref(nfet_component)
nfet_ref.center = component.ports["e1"].center
nfet_ref.dxmin = component.dxmax + 0.4

# 4a. Define a cross-section for the metal route
#     We'll tell it to use metal1 and the same width as the port
metal1_xs = gf.cross_section.cross_section(
    layer=gf180mcu.LAYER.metal1,
    width=photodiode_ref.ports["e1"].width,
)

# 4b. Call the router
#     We connect the ports from the *references*
route = gf.routing.route_single_electrical(
    component=parent_com,
    port1=photodiode_ref.ports["e1"],
    port2=nfet_ref.ports["e1"],
    cross_section=metal1_xs,
)

component.pprint_ports()
parent_com.pprint_ports()
parent_com.show()
