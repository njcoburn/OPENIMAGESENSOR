"""Independent common-mode charge accounting for small two-layer controls."""
from pathlib import Path
import shlex,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/capacitance-candidate';results={}
def value(s):
 m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([a-z]*)',s,re.I)
 return float(m[1])*{'':1e15,'f':1,'p':1e3,'n':1e6}[m[2]]
for case in ['tee','tee-rotated','long-tee','long-tee-rotated']:
 results[case]={}
 for variant in ['combined','area-fixed']:
  d=B/'controls'/case/variant;ext=(d/'coupon.ext').read_text();net=(d/'rc.spice').read_text()
  shunts={};coupling=[];substrate=None
  for s in ext.splitlines():
   if s.startswith('node '):
    t=shlex.split(s);shunts[t[1]]=float(t[3])*.001
   elif s.startswith('substrate '):substrate=shlex.split(s)[1]
   elif s.startswith('cap '):
    t=shlex.split(s);coupling.append((t[1],t[2],float(t[3])*.001))
  assert substrate
  expected=sum(shunts.values());actual=0;neg=0
  for s in net.splitlines():
   if s.startswith('C'):
    t=s.split();c=value(t[3]);neg+=c<0
    if substrate in t[1:3]:actual+=c
  # All signal electrodes are driven together; coupling should carry zero charge.
  # Expose and ground the otherwise implicit substrate in this test fixture only.
  fixture=net.replace(substrate,'SUB')
  fixture=re.sub(r'(?m)^(\.subckt coupon .*)$',r'\1 SUB',fixture)
  (d/'fixture.spice').write_text(fixture)
  deck='''Common-mode capacitance accounting
.include fixture.spice
Vdrive drive 0 AC 1
Xdut drive drive drive 0 coupon
.control
set numdgt=12
set wr_singlescale
set wr_vecnames
ac lin 1 1meg 1meg
let ceff = -imag(i(Vdrive))/(2*pi*1e6)*1e15
wrdata common-mode.dat ceff
quit
.endc
.end
'''
  (d/'accounting.spice').write_text(deck)
  p=subprocess.run(['ngspice','-b','accounting.spice'],cwd=d,text=True,capture_output=True,timeout=20)
  (d/'accounting.log').write_text(p.stdout+p.stderr);assert p.returncode==0
  a=np.loadtxt(d/'common-mode.dat',skiprows=1);measured=float(np.ravel(a)[1]);assert abs(measured-actual)<1e-7
  results[case][variant]={'original_shunt_sum_fF':expected,'incident_coupling_sum_fF':sum(c for a,b,c in coupling),'exported_common_mode_fF':actual,'ngspice_common_mode_fF':measured,'excess_fF':actual-expected,'negative_exported_caps':neg,'charge_conserving':abs(actual-expected)<1e-4}
(B/'accounting.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
