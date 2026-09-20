"""Broaden the reader patch to an actual extracted buffer and a two-instance fixture."""
from pathlib import Path
import subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/network-investigation/device-export';base.mkdir(parents=True,exist_ok=True)
for case in ['buffer','hierarchy']:
 d=base/case;d.mkdir(exist_ok=True)
 for name in ['rc_buffer.ext','rc_buffer.res.ext']:shutil.copyfile(ROOT/'build/buffer-pex'/name,d/name)
 top='rc_buffer'
 if case=='hierarchy':
  top='pair';header=(d/'rc_buffer.ext').read_text().splitlines()[:6]
  lines=header+['use rc_buffer U0 1 0 0 0 1 0','use rc_buffer U1 1 0 60000 0 1 0']
  pins=['GND','VDD','A_PREF','A_IN','A_BUF','B_PREF','B_IN','B_BUF']
  for i,n in enumerate(pins,1):
   lines += [f'port "{n}" {i} 0 {i*100} 0 {i*100} m2',f'node "{n}" 0 0 0 {i*100} m2'+' 0 0'*26]
  for inst,prefix in [('U0','A'),('U1','B')]:
   for pin in ['GND','VDD','PREF','IN','BUF']:lines.append(f'equiv "{pin if pin in ["GND","VDD"] else prefix+"_"+pin}" "{inst}/{pin}"')
  (d/'pair.ext').write_text('\n'.join(lines)+'\n')
 for mode in ['baseline','patched']:
  exe=ROOT/('build/magic-export-diagnostic/bin/magic' if mode=='baseline' else 'build/extraction-diagnostics/magic-patched')
  script=['scalegrid 1 10','tech load /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech','ext2spice lvs','ext2spice cthresh 0','ext2spice extresist on','ext2spice subcircuits top on','ext2spice hierarchy on',f'ext2spice -o {mode}.spice {top}','quit -noprompt']
  commands=''.join(':'+s+'\n' for s in script);(d/(mode+'.commands')).write_text(commands)
  p=subprocess.run([str(exe),'-dnull','-rcfile','/dev/null'],input=commands,text=True,cwd=d,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
  (d/(mode+'.log')).write_text(p.stdout);assert p.returncode==0,p.stdout[-1000:]
  assert (d/(mode+'.spice')).exists()
 print(case,'exported',flush=True)
