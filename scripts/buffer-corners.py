"""Deterministic process/temperature screening; no mismatch or optical model."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json,hashlib,re,subprocess
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];out=root/'build/buffer-corners';out.mkdir(parents=True,exist_ok=True)
models=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice')
inputs=[root/'scripts/output-buffer.py',root/'circuits/output-buffer.spice',root/'circuits/output-buffer-template.spice',root/'checkpoints/readout/pex/readout_reduced.spice',root/'simulations/extracted-20um/rc-filled/array_reduced.spice',models,models.with_suffix('.spice')]
provenance={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
model_text=models.read_text()
for corner in ['typical','ff','ss','fs','sf','diode_typical','diode_ff','diode_ss']:assert re.search(r'(?m)^\.lib '+corner+r'\s*$',model_text)
cases=[(c,t,'diode_typical') for c in ['typical','ff','ss','fs','sf'] for t in [-40,27,85,125]]+ [('typical',t,d) for d in ['diode_ff','diode_ss'] for t in [-40,125]]
def worker(case):
 corner,temp,diode=case;name=f'{corner}_{temp}C_{diode}'+(f'_refined_{globals().get("STEP",0.1)}us' if globals().get('REFINE',False) else '');dest=out/name;dest.mkdir(exist_ok=True)
 m=runpy.run_path(str(root/'scripts/output-buffer.py'));run=m['run'];g=run.__globals__
 base=g['base'].replace('sm141064.ngspice typical',f'sm141064.ngspice {corner}').replace('sm141064.ngspice diode_typical',f'sm141064.ngspice {diode}')
 base=base.replace('Vdd VDD',f'.temp {temp}\nVdd VDD',1)
 if globals().get('REFINE',False):base=base.replace('tran 0.2u',f'tran {globals().get("STEP",0.1)}u').replace('reltol=1e-4',f'reltol={globals().get("RELTOL",5e-5)}')
 g['base']=base;g['out']=dest
 def cached_ng(folder,source):
  key=hashlib.sha256((source+json.dumps(provenance,sort_keys=True)).encode()).hexdigest();stamp=folder/'success.sha256'
  if stamp.exists() and stamp.read_text()==key and (folder/'wave.txt').exists():return np.loadtxt(folder/'wave.txt',skiprows=1)
  (folder/'testbench.spice').write_text(source)
  p=subprocess.run(['ngspice','-b',str(folder/'testbench.spice')],capture_output=True,text=True);(folder/'run.log').write_text(p.stdout+p.stderr)
  assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',p.stdout+p.stderr,re.I|re.M),str(folder)
  wave=np.loadtxt(folder/'wave.txt',skiprows=1);assert np.isfinite(wave).all()
  if '\ntran ' in source:assert wave[-1,0]>=.00905
  stamp.write_text(key);return wave
 g['ng']=cached_ng
 try:
  _,result,wave,dc=run((20,100,True,5))
  assert all(dc[0,0]<=s['input_V']<=dc[-1,0] for s in result['samples']),'Input outside DC transfer sweep'
  sampled=np.array([s['output_V'] for s in result['samples']]).reshape(3,3);pattern=np.array([[0,80,240],[240,0,80],[80,240,0]])
  ordering=all(np.all(np.diff(sampled[r,np.argsort(pattern[r])])<0) for r in range(3))
  hold=max(abs(s['hold_error_mV']) for s in result['samples']);result.update(corner=corner,temperature_C=temp,diode_corner=diode,status='complete',max_hold_error_mV=hold,brightness_order_ok=bool(ordering),screen_pass=bool(hold<1 and result['max_tracking_error_mV']<1 and ordering),output_range_V=[float(sampled.min()),float(sampled.max())])
 except Exception as error:
  result={'corner':corner,'temperature_C':temp,'diode_corner':diode,'status':'simulation_failed','error':str(error),'screen_pass':False}
 (dest/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,json.dumps({k:result[k] for k in ['status','screen_pass','max_hold_error_mV','output_range_V'] if k in result}),flush=True)
 return name,result
def plot_results(results):
 fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
 for corner in ['typical','ff','ss','fs','sf']:
  rows=[r for r in results.values() if r['corner']==corner and r['diode_corner']=='diode_typical' and r['status']=='complete']
  ax[0].plot([r['temperature_C'] for r in rows],[r['max_hold_error_mV'] for r in rows],'o-',label=corner)
  ax[1].plot([r['temperature_C'] for r in rows],[r['mean_total_VDD_power_uW'] for r in rows],'o-',label=corner)
 ax[0].axhline(1,color='black',linestyle='--',label='1 mV screening limit');ax[0].set(xlabel='Temperature (°C)',ylabel='Worst sample-capacitor error (mV)',title='Five MOS corners · typical diode')
 ax[1].set(xlabel='Temperature (°C)',ylabel='Mean total VDD power (µW)',title='Ideal reference currents held fixed')
 for a in ax:a.grid(alpha=.2);a.legend()
 fig.savefig(root/'docs/assets/buffer-corners.png',dpi=160)

if __name__=='__main__':
 results=dict(ThreadPoolExecutor(max_workers=4).map(worker,cases))
 summary={'cases':results,'source_sha256':provenance,'screen_limit_mV':1,'scope':'20uA ideal buffer reference; 0.5uA ideal readout reference; 3.3V supply; 5us acquisition; 100pF board and 20pF sampler. Five MOS corners at four temperatures with diode_typical, plus diode_ff/ss at temperature endpoints with typical MOS. Model temperature applied to devices. Extracted R/C, package estimates, ideal sources, optical current and load values fixed. Not a complete corner cross-product, supply sweep, mismatch/noise analysis, optical temperature model, or fabrication qualification.'}
 (root/'simulations/buffer-corners.json').write_text(json.dumps(summary,indent=2)+'\n')
 plot_results(results)
 print('SUMMARY',sum(r['status']=='complete' for r in results.values()),'completed;',sum(r['screen_pass'] for r in results.values()),'passed of',len(results),flush=True)
