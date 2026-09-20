"""Remove only vias identified as dangling by the preceding native DRC report.
Re-run check_kicad.py immediately afterwards; this is not a DRC waiver.
"""
from pathlib import Path
import re
import pcbnew as p
R=Path(__file__).resolve().parent
for name in ['tester_dock','die_carrier']:
 path=R/'kicad'/name/(name+'.kicad_pcb');b=p.LoadBoard(str(path))
 txt=(R/'reports'/(name+'-drc.txt')).read_text()
 coords=set()
 for block in txt.split('\n['):
  if not block.startswith('via_dangling]'):continue
  m=re.search(r'@\(([\d.]+) mm, ([\d.]+) mm\)',block)
  assert m;coords.add(tuple(round(float(v),4) for v in m.groups()))
 remove=[]
 for t in b.GetTracks():
  if t.GetClass()=='PCB_VIA' and (round(p.ToMM(t.GetPosition().x),4),round(p.ToMM(t.GetPosition().y),4)) in coords:remove.append(t)
 assert len(remove)==len(coords)
 # Move the one carrier legend clear of contact references.
 for t in b.GetDrawings():
  if name=='die_carrier' and t.GetClass()=='PCB_TEXT' and t.GetText().startswith('REV A'):t.SetPosition(p.VECTOR2I(p.FromMM(50),p.FromMM(60.5)))
 for t in remove:b.DeleteNative(t)
 p.SaveBoard(str(path),b)
 print(name,'removed',len(remove),'unused vias')
