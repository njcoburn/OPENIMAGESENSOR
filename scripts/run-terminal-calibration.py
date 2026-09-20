"""Bounded terminal-calibration experiments; legacy evidence is kept in separate folders."""
from pathlib import Path
import subprocess,json,argparse,time
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/terminal-calibration';p=argparse.ArgumentParser();p.add_argument('--part',choices=['calibration','filler'],default='calibration');args=p.parse_args()
if args.part=='calibration':
 for mode in ['area','point']:
  folder=out/('magic-'+mode);start=time.monotonic()
  with (folder/'extraction.log').open('w') as log:
   r=subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(folder/'extract.tcl')],cwd=folder,stdout=log,stderr=subprocess.STDOUT,timeout=60,check=True)
  assert 'Error:' not in (folder/'extraction.log').read_text()
  print('Magic',mode,'completed',time.monotonic()-start,flush=True)
 for model in ['legacy','equipotential']:
  for step in [1,.1]:
   folder=out/(model+'-'+str(step));folder.mkdir(exist_ok=True)
   cmd=['python3',str(ROOT/'scripts/compare-filler-stitch.py'),'--geometry-file',str(out/'geometry.json'),'--output-dir',str(folder),'--step-um',str(step),'--electrode-model',model,'--skip-spice']
   with (folder/'driver.log').open('w') as log:subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
   d=json.loads((folder/'result.json').read_text());print(model,step,{r:v['R_ohm'] for r,v in d['monolithic'].items()},flush=True)
else:
 for step in [1,.5,.25]:
  folder=ROOT/'build/filler-stitch'/('electrode-'+str(float(step)));folder.mkdir(exist_ok=True)
  cmd=['python3',str(ROOT/'scripts/compare-filler-stitch.py'),'--step-um',str(step),'--electrode-model','equipotential']
  if step!=1:cmd.append('--skip-spice')
  with (folder/'driver.log').open('w') as log:subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
  d=json.loads((folder/'result.json').read_text());print('Filler',step,{r:v['R_ohm'] for r,v in d['monolithic'].items()},flush=True)
