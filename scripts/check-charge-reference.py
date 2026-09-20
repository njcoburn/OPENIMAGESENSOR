"""Independent ngspice common-mode, differential and basis-vector charge checks."""
from pathlib import Path
import json,shlex,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reference';out={}
for case in ['tee','tee-rotated','long-tee','long-tee-rotated']:
 src=R/'build/capacitance-candidate/controls'/case/'area-fixed';d=B/f'control-{case}';audit=json.loads((d/'audit.json').read_text());sh={};mutual=0
 for s in (src/'coupon.ext').read_text().splitlines():
  if s.startswith('node '):
   t=shlex.split(s);sh[t[1]]=float(t[3])*.001
  elif s.startswith('cap '):mutual+=float(shlex.split(s)[3])*.001
 expected=np.array([[sh['B']+mutual,-mutual],[-mutual,sh['REF']+mutual]])
 net=(d/'reference.spice').read_text().replace(audit['substrate'],'SUB')
 net=re.sub(r'(?m)^(\.subckt coupon .*)$',r'\1 SUB',net);(d/'fixture.spice').write_text(net)
 out[case]={}
 for name,vs,vr in [('common',1,1),('differential',1,-1),('signal_basis',1,0),('plate_basis',0,1)]:
  deck=f'''Charge-reference {case} {name}
.include fixture.spice
Vs signal 0 AC {vs}
Vr plate 0 AC {vr}
Xdut signal signal plate 0 coupon
.control
set numdgt=12
set wr_singlescale
set wr_vecnames
ac lin 1 1meg 1meg
let qs = -imag(i(Vs))/(2*pi*1e6)*1e15
let qr = -imag(i(Vr))/(2*pi*1e6)*1e15
wrdata {name}.dat qs qr
quit
.endc
.end
'''
  (d/f'{name}.spice').write_text(deck);p=subprocess.run(['ngspice','-b',f'{name}.spice'],cwd=d,capture_output=True,text=True,timeout=30);(d/f'{name}.log').write_text(p.stdout+p.stderr)
  assert p.returncode==0
  a=np.ravel(np.loadtxt(d/f'{name}.dat',skiprows=1))[1:];target=expected@np.array([vs,vr]);error=float(np.max(abs(a-target)));assert np.isfinite(a).all() and error<1e-7,(case,name,a,target)
  out[case][name]={'expected_charge_fC':target.tolist(),'ngspice_charge_fC':a.tolist(),'max_error_fC':error,'pass':True}
(B/'ac-checks.json').write_text(json.dumps(out,indent=2)+'\n');print('16 independent AC charge checks pass; max error fC',max(v['max_error_fC'] for d in out.values() for v in d.values()))
