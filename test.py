import gdsfactory as gf
from gdsfactory.typings import ComponentSpec


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


@gf.cell
def reset_transistor(photodiode_spec: ComponentSpec = nwell_psub_photodiode, reset_distance_from_photo_diode=1.0):

    reset_transistor = gf.Component()

    photodiode = gf.get_component(photodiode_spec)
    # Create reset transistor
    nfet_component = gf180mcu.cells.nfet(
        w_gate=0.36, l_gate=0.36, label=True, sd_label=['S', 'D'], g_label=["gate"]).copy()
    gf.add_ports.add_ports_from_labels(component=nfet_component, port_width=0.36,
                                       port_layer=gf180mcu.LAYER.metal1, layer_label=gf180mcu.LAYER.metal1_label, port_type="electrical")

    nfet_ref = reset_transistor.add_ref(nfet_component)
    reset_transistor.add_ports(nfet_ref.ports)

    # Add patch metal to meet overlap rules on M1 to contact
    source_port_ref = nfet_component.add_ref(gf.components.rectangle(size=(
        nfet_component.ports["e1"].width, nfet_component.ports["e1"].width), layer=gf180mcu.LAYER.metal1))
    source_port_ref.center = nfet_ref.ports["e1"].center

    reset_transistor.center = photodiode.ports["e1"].center
    reset_transistor.dxmin = photodiode.dxmax + reset_distance_from_photo_diode

    return reset_transistor


@gf.cell
def source_follower_nfet(photodiode_spec: ComponentSpec = nwell_psub_photodiode, reset_transistor_spec: ComponentSpec = reset_transistor, max_distance_from_nwell=0.4):
    source_follower_nfet = gf.Component()
    photodiode = gf.get_component(photodiode_spec)
    reset_transistor = gf.get_component(reset_transistor_spec)

    nfet_component = gf180mcu.cells.nfet(
        w_gate=1.5, l_gate=0.36, label=True, sd_label=['D', 'S'], g_label=["gate"], enable_left_diffusion_contacts=False).copy()
    gf.add_ports.add_ports_from_labels(component=nfet_component, port_width=0.36,
                                       port_layer=gf180mcu.LAYER.metal1, layer_label=gf180mcu.LAYER.metal1_label, port_type="electrical", guess_port_orientation=False, port_orientation=270)

    # # Add patch metal to meet overlap rules on M1 to contact
    source_port_ref = nfet_component.add_ref(gf.components.rectangle(size=(
        nfet_component.ports["e3"].width, nfet_component.ports["e3"].width), layer=gf180mcu.LAYER.metal1))
    source_port_ref.center = nfet_component.ports["e3"].center

    poly2poly_spacing_min_rule = 0.28
    nwell_to_nplus_spacing = 0.4
    nfet_ref = source_follower_nfet.add_ref(nfet_component)
    nfet_ref.center = reset_transistor.ports["e1"].center
    nfet_ref.ymax = reset_transistor.ymin + poly2poly_spacing_min_rule
    nfet_ref.xmin = min(max(nfet_ref.xmin - photodiode.xmax,
                        nwell_to_nplus_spacing), max_distance_from_nwell) + photodiode.xmax

    source_follower_nfet.add_ports(nfet_ref.ports)
    source_follower_nfet.rotate(180, center=source_follower_nfet.center)

    return source_follower_nfet


@gf.cell
def row_select(source_follower_spec: ComponentSpec = source_follower_nfet):

    row_select = gf.Component()

    source_follower = gf.get_component(source_follower_spec)
    # Create reset transistor
    nfet_component = gf180mcu.cells.nfet(
        w_gate=0.36, l_gate=0.36, label=True, sd_label=['S', 'D'], g_label=["gate"], enable_left_diffusion_contacts=False).copy()
    gf.add_ports.add_ports_from_labels(component=nfet_component, port_width=0.36,
                                       port_layer=gf180mcu.LAYER.metal1, layer_label=gf180mcu.LAYER.metal1_label, port_type="electrical")

    nfet_ref = row_select.add_ref(nfet_component)
    row_select.add_ports(nfet_ref.ports)

    row_select.pprint_ports()

    row_select.x = row_select.x + \
        (source_follower.ports["e1"].x - row_select.ports["e1"].x) + 0.23
    row_select.y = row_select.y + \
        (source_follower.ports["e1"].y - row_select.ports["e1"].y)

    return row_select


@gf.cell
def active_pixel_3t(
        photodiode_spec: ComponentSpec = nwell_psub_photodiode,
        reset_transistor_spec: ComponentSpec = reset_transistor,
        source_follower_spec: ComponentSpec = source_follower_nfet,
        row_select_spec: ComponentSpec = row_select):

    active_pixel = gf.Component()
    photodiode = gf.get_component(photodiode_spec)
    reset_transistor = gf.get_component(reset_transistor_spec)
    source_follower_nfet = gf.get_component(source_follower_spec)
    row_select = gf.get_component(row_select_spec)

    source_follower_nfet.pprint_ports()

    photodiode_ref = active_pixel << photodiode
    active_pixel << reset_transistor
    active_pixel << source_follower_nfet
    active_pixel << row_select

    # 4a. Define a cross-section for the metal route
    #     We'll tell it to use metal1 and the same width as the port
    metal1_xs = gf.cross_section.cross_section(
        layer=gf180mcu.LAYER.metal1,
        width=reset_transistor.ports["e1"].width,
    )

    # 4b. Call the router
    #     We connect the ports from the *references*
    route = gf.routing.route_single_electrical(
        component=active_pixel,
        port1=photodiode_ref.ports["e1"],
        port2=reset_transistor.ports["e1"],
        cross_section=metal1_xs,
    )

    # 4a. Define a cross-section for the metal route
    #     We'll tell it to use metal1 and the same width as the port
    metal1_xs = gf.cross_section.cross_section(
        layer=gf180mcu.LAYER.metal1,
        width=source_follower_nfet.ports["e3"].width,
    )

    # 4b. Call the router
    #     We connect the ports from the *references*
    route = gf.routing.route_single_electrical(
        component=active_pixel,
        port2=source_follower_nfet.ports["e3"],
        port1=reset_transistor.ports["e1"],
        cross_section=metal1_xs,
    )

    return active_pixel


gf.kcl.dbu = 5e-3  # set 1 DataBase Unit to 5 nm


gf180mcu.PDK.activate()

com = active_pixel_3t()

com.show()
