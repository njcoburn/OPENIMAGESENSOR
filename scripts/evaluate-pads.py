"""Functional evaluation of installed GF180 analog pad; not ESD qualification."""
from pathlib import Path
import runpy,re,json,hashlib,subprocess
from concurrent.futures import ThreadPoolExecutor
import numpy as np
root=Path(__file__).resolve().parents[1]; out=root/'build/pad-evaluation';out.mkdir(parents=True,exist_ok=True)
pdk=Path('/foss/pdks/gf180mcuD'); lib=pdk/'libs.tech/ngspice/sm141064.ngspice'
source=pdk/'libs.ref/gf180mcu_fd_io/spice/gf180mcu_fd_io.spice'
checkpoint=root/'checkpoints/pad-evaluation';checkpoint.mkdir(parents=True,exist_ok=True)
s=source.read_text();cell=s[:s.index('.ENDS')+len('.ENDS')]+'\n'
(checkpoint/'analog-pad.spice').write_text(cell)
padfile=checkpoint/'analog-pad.spice'
def header(d,t,v):
 return f'Analog pad functional characterization\n.include {pdk}/libs.tech/ngspice/design.ngspice\n.lib {lib} typical\n.lib {lib} {d}\n.lib {lib} moscap_typical\n.include {padfile}\n.temp {t}\n.options gmin=1e-17 abstol=1e-16 reltol=1e-6\nVdd VDD 0 {v}\n'
def run(folder,deck):
 folder.mkdir(parents=True,exist_ok=True);(folder/'testbench.spice').write_text(deck)
 with (folder/'run.log').open('w') as log:
  p=subprocess.run(['ngspice','-b',str(folder/'testbench.spice')],stdout=log,stderr=subprocess.STDOUT,timeout=120)
 log=(folder/'run.log').read_text()
 if p.returncode or re.search(r'^Error|aborted|timestep too small',log,re.M|re.I):raise RuntimeError(str(folder)+' '+log[-1500:])
 a=np.loadtxt(folder/'wave.txt',skiprows=1,ndmin=2);assert np.isfinite(a).all();return a

def characterize(case):
 d,t,v=case;name=f'{d}_{t}C_{v}V';folder=out/'characterization'/name
 deck=header(d,t,v)+f'Vpin PIN 0 0\nXpad PIN VDD 0 VDD 0 gf180mcu_fd_io__asig_5p0\n.control\nset wr_singlescale\nset wr_vecnames\ndc Vpin 0 {v} .01\nwrdata {folder}/wave.txt i(Vpin)\nquit\n.endc\n.end\n'
 a=run(folder,deck)
 rows={}
 for name2,bias in [('BIAS',.71),('PREF',1.99),('VRESET',2.0),('BUF_low',.4),('BUF_high',2.5)]:
  dest=folder/name2
  deck=header(d,t,v)+f'Vpin PIN 0 {bias} AC 1\nXpad PIN VDD 0 VDD 0 gf180mcu_fd_io__asig_5p0\n.control\nset wr_singlescale\nset wr_vecnames\nac lin 1 1000 1000\nlet cp=-imag(i(Vpin))/(2*pi*1000)\nwrdata {dest}/wave.txt cp\nquit\n.endc\n.end\n'
  cap=run(dest,deck)[0,1]
  rows[name2]={'voltage_V':bias,'leakage_into_pad_A':float(-np.interp(bias,a[:,0],a[:,1])),'capacitance_F':float(cap)}
 return f'{d}_{t}C_{v}V',{'diode':d,'temp_C':t,'supply_V':v,'max_abs_rail_range_leakage_A':float(np.max(abs(a[:,1]))),'pins':rows}

def network(mode):
 lines=[f'.include {padfile}',f'.lib {lib} moscap_typical']
 for pin in ['BIAS','PREF','BUF','VRESET']:
  lines.append(f'Xpad_{pin} {pin}_PIN VDD 0 VDD 0 gf180mcu_fd_io__asig_5p0')
  if mode.startswith('secondary'):
   lines += [f'Rprotect_{pin} {pin}_PIN {pin}_ESD 100',f'Dlo_{pin} 0 {pin}_ESD diode_nd2ps_03v3 area=12p pj=26u',f'Dhi_{pin} {pin}_ESD VDD diode_pd2nw_03v3 area=12p pj=26u',f'Vcore_{pin} {pin}_ESD {pin} 0']
  else:lines.append(f'Vcore_{pin} {pin}_PIN {pin} 0')
 return '\n'.join(lines)+'\n'
def engine(mode):
 env=runpy.run_path(str(root/'scripts/bias-reference.py'));g=env['scan'].__globals__;orig=g['base'];original_ng=g['ng']
 def base(*args,**kw):
  s,delay=orig(*args,**kw)
  s=s.replace('Xbias VDD 0 BIAS PREF','Xbias VDD 0 BIAS_PIN PREF_PIN')
  s=re.sub(r'(?m)^Vreset VRESET ', 'Vreset VRESET_PIN ',s)
  s=s.replace('Rbond BUF BOND','Rbond BUF_PIN BOND')
  # Keep a separate 1pF external trace/package allowance; modeled pad is additional.
  s=s.replace('Cpad PAD 0 5p','Cpad PAD 0 1p')
  if mode.endswith('-smooth'):
   # Finite conductance transition over the existing 10ns ADC control edges.
   s=s.replace('Ssample ADCIN HOLD ACQ 0 sample_switch', 'Bsample ADCIN HOLD I=V(ADCIN,HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(ACQ)-1.65)/0.1)))')
   s=s.replace('Sreset HOLD 0 RSTADC 0 sample_switch', 'Breset HOLD 0 I=V(HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(RSTADC)-1.65)/0.1)))')
  return s+network(mode),delay
 def ng(folder,s):
  # Current estimates from board resistors require their external pin voltages.
  s=s.replace('v(BIAS) v(PREF) v(VDD)','v(BIAS_PIN) v(PREF_PIN) v(VDD)')
  return original_ng(folder,s)
 g['base']=base;g['ng']=ng;g['out']=out/mode;g['fingerprint']+=hashlib.sha256((cell+network(mode)).encode()).hexdigest()
 return g
if __name__=='__main__':
 import sys
 mode=sys.argv[1] if len(sys.argv)>1 else 'characterize'
 if mode=='characterize':
  cases=[(d,t,v) for d in ['diode_typical','diode_ff','diode_ss'] for t in [-40,27,85,125] for v in [3,3.3,3.6]]
  rows=dict(ThreadPoolExecutor(max_workers=4).map(characterize,cases))
  result={'scope':'Isolated installed pad model with ideal 3.0-3.6V rails; no ESD qualification. Capacitance is AC differential signal capacitance at 1kHz, ideal AC-grounded rails. Representative pin voltages; full rail-range leakage curves also saved. MOS capacitor section fixed typical.','cases':rows,'pad_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pad_cell_sha256':hashlib.sha256(cell.encode()).hexdigest()}
  (root/'simulations/pad-characterization.json').write_text(json.dumps(result,indent=2)+'\n')
  print('Characterized',len(rows),'cases; max leakage nA',max(r['max_abs_rail_range_leakage_A'] for r in rows.values())*1e9)
 elif mode=='dc':
  reference=json.loads((root/'simulations/bias-reference-dc.json').read_text())['cases']
  results={}
  for variant in ['pad-only','secondary']:
   g=engine(variant)
   def dc(item):
    key,r=item;c,t,v,d,rc,rb=[r[k] for k in ['corner','temp_C','supply_V','diode','rcol_scale','rbuf_scale']]
    dest=out/variant/'dc-evaluation'/key
    s,_=g['base'](c,t,v,d,rc,rb,1)
    a=g['ng'](dest,s+g['control'](dest,'op','v(BIAS) v(PREF) v(BIAS_PIN) v(PREF_PIN) i(Vcore_BIAS) i(Vcore_PREF) i(Vcore_VRESET)'))[0]
    ib=a[5]*1e6;ip=-a[6]*1e6
    return key,dict(corner=c,temp_C=t,supply_V=v,diode=d,rcol_scale=rc,rbuf_scale=rb,column_core_uA=float(ib),buffer_core_uA=float(ip),column_change_percent=float(100*(ib/r['column_reference_uA']-1)),buffer_change_percent=float(100*(ip/r['buffer_reference_uA']-1)),bias_pin_V=float(a[3]),pref_pin_V=float(a[4]),bias_core_V=float(a[1]),pref_core_V=float(a[2]),bias_total_leakage_nA=float(((v-a[3])/(5.1e6*rc)-a[5])*1e9),pref_total_leakage_nA=float((-a[6]-a[4]/(49900*rb))*1e9),vreset_drop_mV=float(100*a[7]*1000) if variant=='secondary' else 0)
   results[variant]=dict(ThreadPoolExecutor(max_workers=4).map(dc,reference.items()))
   print(variant,'DC complete',len(results[variant]),flush=True)
   (root/'simulations/pad-dc.json').write_text(json.dumps({'cases':results,'scope':'Matched comparison with the 84 original resistor-bias DC cases. Core reference current measured after protection, excluding pad and secondary-diode leakage.'},indent=2)+'\n')
 else:
  g=engine(mode)
  tasks=[('typical',27,3.3,'diode_typical'),('typical',125,3.0,'diode_ff'),('ss',-40,3.0,'diode_ss'),('ff',125,3.6,'diode_ff'),('fs',125,3.0,'diode_typical')]
  rows={}
  def imaging(task):
   c,t,v,d=task
   return g['scan'](c,t,v,d,cext=1)
  for name,r in ThreadPoolExecutor(max_workers=3).map(imaging,tasks):
   rows[name]=r
   (root/f'simulations/pad-{mode}.json').write_text(json.dumps({'scope':mode+' functional candidate; four pads on common 3.3V-domain rails. 1pF residual external capacitance. Secondary uses ideal 100ohm resistors and 12um2/26um perimeter diode pairs, not a qualified ESD layout.','cases':rows},indent=2)+'\n')
