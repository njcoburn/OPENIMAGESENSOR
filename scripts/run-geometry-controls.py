"""Matched terminal planes and small bend/via DC diagnostics (not fabrication cells)."""
from pathlib import Path
import json, subprocess
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/geometry-controls';base.mkdir(exist_ok=True)
prior=json.loads((ROOT/'build/filler-stitch/geometry.json').read_text())
fixtures={
 'straight':{81:[[-5000,0,5000,2000]]},
 'bend':{81:[[-5000,0,1000,2000],[-1000,2000,1000,4000],[-1000,4000,5000,6000]]},
 'via_bridge':{81:[[-5000,0,-1000,2000],[1000,0,5000,2000]],46:[[-1500,0,1500,2000]],41:[[-1380,870,-1120,1130],[1120,870,1380,1130]]},
 'wide_via_bridge':{81:[[-5000,0,-1000,2000],[1000,0,5000,2000]],46:[[-1500,0,1500,2000]],41:[[-1380,y,-1120,y+260] for y in [350,870,1390]]+[[1120,y,1380,y+260] for y in [350,870,1390]]}}
for name,shapes in fixtures.items():
 d=base/name;d.mkdir(exist_ok=True);l=k.Layout();l.dbu=.001;c=l.create_cell('control')
 rects={z:shapes.get(z,[]) for z in [34,36,42,46,81,35,38,40,41]}
 for z,boxes in rects.items():
  for b in boxes:c.shapes(l.layer(z,0)).insert(k.Box(*b))
 l.write(str(d/'control.gds'))
 by=5 if name=='bend' else 1
 ports=[{'name':'test_A','x':-4.9,'y':1,'half_x_um':.1,'half_y_um':1},{'name':'test_B','x':4.9,'y':by,'half_x_um':.1,'half_y_um':1}]
 geo={key:prior[key] for key in ['sheet_ohm_per_square','via_ohm_per_cut','tech_sha256']};geo.update(dbu_um=.001,rects=rects,ports=ports,seam_dbu=0,expected_intervals=1)
 (d/'geometry.json').write_text(json.dumps(geo,indent=2)+'\n')
 t=['drc off',f'gds read {d}/control.gds','load control','select top cell']
 # The observed Magic lower-left x coordinates now coincide with FV inner electrode faces.
 for idx,(label,x,y) in enumerate([('test_A',-4.8,0),('test_B',4.8,by-1)],1):
  t += [f'box values {x}um {y}um {x+.01}um {y+2}um',f'label {label} center m5',f'port make {idx}',f'port {label} class '+('input' if idx==1 else 'output')]
 t += ['extract do resistance','extresist threshold -1','extresist minres 1','extresist mindelay 0','extresist simplify off','extresist include test_B','extract all','ext2spice lvs','ext2spice cthresh infinite','ext2spice extresist on','ext2spice subcircuits top on','ext2spice -o rc.spice','quit -noprompt']
 (d/'extract.tcl').write_text('\n'.join(t)+'\n')
 with (d/'magic.log').open('w') as f:subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(d/'extract.tcl')],cwd=d,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
 for step in [.2,.1,.05]:
  out=d/f'mesh-{step}';out.mkdir(exist_ok=True)
  cmd=['python3',str(ROOT/'scripts/compare-filler-stitch.py'),'--geometry-file',str(d/'geometry.json'),'--output-dir',str(out),'--step-um',str(step),'--electrode-model','equipotential','--align-vias','--skip-spice']
  with (out/'driver.log').open('w') as f:subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 print(name,'complete',flush=True)
