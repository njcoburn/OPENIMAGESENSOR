"""Check the physical local protection devices and extracted capacitance."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import runpy,json,hashlib,re
root=Path(__file__).resolve().parents[1];e=runpy.run_path(str(root/'scripts/evaluate-pads.py'));p=root/'build/pad-layout/secondary_pex.spice';out=root/'build/pad-layout-sim';out.mkdir(exist_ok=True)
def engine(res):
 g=e['engine']('secondary-smooth');base=g['base'];g['out']=out/res;g['fingerprint']+=hashlib.sha256(p.read_bytes()).hexdigest()+res
 def physical(*args,**kw):
  s,delay=base(*args,**kw)
  for pin in ['BIAS','PREF','BUF','VRESET']:
   s=re.sub(r'(?m)^Rprotect_'+pin+r' .*$',f'Xprotect_{pin} {pin}_PIN {pin}_ESD VDD 0 secondary_pex',s)
   s=re.sub(r'(?m)^D(?:lo|hi)_'+pin+r' .*\n','',s)
  return s+f'.include {p}\n.lib {e["lib"]} {res}\n',delay
 g['base']=physical
 return g
if __name__=='__main__':
 import sys
 if len(sys.argv)>1 and sys.argv[1]=='dc':
  result={}
  for res in ['res_typical','res_ff','res_ss']:
   g=engine(res)
   for t in [-40,27,85,125]:
    for v in [3.0,3.3,3.6]:
     dest=out/res/'dc'/f'{t}_{v}';s,_=g['base']('typical',t,v,'diode_typical',cext=1)
     a=g['ng'](dest,s+g['control'](dest,'op','v(BIAS_PIN) v(PREF_PIN) i(Vcore_BIAS) i(Vcore_PREF)'))[0]
     result[f'{res}_{t}_{v}']={'res_corner':res,'temp_C':t,'supply_V':v,'column_core_uA':float(a[3]*1e6),'buffer_core_uA':float(-a[4]*1e6)}
  # Isolate actual PDK resistor resistance at 10mV and grounded substrate.
  resistor={}
  for res in ['res_typical','res_ff','res_ss']:
   for t in [-40,27,85,125]:
    dest=out/res/'resistor'/str(t)
    deck=e['header']('diode_typical',t,3.3)+f'.lib {e["lib"]} {res}\nVtest A 0 .01\nXr A 0 0 ppolyf_u r_width=3.2u r_length=1u\n.control\nset wr_vecnames\nset wr_singlescale\nop\nwrdata {dest}/wave.txt i(Vtest)\nquit\n.endc\n.end\n'
    a=e['run'](dest,deck)[0];resistor[f'{res}_{t}']=-.01/float(a[1])
  (root/'simulations/pad-layout-dc.json').write_text(json.dumps({'cases':result,'resistor_ohm':resistor},indent=2)+'\n');print('DC cases',len(result),'resistor range',min(resistor.values()),max(resistor.values()))
 else:
  tasks=[('res_typical','typical',27,3.3,'diode_typical'),('res_ss','typical',125,3.0,'diode_ff'),('res_ff','typical',125,3.0,'diode_ff'),('res_ss','ss',-40,3.0,'diode_ss'),('res_ss','fs',125,3.0,'diode_typical')]
  def scan(task):
   res,c,t,v,d=task;g=engine(res);name,r=g['scan'](c,t,v,d,cext=1);return res+'/'+name,r
  result={}
  with ThreadPoolExecutor(max_workers=3) as pool:
   for f in as_completed([pool.submit(scan,t) for t in tasks]):
    name,r=f.result();result[name]=r;(root/'simulations/pad-layout-imaging.json').write_text(json.dumps({'cases':result,'scope':'Physical local poly resistor and two diodes; local wiring/fill capacitance. Primary pad remains library schematic model. No metal wire R or full pad-ring extraction.'},indent=2)+'\n')
