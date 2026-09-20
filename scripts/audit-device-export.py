"""Preserve devices, capacitances and hierarchy; exercise nominal full-RC transients."""
from pathlib import Path
import json,subprocess,re,math
from collections import Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/network-investigation/device-export';results={}
for case in ['buffer','hierarchy']:
 d=base/case;a=(d/'baseline.spice').read_text().splitlines();b=(d/'patched.spice').read_text().splitlines()
 assert len(a)==len(b)
 def canonical(s):
  t=s.split()
  if t and t[0].startswith('C'):return ('C',*sorted(t[1:3]),*t[3:])
  return tuple(t)
 assert Counter(canonical(s) for s in a if not s.startswith('R'))==Counter(canonical(s) for s in b if not s.startswith('R'))
 resistors=[(x.split(),y.split()) for x,y in zip(a,b) if x.startswith('R')]
 for x,y in resistors:
  assert x[:3]==y[:3];assert abs(float(x[3])-float(y[3])-.0005)<=10**(math.floor(math.log10(max(float(x[3]),float(y[3]))))-5)+1e-9 # six significant digits in export
 counts={c:sum(s.startswith(c) for s in a) for c in ['R','C','X','.subckt']}
 assert counts['C']>0 and counts['R']>0 and counts['X']>=3
 results[case]={'counts':counts,'nonresistor_records_identical_ignoring_cap_names_and_order':True,'same_resistor_nodes':True,'simulations':{}}
 for mode in ['baseline','patched']:
  circuit=f'''Buffer patch regression
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice diode_typical
.include {d}/{mode}.spice
.options rshunt=1e12 reltol=1e-5 abstol=1e-13 method=gear
VDD vdd 0 3.3
VIN vin 0 PWL(0 0.7 2u 0.7 2.1u 0.9 6u 0.9)
IREF pref 0 40u
CLOAD buf 0 100p
'''
  if case=='buffer':circuit+='XDUT 0 vdd pref vin buf rc_buffer\n'
  else:circuit+='XDUT 0 vdd pref vin buf pref2 vin2 buf2 pair\nVIN2 vin2 0 0.8\nIREF2 pref2 0 40u\nCLOAD2 buf2 0 100p\n'
  circuit+=f'.control\nset numdgt=12\nset wr_singlescale\nset wr_vecnames\ntran 0.05u 6u\nwrdata {d}/{mode}-wave.txt v(buf) v(pref)\nquit\n.endc\n.end\n'
  deck=d/(mode+'.cir');deck.write_text(circuit)
  try:
   with (d/(mode+'.ngspice.log')).open('w') as log:p=subprocess.run(['ngspice','-b',str(deck)],stdout=log,stderr=subprocess.STDOUT,timeout=90)
   log=(d/(mode+'.ngspice.log')).read_text();assert p.returncode==0 and not re.search('timestep too small|simulation aborted|^Error',log,re.I|re.M)
   wave=np.loadtxt(d/(mode+'-wave.txt'),skiprows=1);assert np.isfinite(wave).all() and wave[-1,0]>=6e-6
   results[case]['simulations'][mode]={'status':'complete','final_buffer_V':float(wave[-1,1]),'points':len(wave)}
  except (subprocess.TimeoutExpired,AssertionError,OSError) as e:
   results[case]['simulations'][mode]={'status':'failed_or_timeout','detail':str(e)}
  print(case,mode,results[case]['simulations'][mode],flush=True)
 if all(v['status']=='complete' for v in results[case]['simulations'].values()):
  wa=np.loadtxt(d/'baseline-wave.txt',skiprows=1);wb=np.loadtxt(d/'patched-wave.txt',skiprows=1)
  results[case]['max_buffer_difference_V']=float(max(abs(wa[:,1]-np.interp(wa[:,0],wb[:,0],wb[:,1]))))
results['scope']='Nominal 27C, 3.3V, 40uA reference, 0.7-to-0.9V input and 100pF load, 6us full-RC transient. 1e12-ohm rshunt stabilizes floating extracted fill nodes; this numerical loading is a test condition, not a production model change.'
(base/'regression.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
