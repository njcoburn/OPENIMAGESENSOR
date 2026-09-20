"""Use the previously audited charge-neutral fill elimination for reader-patch transients."""
from pathlib import Path
from collections import Counter
import json,hashlib,subprocess,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/network-investigation/device-export'
original=ROOT/'build/buffer-pex/buffer_rc.spice';reduction=json.loads((ROOT/'build/buffer-pex/reduction.json').read_text())
assert hashlib.sha256(original.read_bytes()).hexdigest()==reduction['raw_netlist_sha256']
def canon(line):
 t=line.split()
 if not t or t[0].startswith('*'):return None
 if t[0].startswith('C'):return ('C',*sorted(t[1:3]),*t[3:])
 return tuple(t)
baseline=(base/'buffer/baseline.spice').read_text().splitlines();old=original.read_text().splitlines()
assert Counter(canon(s) for s in baseline)==Counter(canon(s) for s in old)
results={'scope':'Nominal 6us buffer and two-instance hierarchy transients using the existing verified Schur capacitance reduction, with charge-neutral floating fill. No artificial shunt added. Full raw-network attempts retained separately.','reduction':reduction,'cases':{}}
for mode in ['baseline','patched']:
 raw=(base/'buffer'/(mode+'.spice')).read_text().splitlines();rv={s.split()[0]:s.split()[3] for s in raw if s.startswith('R')}
 text=(ROOT/'build/buffer-pex/buffer_reduced.spice').read_text().replace('buffer_pex','rc_buffer')
 lines=[]
 for line in text.splitlines():
  if line.startswith('R'):
   t=line.split();assert t[0] in rv;t[3]=rv[t[0]];line=' '.join(t)
  lines.append(line)
 for case in ['buffer','hierarchy']:
  d=base/(case+'-reduced');d.mkdir(exist_ok=True);net='\n'.join(lines)+'\n'
  if case=='hierarchy':net+=(base/'hierarchy'/(mode+'.spice')).read_text().split('.subckt pair',1)[1].join(['.subckt pair',''])
  (d/(mode+'.spice')).write_text(net)
  circuit=f'''Buffer reader-patch regression with verified fill elimination
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice diode_typical
.include {d}/{mode}.spice
.options reltol=1e-6 abstol=1e-14 method=gear
VDD vdd 0 3.3
VIN vin 0 PWL(0 0.7 2u 0.7 2.1u 0.9 6u 0.9)
IREF pref 0 40u
CLOAD buf 0 100p
'''
  if case=='buffer':circuit+='XDUT 0 vdd pref vin buf rc_buffer\n'
  else:circuit+='XDUT 0 vdd pref vin buf pref2 vin2 buf2 pair\nVIN2 vin2 0 0.8\nIREF2 pref2 0 40u\nCLOAD2 buf2 0 100p\n'
  circuit+=f'.control\nset numdgt=12\nset wr_singlescale\nset wr_vecnames\ntran 0.01u 6u\nwrdata {d}/{mode}-wave.txt v(buf) v(pref)\nquit\n.endc\n.end\n'
  (d/(mode+'.cir')).write_text(circuit)
  with (d/(mode+'.log')).open('w') as log:p=subprocess.run(['ngspice','-b',str(d/(mode+'.cir'))],stdout=log,stderr=subprocess.STDOUT,timeout=45)
  log=(d/(mode+'.log')).read_text();assert p.returncode==0 and not re.search('timestep too small|simulation aborted|^Error',log,re.I|re.M)
  wave=np.loadtxt(d/(mode+'-wave.txt'),skiprows=1);assert np.isfinite(wave).all() and wave[-1,0]>=6e-6
  assert .7<wave[-1,1]<3.3 and wave[-1,1]>wave[0,1]
  results['cases'].setdefault(case,{})[mode]={'final_buffer_V':float(wave[-1,1]),'points':len(wave),'pass':True}
for case in ['buffer','hierarchy']:
 d=base/(case+'-reduced');a=np.loadtxt(d/'baseline-wave.txt',skiprows=1);b=np.loadtxt(d/'patched-wave.txt',skiprows=1)
 difference=float(max(abs(a[:,1]-np.interp(a[:,0],b[:,0],b[:,1]))));assert difference<1e-4
 results['cases'][case]['max_buffer_difference_V']=difference
(base/'reduced-regression.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
