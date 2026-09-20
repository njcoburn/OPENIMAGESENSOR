"""Matched diagnostic ring extraction without altering production geometry."""
from pathlib import Path
import json,subprocess,time,hashlib,shutil,argparse
R=Path(__file__).resolve().parents[1];B=R/'build/ring-candidate'
parser=argparse.ArgumentParser();parser.add_argument('--area-fixed',action='store_true');args=parser.parse_args()
variants=[('area-fixed','build/capacitance-candidate/magic-area-fixed')] if args.area_fixed else [('baseline','build/magic-export-diagnostic/bin/magic'),('combined','build/combined-patch/magic-combined')]
for variant,exe in variants:
 for case in ['fill10','corner']:
  d=B/variant/case;d.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(R/'build/ring-sections'/case/'geometry.json',d/'geometry.json')
  for mode in ['full','metal']:
   folder=d/mode;folder.mkdir(exist_ok=True);src=R/'build/ring-sections'/case
   commands='scalegrid 1 10\ntech load /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech\n'+(src/mode/'extract.tcl').read_text().replace('ext2spice -o rc.spice','ext2spice -o rc.spice coupon')
   (folder/'commands.txt').write_text(commands);(folder/'rc.spice').unlink(missing_ok=True);start=time.monotonic()
   with (folder/'extraction.log').open('w') as log:
    try:
     p=subprocess.run([str(R/exe),'-dnull','-rcfile','/dev/null'],cwd=folder,input=''.join(':'+s+'\n' for s in commands.splitlines()),text=True,stdout=log,stderr=subprocess.STDOUT,timeout=180)
     status='exported_unvalidated' if p.returncode==0 and (folder/'rc.spice').exists() else 'failed'
    except subprocess.TimeoutExpired:status='timeout'
   data={'status':status,'elapsed_s':time.monotonic()-start,'mode':mode,'binary_sha256':hashlib.sha256((R/exe).read_bytes()).hexdigest(),'gds_sha256':hashlib.sha256((src/f'{mode}.gds').read_bytes()).hexdigest()}
   (folder/'status.json').write_text(json.dumps(data,indent=2)+'\n');print(variant,case,mode,data,flush=True)
   assert status=='exported_unvalidated'
