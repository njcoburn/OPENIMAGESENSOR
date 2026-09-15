"""Prepare isolated, reproducible diode-size variants; preserve baseline artifacts."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
for size in (5,10,20):
 out=root/f'build/size-study/{size}um'
 out.mkdir(parents=True,exist_ok=True)
 for directory in ('scripts','layout','xschem'):
  shutil.copytree(root/directory,out/directory,dirs_exist_ok=True)
 for directory in ('build','simulations','docs/assets'):(out/directory).mkdir(parents=True,exist_ok=True)
 h=size/2;cy=5 if size==20 else 10
 p=out/'layout/diode-probe.tcl';s=p.read_text().replace('pars w 5',f'pars w {size}').replace('pars l 5',f'pars l {size}')
 s=s.replace('-2.5um -2.5um 2.5um 2.5um',f'-{h}um -{h}um {h}um {h}um').replace('1.885um -0.115um 2.115um 0.115um',f'{h-.615}um -0.115um {h-.385}um 0.115um').replace('1.8um -0.2um 2.2um 0.2um',f'{h-.7}um -0.2um {h-.3}um 0.2um').replace('A 1 0 -2.99 K 2 2 0',f'A 1 0 -{h+.49} K 2 {h-.5} 0');p.write_text(s)
 p=out/'layout/array_3x3.py';s=p.read_text().replace('r.dmove((60,10))',f'r.dmove((60,{cy}))')
 if size!=5:
  s=s.replace("terminal(62,10,65,'sense')",f"terminal({60+h-.5},{cy},73,'sense')").replace("terminal(60,7.01,67,'GND')",f"terminal(60,{cy-h-.49},72,'GND')")
 s=s.replace('diode_area_um2=25,diode_perimeter_um=20',f'diode_area_um2={size*size},diode_perimeter_um={4*size}')
 p.write_text(s)
 p=out/'layout/add_fill.py';s=p.read_text().replace('y=10+50*r',f'y={cy}+50*r').replace('5.5',str(h+3))
 if size==20:s=s.replace('u(0),u(240)', 'u(-8),u(240)')
 if size != 5:s=s.replace('assert abs(dbu-.001)<1e-12', 'assert abs(dbu-.001)<1e-12\n# Remove nonphysical primitive bounding boxes before density checks.\nly.clear_layer(ly.layer(0,0))')
 p.write_text(s)
 p=out/'layout/array_3x3.spice';p.write_text(p.read_text().replace('area=25p pj=20u',f'area={size*size}p pj={4*size}u'))
 p=out/'scripts/make-array-schematics.py';p.write_text(p.read_text().replace('r_w=5u r_l=5u',f'r_w={size}u r_l={size}u').replace('5 x 5 um',f'{size} x {size} um'))
 p=out/'scripts/simulate-array.py';s=p.read_text().replace('pattern=[[0,5,15],[15,0,5],[5,15,0]]',f'pattern=(np.array([[0,5,15],[15,0,5],[5,15,0]])*{(size/5)**2}).tolist()');p.write_text(s)
 print(out)
