"""Matched finite-switch controls and finer-step checks for pad evaluation."""
from pathlib import Path
import runpy,json
from concurrent.futures import ThreadPoolExecutor
root=Path(__file__).resolve().parents[1]
engine=runpy.run_path(str(root/'scripts/evaluate-pads.py'))['engine']
def task(t):
 mode,c,temp,v,d,step=t;g=engine(mode)
 name,r=g['scan'](c,temp,v,d,cext=1,step=step)
 return mode+'/'+name,r
tasks=[('pad-only-smooth','typical',27,3.3,'diode_typical',.1),('pad-only-smooth','typical',125,3.0,'diode_ff',.1),('secondary-smooth','typical',125,3.0,'diode_ff',.05)]
rows={}
for name,r in ThreadPoolExecutor(max_workers=3).map(task,tasks):
 rows[name]=r
 (root/'simulations/pad-refinements.json').write_text(json.dumps({'cases':rows},indent=2)+'\n')
