"""Refine the isolated M5 transition; rerun Magic with accepted threshold syntax."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/rail-isolation'
for d in sorted(base.glob('m5-to-m*')):
 p=d/'extract.tcl';s=p.read_text().replace('extresist threshold -1','extresist threshold 0')
 if 'extresist all\n' not in s:s=s.replace('extract all\n','extract all\nextresist all\n')
 p.write_text(s)
 with (d/'magic.log').open('w') as f:subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(p)],cwd=d,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
 assert 'Usage:' not in (d/'magic.log').read_text()
if '--magic-only' in sys.argv:raise SystemExit(0)
d=base/'m5-to-m5'
for step in [.025,.0125]:
 out=d/f'mesh-{step}';out.mkdir(exist_ok=True)
 with (out/'driver.log').open('w') as f:subprocess.run(['python3',str(ROOT/'scripts/compare-filler-stitch.py'),'--geometry-file',str(d/'geometry.json'),'--output-dir',str(out),'--step-um',str(step),'--electrode-model','equipotential','--align-vias','--skip-spice'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
 print('M5 refined',step,flush=True)
