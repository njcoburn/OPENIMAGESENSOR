import klayout.db as k
l=k.Layout();l.read('/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/gds/gf180mcu_fd_io.gds')
for name in ['fill10','cor']:
 c=l.cell('gf180mcu_fd_io__'+name);n=k.LayoutToNetlist(k.RecursiveShapeIterator(l,c,[]));m={z:n.make_polygon_layer(l.layer(z,0),'m'+str(z)) for z in [34,36,42,46,81]}
 for v in m.values():n.connect(v)
 for z,a,b in [(35,34,36),(38,36,42),(40,42,46),(41,46,81)]:
  v=n.make_polygon_layer(l.layer(z,0),'v'+str(z));n.connect(m[a],v);n.connect(v,m[b])
 n.extract_netlist();groups={}
 for z in m:
  for sh in c.shapes(l.layer(z,10)).each():
   if sh.is_text():
    pt=sh.text.trans.disp.to_dtype(l.dbu);net=n.probe_net(m[z],pt)
    groups.setdefault(sh.text.string,set()).add((net.circuit().name,net.cluster_id) if net else None)
 print(name,{a:sorted(v) for a,v in groups.items()})
