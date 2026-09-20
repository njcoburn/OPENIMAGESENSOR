"""Compare normal and bypassed construction reductions in a diagnostic executable."""
from pathlib import Path
import subprocess,os,sys
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/network-investigation';fixed='--fixed' in sys.argv;exe=base/('magic-reduction-fixed' if fixed else 'magic-trace')
for case in ['two_end_columns','all_cuts']:
 src=ROOT/'build/extraction-diagnostics'/case
 for mode in (['fixed'] if fixed else ['normal','unreduced']):
  d=base/(case+'-'+mode);d.mkdir(exist_ok=True)
  commands='scalegrid 1 10\ntech load /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech\n'+(src/'extract.tcl').read_text().replace('ext2spice -o rc.spice','ext2spice -o rc.spice rail')
  (d/'commands.txt').write_text(commands)
  env=os.environ.copy()
  if mode=='unreduced':env['OIS_NO_REDUCE']='1'
  else:env.pop('OIS_NO_REDUCE',None)
  p=subprocess.run([str(exe),'-dnull','-rcfile','/dev/null'],input=''.join(':'+s+'\n' for s in commands.splitlines()),text=True,cwd=d,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
  (d/'trace.log').write_text(p.stdout);assert p.returncode==0,p.stdout[-1000:]
  assert (d/'rail.res.ext').exists()
  print(case,mode,'edges',sum(s.startswith('resist ') for s in (d/'rail.res.ext').read_text().splitlines()),flush=True)
