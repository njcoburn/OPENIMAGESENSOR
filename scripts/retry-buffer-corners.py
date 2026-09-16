"""Retry incomplete cases with smaller steps and documented solver settings."""
from pathlib import Path
import runpy,json,sys
root=Path(__file__).resolve().parents[1];early='--early' in sys.argv;trap='--trap' in sys.argv;op='--op' in sys.argv;gmin='--gmin' in sys.argv
p=root/('build/buffer-retries.json' if early else 'simulations/buffer-corners.json')
data={'cases':{f.parent.name:json.loads(f.read_text()) for f in (root/'build/buffer-corners').glob('*/result.json')}} if early else json.loads(p.read_text())
for name,old in list(data['cases'].items()):
 if old['status']=='complete':continue
 m=runpy.run_path(str(root/'scripts/buffer-corners.py'));worker=m['worker'];g=worker.__globals__
 # Keep failed-case evidence in a separate run directory.
 g['out']=root/('build/buffer-corners/retries-gmin' if gmin else 'build/buffer-corners/retries-op' if op else ('build/buffer-corners/retries-trap' if trap else 'build/buffer-corners/retries'));g['out'].mkdir(exist_ok=True)
 original=g['runpy'].run_path
 # Each worker loads output-buffer.py into its own globals. Patch only its ng wrapper
 # through the base template, keeping corner, temperature and physical sources fixed.
 import types
 def load(path):
  module=original(path)
  run=module['run'];env=run.__globals__
  env['base']=env['base'].replace('tran 0.2u','tran 0.1u').replace('chgtol=1e-16','chgtol=1e-15').replace('method=gear','method=trap itl4=200 bypass=0' if trap else 'method=gear itl4=200')
  if gmin:env['base']=env['base'].replace('gmin=1e-17','gmin=1e-14')
  if op:env['base']=env['base'].replace('9.05m uic','9.05m')
  return module
 g['runpy']=types.SimpleNamespace(run_path=load)
 _,result=worker((old['corner'],old['temperature_C'],old['diode_corner']))
 result['retry_settings']=('gmin=1e-14; ' if gmin else '')+('operating-point initialization; ' if op else '')+('trap, bypass=0; ' if trap else 'gear; ')+'0.1us transient step, chgtol=1e-15, itl4=200; original failed deck/log retained.'
 data['cases'][name]=result
p.write_text(json.dumps(data,indent=2)+'\n')
if not early:runpy.run_path(str(root/'scripts/buffer-corners.py'))['plot_results'](data['cases'])
assert all(r['status']=='complete' for r in data['cases'].values()),'Some cases remain incomplete'
