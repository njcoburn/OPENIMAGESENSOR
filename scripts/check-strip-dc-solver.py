"""Independent sparse-solver cross-check of completed strip DC references."""
from pathlib import Path
import hashlib,json,os,runpy,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1];source=R/'build/array-strip-imaging-matched-20260924/r64c1-rc-port';out=R/'build/array-strip-dc-solver-20260924';out.mkdir(exist_ok=False)
read=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw'];results=[]
(out/'runner.py').write_bytes(Path(__file__).read_bytes())
for i in [0,20,40]:
 src=source/f'dc-{i:03d}';d=out/f'dc-{i:03d}';d.mkdir();original=(src/'test.spice').read_text();assert original.count('set klu\n')==1;deck=original.replace('set klu\n','unset klu\n');(d/'test.spice').write_text(deck)
 t=time.monotonic()
 with (d/'ngspice.log').open('w') as f:
  p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'SPICE_USERINIT_DIR':str(source.parent/'init')},timeout=120)
 log=(d/'ngspice.log').read_text();assert p.returncode==0 and 'aborted' not in log.lower() and 'No. of Data Rows : 1' in log
 n,a=read(src/'op.raw');m,b=read(d/'op.raw');assert n==m and a.shape==b.shape and np.isfinite(b).all();err=max(abs(a[0,j]-b[0,j]) for j,name in enumerate(n) if name.startswith('v('));assert err<1e-6,err
 result={'sample':i,'seconds':time.monotonic()-t,'max_voltage_difference_V':float(err),'source_sha256':hashlib.sha256(original.encode()).hexdigest(),'deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),'transient_op_fallback':'Transient op started' in log};results.append(result);print(result,flush=True);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
