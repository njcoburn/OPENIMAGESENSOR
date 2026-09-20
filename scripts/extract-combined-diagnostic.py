"""Fresh extraction of verified buffer/readout GDS with matched baseline and candidate."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/combined-patch'
for block,cell,gds in [('buffer','output_buffer','checkpoints/output-buffer/output_buffer.gds'),('readout','column_readout','checkpoints/readout/column_readout.gds')]:
 for mode in ['baseline','combined']:
  d=base/block/mode;d.mkdir(parents=True,exist_ok=True)
  exe=ROOT/('build/magic-export-diagnostic/bin/magic' if mode=='baseline' else 'build/combined-patch/magic-combined')
  commands=['scalegrid 1 10','tech load /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech','drc off',f'gds read {ROOT/gds}',f'load {cell}','select top cell',f'flatten rc_{block}',f'load rc_{block}','select top cell','extract do capacitance','extract do coupling','extract do resistance','extresist threshold 1000','extresist minres 100','extresist mindelay 0','extract all','ext2spice lvs','ext2spice cthresh 0','ext2spice extresist on','ext2spice subcircuits top on',f'ext2spice -o {block}_rc.spice rc_{block}','quit -noprompt']
  script=''.join(':'+s+'\n' for s in commands);(d/'commands.txt').write_text(script)
  with (d/'extract.log').open('w') as log:p=subprocess.run([str(exe),'-dnull','-rcfile','/dev/null'],input=script,text=True,cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  assert p.returncode==0 and (d/f'{block}_rc.spice').exists()
  (d/'inputs.json').write_text(json.dumps({'gds':gds,'gds_sha256':hashlib.sha256((ROOT/gds).read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'fresh_extraction':True},indent=2)+'\n')
  print(block,mode,'extracted',flush=True)
