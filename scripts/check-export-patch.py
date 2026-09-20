"""Re-export fixed existing .ext data through an isolated patched Magic executable."""
from pathlib import Path
import subprocess,shutil,sys
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/extraction-diagnostics/export-check';out.mkdir(exist_ok=True)
mode='baseline' if '--baseline' in sys.argv else 'patched'
exe=ROOT/('build/magic-export-diagnostic/bin/magic' if mode=='baseline' else 'build/extraction-diagnostics/magic-patched')
for src in sorted((ROOT/'build/rail-faces').glob('m5-to-m*')):
 d=out/src.name;d.mkdir(exist_ok=True)
 for name in ['rail.ext','rail.res.ext']:shutil.copyfile(src/name,d/name)
 script='\n'.join(['tech load /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech','ext2spice lvs','ext2spice cthresh infinite','ext2spice extresist on','ext2spice subcircuits top on',f'ext2spice -o {mode}.spice rail','quit -noprompt'])+'\n'
 (d/(mode+'.commands')).write_text(script)
 p=subprocess.run([str(exe),'-dnull','-rcfile','/dev/null'],input=''.join(':'+line+'\n' for line in script.splitlines()),text=True,cwd=d,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (d/(mode+'.log')).write_text(p.stdout);print(src.name,p.returncode,(d/(mode+'.spice')).exists(),flush=True)
 if p.returncode or not (d/(mode+'.spice')).exists():raise RuntimeError(p.stdout)
