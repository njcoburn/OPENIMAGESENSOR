from pathlib import Path
import klayout.db as k
p=Path('/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io')
l=k.Layout();l.read(str(p/'gds/gf180mcu_fd_io.gds'))
for name in ['dvdd','dvss','cor','fill10']:
 c=l.cell('gf180mcu_fd_io__'+name);print(name,c.dbbox())
 for idx in l.layer_indexes():
  for sh in c.shapes(idx).each():
   if sh.is_text():print(str(l.get_info(idx)),sh.text.string,sh.text.trans.disp.to_dtype(l.dbu))
for file in (p/'spice').glob('*'):
 for line in file.read_text().splitlines():
  if line.lower().startswith('.subckt') and any('__'+n+' ' in line+' ' for n in ['dvdd','dvss','cor','fill10']):print(file.name,line)
