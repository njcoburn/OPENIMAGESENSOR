from pathlib import Path
import klayout.db as k
root=Path('/foss/designs')
for p in (root/'build/pad-layout').glob('protect*.gds'):
 l=k.Layout();l.read(str(p));c=l.top_cell();print(p.name,c.dbbox())
 for layer in [(34,0),(21,0),(22,0)]:
  r=k.Region(c.begin_shapes_rec(l.layer(*layer)));print(layer,[str(p.bbox().to_dtype(l.dbu)) for p in r.merged().each()])
p=Path('/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/gds/gf180mcu_fd_io.gds');l=k.Layout();l.read(str(p))
for name in ['gf180mcu_fd_io__asig_5p0','gf180mcu_fd_io__dvdd','gf180mcu_fd_io__dvss']:
 c=l.cell(name);print(name,c.dbbox())
 for i in l.layer_indexes():
  for sh in c.shapes(i).each():
   if sh.is_text():print(l.get_info(i),sh.text.string,sh.text.trans.disp.to_dtype(l.dbu))
