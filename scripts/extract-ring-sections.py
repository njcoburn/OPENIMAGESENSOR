"""Bounded per-coupon Magic extraction; timeout output is never a passing model."""
from pathlib import Path
import argparse,json,subprocess,time,re
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['full','metal'],default='full');p.add_argument('--timeout',type=int,default=180);p.add_argument('--cases',nargs='+',default=['fill10','fill20','corner','corner_fill']);a=p.parse_args()
for name in a.cases:
 folder=ROOT/'build/ring-sections'/name/a.mode;start=time.monotonic()
 # Remove stale candidate exports before a fresh invocation.
 for f in ['rc.spice','devices.spice']:(folder/f).unlink(missing_ok=True)
 with (folder/'extraction.log').open('w') as log:
  try:
   r=subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc',str(folder/'extract.tcl')],cwd=folder,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout)
   status='exported_unvalidated' if r.returncode==0 and (folder/'rc.spice').exists() else 'failed'
  except subprocess.TimeoutExpired:status='timeout'
 logtext=(folder/'extraction.log').read_text()
 if re.search(r'^Error:',logtext,re.M):status='export_error'
 data={'status':status,'elapsed_s':time.monotonic()-start,'timeout_s':a.timeout,'mode':a.mode}
 (folder/'status.json').write_text(json.dumps(data,indent=2)+'\n');print(name,data,flush=True)
