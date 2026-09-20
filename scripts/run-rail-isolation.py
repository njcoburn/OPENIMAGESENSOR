"""Isolate the real VDD conductor component and add connected layers incrementally."""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/rail-isolation';base.mkdir(exist_ok=True)
g=json.loads((ROOT/'build/geometry-controls/filler-matched.json').read_text())
metals=[81,46,42,36,34];vias=[(41,81,46),(40,46,42),(38,42,36),(35,36,34)]
for count in [1,2,3,4,5]:
 name=f'm5-to-m{6-count}';d=base/name;d.mkdir(exist_ok=True)
 zs=metals[:count];boxes=[(z,b) for z in zs for b in g['rects'][str(z)]];parent=list(range(len(boxes)))
 def root(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 def union(a,b):parent[root(a)]=root(b)
 def overlap(a,b,touch=False):
  return min(a[2],b[2])>=max(a[0],b[0]) and min(a[3],b[3])>=max(a[1],b[1]) if touch else min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
 for i,(z,b) in enumerate(boxes):
  for j in range(i):
   if boxes[j][0]==z and overlap(b,boxes[j][1],True):union(i,j)
 contacts=[]
 for v,lo,hi in vias[:count-1]:
  for b in g['rects'][str(v)]:
   ends=[[i for i,(z,a) in enumerate(boxes) if z==zz and overlap(a,b)] for zz in [lo,hi]]
   assert all(ends),(v,b)
   for i in ends[0]:
    for j in ends[1]:union(i,j)
   contacts.append((v,b,ends[0][0]))
 seed=next(i for i,(z,b) in enumerate(boxes) if z==81 and b[0]<=-2000<=b[2] and b[1]<=257290<=b[3]);component=root(seed)
 selected={z:[] for z in [34,36,42,46,81,35,38,40,41]}
 for i,(z,b) in enumerate(boxes):
  if root(i)==component:selected[z].append(b)
 for z,b,i in contacts:
  if root(i)==component:selected[z].append(b)
 assert any(a<=22000<=c and b<=257290<=e for a,b,c,e in selected[81])
 layout=k.Layout();layout.dbu=.001;cell=layout.create_cell('rail');intervals=0
 for z,bs in selected.items():
  reg=k.Region()
  for b in bs:reg.insert(k.Box(*b));cell.shapes(layout.layer(z,0)).insert(k.Box(*b))
  if z in metals:intervals+=len(list((reg.merged()&k.Region(k.Box(9999,-1000000,10001,1000000))).merged().each()))
 layout.write(str(d/'rail.gds'))
 geo={**g,'rects':selected,'ports':[p for p in g['ports'] if p['name'].startswith('VDD_')],'expected_intervals':intervals};(d/'geometry.json').write_text(json.dumps(geo,indent=2)+'\n')
 t=['drc off',f'gds read {d}/rail.gds','load rail','select top cell']
 for idx,(n,x) in enumerate([('VDD_A',-2.1),('VDD_B',21.9)],1):t += [f'box values {x}um 257.09um {x+.01}um 257.49um',f'label {n} center m5',f'port make {idx}']
 t += ['extract do resistance','extresist threshold 0','extresist minres 1','extresist mindelay 0','extresist simplify off','extresist include VDD_B','extract all','extresist all','ext2spice lvs','ext2spice cthresh infinite','ext2spice extresist on','ext2spice subcircuits top on','ext2spice -o rc.spice','quit -noprompt']
 (d/'extract.tcl').write_text('\n'.join(t)+'\n')
 with (d/'magic.log').open('w') as f:subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(d/'extract.tcl')],cwd=d,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
 for step in [.25,.1,.05]:
  out=d/f'mesh-{step}';out.mkdir(exist_ok=True)
  cmd=['python3',str(ROOT/'scripts/compare-filler-stitch.py'),'--geometry-file',str(d/'geometry.json'),'--output-dir',str(out),'--step-um',str(step),'--electrode-model','equipotential','--align-vias','--skip-spice']
  with (out/'driver.log').open('w') as f:subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=180,check=True)
 print(name,'complete', {z:len(b) for z,b in selected.items()},flush=True)
