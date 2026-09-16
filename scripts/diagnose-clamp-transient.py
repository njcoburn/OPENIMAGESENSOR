"""Isolate long clamp transients; preserve all original model/tolerance settings."""
from pathlib import Path
import runpy,os,json,subprocess,time,re
from concurrent.futures import ThreadPoolExecutor,as_completed
root=Path(__file__).resolve().parents[1]
os.environ['SPICE_USERINIT_DIR']=str(root/'checkpoints/pad-closure/ngspice-init')
out=root/'build/clamp-diagnostic';out.mkdir(exist_ok=True)
def test(kind):
 folder=out/kind;folder.mkdir(exist_ok=True)
 if kind=='isolated':
  e=runpy.run_path(str(root/'scripts/evaluate-supply-clamps.py'))
  s=e['header']('res_ss','moscap_typical','diode_ff',125,3.0).replace('Vdd VDD 0 3.0','Vdd VDD 0 PWL(0 0 1m 3.0)').replace('abstol=1e-15 reltol=1e-5','abstol=1e-14 reltol=5e-5 chgtol=1e-16 trtol=3')
  s+=e['control'](folder,'tran .1u 10.25m uic','v(VDD) i(Vdd) v(xvdd.n4) v(xvdd.n8)')
 else:
  original=next((root/'build/clamp-imaging/with-clamps/scan').glob('*125C*/testbench.spice'))
  s=original.read_text().replace(str(original.parent),str(folder))
  if kind=='klu12':s=s.replace('.options gmin','.options klu gmin').replace('abstol=1e-14','abstol=1e-12')
  elif kind=='klu':s=s.replace('.options gmin','.options klu gmin')
  elif kind=='no-bypass':s=s.replace('.options gmin','.options bypass=0 gmin')
  elif kind=='board':s=s.replace('Vdd VDD 0 PWL(0 0 0.001 3.0)','Vdd SOURCE 0 PWL(0 0 0.001 3.0)\nRsource SOURCE VDD 1\nCdec VDD 0 100n')
  elif kind=='adapter':s=s.replace('Xsupply VDD 0 sensor_supply_pads','Eclamp CLAMPDRIVE 0 VDD 0 1\nVclamp CLAMPDRIVE CLAMPRAIL 0\nFclamp VDD 0 Vclamp 1\nXsupply CLAMPRAIL 0 sensor_supply_pads')
  elif kind=='probe':s=s.replace('Xsupply VDD 0 sensor_supply_pads','Vclamp VDD VCLAMP 0\nXsupply VCLAMP 0 sensor_supply_pads')
  elif kind=='saved':s=s.replace('tran 0.1u', 'save v(OUT) v(BUF) v(ADCIN) i(Vdd) v(HOLD) v(BIAS_PIN) v(PREF_PIN) v(VDD)\ntran 0.1u')
  elif kind=='abstol11':s=s.replace('abstol=1e-14','abstol=1e-11')
  elif kind=='abstol12':s=s.replace('abstol=1e-14','abstol=1e-12')
  elif kind=='abstol5e13':s=s.replace('abstol=1e-14','abstol=5e-13')
  elif kind=='gmin15':s=s.replace('gmin=1e-17','gmin=1e-15')
  elif kind=='pivot':s=s.replace('.options gmin','.options pivrel=0.1 gmin')
  elif kind=='euler':s=s.replace('method=gear','method=trap maxord=1')
  elif kind=='trap':s=s.replace('method=gear','method=trap')
  elif kind=='iterations':s=s.replace('.options gmin','.options itl4=100 gmin')
  elif kind=='gmin':s=s.replace('gmin=1e-17','gmin=1e-14')
  elif kind=='no-uic':s=s.replace(' uic\n','\n')
 s=s.replace('\nquit\n','\nrusage all\nquit\n');(folder/'testbench.spice').write_text(s);start=time.monotonic()
 try:
  with (folder/'run.log').open('w') as f:p=subprocess.run(['ngspice','-b',str(folder/'testbench.spice')],stdout=f,stderr=subprocess.STDOUT,timeout=600)
  log=(folder/'run.log').read_text();ok=p.returncode==0 and not re.search('aborted|timestep too small|^Error',log,re.M|re.I)
  result={'status':'complete' if ok else 'failed','wall_s':time.monotonic()-start,'log_tail':log[-2400:]}
 except subprocess.TimeoutExpired:result={'status':'timeout','wall_s':time.monotonic()-start}
 (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(kind,result['status'],round(result['wall_s'],2),flush=True);return kind,result
if __name__=='__main__':
 import sys
 rows={}
 with ThreadPoolExecutor(max_workers=2) as pool:
  for f in as_completed([pool.submit(test,k) for k in (sys.argv[1:] or ['isolated','klu','no-bypass','no-uic','iterations'])]):
   k,r=f.result();rows[k]=r;(root/'simulations/clamp-diagnostic-followup.json').write_text(json.dumps(rows,indent=2)+'\n')
