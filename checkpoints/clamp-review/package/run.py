"""Replay one case, preserving the archived evidence. Requires ngspice and GF180 PDK."""
from pathlib import Path
import argparse,subprocess,os,re,shutil,json
p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('--timeout',type=int,default=120);a=p.parse_args()
r=Path(__file__).resolve().parent
assert a.case in [x.name for x in (r/'cases').iterdir() if x.is_dir()]
d=r/'replay'/a.case;d.mkdir(parents=True,exist_ok=True)
shutil.copy2(r/'cases'/a.case/'test.spice',d/'test.spice');(d/'tran.dat').unlink(missing_ok=True)
result={'completed':False}
try:
 with (d/'ngspice.log').open('w') as log:
  proc=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout,env={**os.environ,'SPICE_USERINIT_DIR':str(r/'init')})
 text=(d/'ngspice.log').read_text()
 assert proc.returncode==0 and not re.search('aborted|timestep too small|^Error',text,re.I|re.M)
 lines=(d/'tran.dat').read_text().splitlines()[1:]
 assert len(lines)>1 and float(lines[-1].split()[0])>=152.99e-6
 result['completed']=True
except Exception as e:result['failure']=str(e)
(d/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
raise SystemExit(0 if result['completed'] else 1)
