"""Retain controlled tests of Magic selection of sub-ohm passive strips."""
from pathlib import Path
import subprocess,time,json
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/terminal-calibration'
s=(base/'magic-area/extract.tcl').read_text()
for name in ['all','negative-threshold','include','canonical-negative']:
 d=base/('magic-'+name);d.mkdir(exist_ok=True);t=s
 if name=='canonical-negative':
  t=t.replace('extresist threshold 0','extresist threshold -1').replace('extract all\n',''.join('extresist include '+n+'_B\n' for n in ['thin10','thin20','wide10','wide20'])+'extract all\n')
 elif name=='all':t=t.replace('extract all\n','extract all\nextresist all\n')
 elif name=='negative-threshold':t=t.replace('extresist threshold 0','extresist threshold -1')
 else:t=t.replace('extract all\n','extresist include wide10_B\nextresist include wide20_B\nextract all\n')
 (d/'extract.tcl').write_text(t);start=time.monotonic()
 with (d/'extraction.log').open('w') as log:
  p=subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(d/'extract.tcl')],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=60)
 (d/'status.json').write_text(json.dumps({'returncode':p.returncode,'elapsed_s':time.monotonic()-start,'status':'exported_unvalidated'},indent=2)+'\n')
 print(name,[line for line in (d/'rc.spice').read_text().splitlines() if line.startswith('R')],flush=True)
