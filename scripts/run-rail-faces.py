"""Remove coupon leads and measure VDD through full-width ideal M5 end faces."""
from pathlib import Path
import json,subprocess
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/rail-faces';base.mkdir(exist_ok=True)
for source in sorted((ROOT/'build/rail-isolation').glob('m5-to-m*'),reverse=True):
 d=base/source.name;d.mkdir(exist_ok=True);g=json.loads((source/'geometry.json').read_text())
 # Clip to the actual two-filler x extent; preserve every interior rectangle.
 for z,boxes in g['rects'].items():g['rects'][z]=[[max(0,a),b,min(20000,c),e] for a,b,c,e in boxes if min(20000,c)>max(0,a)]
 # Ideal extensions put inward electrode faces exactly at x=0 and x=20 µm.
 g['rects']['81'] += [[-200,254000,0,261000],[20000,254000,20200,261000]]
 g['ports']=[{'name':'VDD_A','x':-.1,'y':257.5,'half_x_um':.1,'half_y_um':3.5},{'name':'VDD_B','x':20.1,'y':257.5,'half_x_um':.1,'half_y_um':3.5}]
 g['scope']='Clipped x=0..20um VDD component with full-width ideal M5 electrodes; no physical probe leads.'
 layout=k.Layout();layout.dbu=.001;c=layout.create_cell('rail');intervals=0
 for z,boxes in g['rects'].items():
  region=k.Region()
  for box in boxes:c.shapes(layout.layer(int(z),0)).insert(k.Box(*box));region.insert(k.Box(*box))
  if int(z) in [34,36,42,46,81]:intervals+=len(list((region.merged()&k.Region(k.Box(9999,-1000000,10001,1000000))).merged().each()))
 g['expected_intervals']=intervals;(d/'geometry.json').write_text(json.dumps(g,indent=2)+'\n');layout.write(str(d/'rail.gds'))
 t=['drc off',f'gds read {d}/rail.gds','load rail','select top cell']
 for idx,(n,x) in enumerate([('VDD_A',0),('VDD_B',20)],1):t += [f'box values {x}um 254um {x+.01}um 261um',f'label {n} center m5',f'port make {idx}']
 t += ['extract do resistance','extresist threshold 0','extresist minres 1','extresist mindelay 0','extresist simplify off','extresist include VDD_B','extract all','extresist all','ext2spice lvs','ext2spice cthresh infinite','ext2spice extresist on','ext2spice subcircuits top on','ext2spice -o rc.spice','quit -noprompt']
 (d/'extract.tcl').write_text('\n'.join(t)+'\n')
 with (d/'magic.log').open('w') as f:subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(d/'extract.tcl')],cwd=d,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
 assert 'Usage:' not in (d/'magic.log').read_text()
 for step in [.25,.1,.05]:
  out=d/f'mesh-{step}';out.mkdir(exist_ok=True)
  with (out/'driver.log').open('w') as f:subprocess.run(['python3',str(ROOT/'scripts/compare-filler-stitch.py'),'--geometry-file',str(d/'geometry.json'),'--output-dir',str(out),'--step-um',str(step),'--electrode-model','equipotential','--align-vias','--skip-spice'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
 print(source.name,'complete',flush=True)
