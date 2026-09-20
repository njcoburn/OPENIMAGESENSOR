"""Make unchanged foundry-macro coupons and conductor-only controls for RC experiments."""
from pathlib import Path
import json,hashlib
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/ring-sections';out.mkdir(parents=True,exist_ok=True)
source=Path('/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/gds/gf180mcu_fd_io.gds')
s=k.Layout();s.read(str(source));layers=[34,35,36,38,40,41,42,46,81]
straight={'VDD':257.29,'VSS':250.115,'DVDD':221.84,'DVSS':237.975}
corner_top={'VDD':257.49,'VSS':249.245,'DVDD':221.46,'DVSS':237.615}
corner_right={'VDD':257.055,'VSS':249.88,'DVDD':221.605,'DVSS':237.74}
for name,parts in {'fill10':[('fill10',0)],'fill20':[('fill10',0),('fill10',10)],'corner':[('cor',0)],'corner_fill':[('cor',0),('fill10',355)]}.items():
 folder=out/name;folder.mkdir(exist_ok=True);l=k.Layout();l.dbu=s.dbu;c=l.create_cell(name)
 for macro,x in parts:
  child=l.cell('gf180mcu_fd_io__'+macro)
  if child is None:child=l.create_cell('gf180mcu_fd_io__'+macro);child.copy_tree(s.cell(child.name))
  c.insert(k.CellInstArray(child.cell_index(),k.Trans(round(x/l.dbu),0)))
 # Export after adding explicit measurement terminals.
 metal=l.create_cell(name+'_metal')
 for z in layers:
  region=k.Region(c.begin_shapes_rec(l.layer(z,0))).merged();metal.shapes(l.layer(z,0)).insert(region)
  assert (region^k.Region(metal.begin_shapes_rec(l.layer(z,0))).merged()).is_empty()
 # Conductor controls receive the same measurement leads.
 ports=[]
 for rail in straight:
  if name.startswith('fill'):a=(.5,straight[rail]);b=((9.5 if name=='fill10' else 19.5),straight[rail])
  else:a=(corner_top[rail],354.5);b=((354.5,corner_right[rail]) if name=='corner' else (364.5,straight[rail]))
  ports += [{'name':rail+'_A','rail':rail,'x':a[0],'y':a[1]},{'name':rail+'_B','rail':rail,'x':b[0],'y':b[1]}]
 # Narrow external probe leads create distinct extraction tiles for passive rail terminals.
 # The quoted resistance includes this test fixture; it is not a bare macro-edge resistance.
 for p in ports:
  x,y=p['x'],p['y']
  if name.startswith('fill'):
   xx=x+(-2.5 if p['name'].endswith('_A') else 2.5);yy=y
  elif p['name'].endswith('_A'):xx=x;yy=357
  else:xx=x+2.5;yy=y
  shape=k.Box(round((min(x,xx)-.2)/l.dbu),round((min(y,yy)-.2)/l.dbu),round((max(x,xx)+.2)/l.dbu),round((max(y,yy)+.2)/l.dbu))
  for target in [c,metal]:target.shapes(l.layer(81,0)).insert(shape)
  p['macro_probe_x']=x;p['macro_probe_y']=y;p['x']=xx;p['y']=yy
 for target,filename in [(c,'full.gds'),(metal,'metal.gds')]:
  opt=k.SaveLayoutOptions();opt.add_cell(target.cell_index());l.write(str(folder/filename),opt)
 # Physical check of every terminal and all foundry supply labels without joining names.
 n=k.LayoutToNetlist(k.RecursiveShapeIterator(l,c,[]));m={z:n.make_polygon_layer(l.layer(z,0),'m'+str(z)) for z in [34,36,42,46,81]}
 for v in m.values():n.connect(v)
 for z,a,b in [(35,34,36),(38,36,42),(40,42,46),(41,46,81)]:
  v=n.make_polygon_layer(l.layer(z,0),'v'+str(z));n.connect(m[a],v);n.connect(v,m[b])
 n.extract_netlist()
 def probe(z,x,y):
  net=n.probe_net(m[z],k.DPoint(x,y));assert net is not None,(name,z,x,y)
  return (net.circuit().name,net.cluster_id)
 groups={rail:probe(81,p['x'],p['y']) for rail in straight for p in ports if p['name']==rail+'_A'}
 assert len(set(groups.values()))==4
 for p in ports:assert probe(81,p['x'],p['y'])==groups[p['rail']],p
 count=0
 for inst in c.each_inst():
  for z in m:
   for sh in inst.cell.shapes(l.layer(z,10)).each():
    if sh.is_text() and sh.text.string in groups:
     off=sh.text.trans.disp;pt=(inst.cplx_trans*k.Point(off.x,off.y)).to_dtype(l.dbu)
     assert probe(z,pt.x,pt.y)==groups[sh.text.string];count+=1
 meta={'name':name,'instances':parts,'ports':ports,'physical_label_probes':count,'four_distinct_rails':True,'conductor_masks_equal':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Point-terminal extraction coupon with 0.4 um M5 probe leads; resistance includes the leads. Not an equipotential-edge or complete macro replacement.'}
 (folder/'geometry.json').write_text(json.dumps(meta,indent=2)+'\n')
 for mode in ['full','metal']:
  work=folder/mode;work.mkdir(exist_ok=True);cell=name+('_metal' if mode=='metal' else '')
  lines=['drc off',f'gds read {folder}/{mode}.gds',f'load {cell}','select top cell','flatten coupon','load coupon','select top cell','box values -5um -5um 400um 400um','erase labels']
  for idx,p in enumerate(ports,1):
   x,y=p['x'],p['y'];lines += [f'box values {x-.1}um {y-.1}um {x+.1}um {y+.1}um',f'label {p["name"]} center m5',f'port make {idx}',f'port {p["name"]} class '+('input' if p['name'].endswith('_A') else 'output')]
  lines += ['extract do capacitance','extract do coupling','extract do resistance','extresist threshold 0','extresist minres 1','extresist mindelay 0','extresist simplify off','extract all','ext2spice lvs','ext2spice subcircuits top on','extresist threshold 0','extresist minres 1','extresist mindelay 0','extresist simplify off','ext2spice cthresh 0','ext2spice extresist on','ext2spice -o rc.spice','quit -noprompt']
  (work/'extract.tcl').write_text('\n'.join(lines)+'\n')
 print(name,':',count,'label probes passed; four distinct rails; conductor masks preserved')
