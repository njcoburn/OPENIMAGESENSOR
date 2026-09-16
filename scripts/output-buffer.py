"""Nominal PMOS follower and generic board/ADC load experiments."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,re,hashlib
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];out=root/'build/output-buffer';out.mkdir(parents=True,exist_ok=True)
base=(root/'circuits/output-buffer-template.spice').read_text().replace('/foss/designs/build/readout-pex/readout_reduced.spice',str(root/'checkpoints/readout/pex/readout_reduced.spice'))
inc=f'.include {root}/circuits/output-buffer.spice\n'
# Generic lumped assumptions, not a specific ADC or package model.
def stage(ua,pf,adc,acq_us=1):
 s=inc+f'Xbuffer OUT BUF PREF VDD 0 output_buffer\nIbufref PREF 0 {ua}u\nRbond BUF BOND 1\nLbond BOND PAD 5n\nCpad PAD 0 5p\nRiso PAD ADCIN 100\nCboard ADCIN 0 {pf}p\nRinput ADCIN 0 1Meg\n'
 if adc:
  s+='Csample HOLD 0 20p\nSsample ADCIN HOLD ACQ 0 sample_switch\nSreset HOLD 0 RSTADC 0 sample_switch\n.model sample_switch SW(Ron=100 Roff=1e12 Vt=1.65 Vh=0)\n'
  # Three 1us acquisition windows per selected row; reset the sampling cap first.
  for name,offset in [('ACQ',10-acq_us),('RSTADC',8-acq_us)]:
   points=[(0,0)]
   for f in range(3):
    for r in range(3):
     for c in range(3):
      t=f*.003+r*.001+.000975+c*18e-6+offset*1e-6
      duration=(acq_us if name=='ACQ' else 1)*1e-6
      points.extend([(t,0),(t+10e-9,3.3),(t+duration,3.3),(t+duration+10e-9,0)])
   s+=f'V{name} {name} 0 PWL('+' '.join(f'{t:.12g} {v}' for t,v in points)+')\n'
 return s

def ng(dest,s):
 (dest/'testbench.spice').write_text(s);p=subprocess.run(['ngspice','-b',str(dest/'testbench.spice')],capture_output=True,text=True);(dest/'run.log').write_text(p.stdout+p.stderr)
 assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',p.stdout+p.stderr,re.I|re.M),str(dest)
 return np.loadtxt(dest/'wave.txt',skiprows=1)

def run(case):
 ua,pf,adc=case[:3];acq_us=case[3] if len(case)>3 else 1;name=f'{ua}uA_{pf}pF'+(f'_sampled{acq_us}us' if adc else '');dest=out/name;dest.mkdir(exist_ok=True)
 s=base.replace('.control',stage(ua,pf,adc,acq_us)+'.control')
 vectors='v(OUT) v(BUF) v(ADCIN) i(Vdd)'+(' v(HOLD)' if adc else '')
 s=re.sub('wrdata .*',f'wrdata {dest}/wave.txt {vectors}',s)
 d=ng(dest,s);assert np.isfinite(d).all() and d[-1,0]>=.00905
 # Loaded static transfer reference, including the same DC output resistance.
 dc=dest/'dc';dc.mkdir(exist_ok=True)
 header=base[:base.index('Vdd VDD')]
 ds=header+'Vdd VDD 0 3.3\nVin OUT 0 0\n'+stage(ua,pf,False)+f'.control\nset num_threads=1\nset wr_singlescale\nset wr_vecnames\ndc Vin 0 1.4 .002\nwrdata {dc}/wave.txt v(ADCIN)\nquit\n.endc\n.end\n'
 transfer=ng(dc,ds)
 samples=[]
 for r in range(3):
  for c in range(3):
   t=.006975+r*.001+c*18e-6+10e-6
   at=lambda col:float(np.interp(t,d[:,0],d[:,col]))
   expected=float(np.interp(at(1),transfer[:,0],transfer[:,1]))
   samples.append({'row':r,'col':c,'input_V':at(1),'output_V':at(3),'static_expected_V':expected,'tracking_error_mV':1000*(at(3)-expected),'hold_error_mV':1000*(at(5)-expected) if adc else None})
 mask=(d[:,0]>=.006)&(d[:,0]<=.009)
 result={'bias_reference_uA':ua,'board_capacitance_pF':pf,'adc_sampling':adc,'acquisition_us':acq_us if adc else None,'samples':samples,'max_tracking_error_mV':max(abs(x['tracking_error_mV']) for x in samples),'mean_total_VDD_power_uW':float(-3.3*np.trapezoid(d[mask,4],d[mask,0])/(d[mask,0][-1]-d[mask,0][0])*1e6),'testbench_sha256':hashlib.sha256(s.encode()).hexdigest()}
 print(name,result['max_tracking_error_mV'],flush=True)
 return name,result,d,transfer
if __name__=='__main__':
 runs=list(ThreadPoolExecutor(max_workers=3).map(run,[(5,100,False),(20,100,False),(20,1000,False),(20,100,True)]))
 fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
 for name,r,d,dc in runs:
  m=(d[:,0]>=.00697)&(d[:,0]<=.00703);ax[0].plot((d[m,0]-.00697)*1e6,d[m,3],label=name)
  if not r['adc_sampling']:ax[1].plot(dc[:,0],dc[:,1],label=name)
 ax[0].set(xlabel='Time after row selection (µs)',ylabel='ADC input voltage (V)',title='Buffered output under external loads')
 ax[1].set(xlabel='Mux voltage (V)',ylabel='ADC input, static (V)',title='Follower level shift and gain')
 for a in ax:a.grid(alpha=.2);a.legend()
 fig.savefig(root/'docs/assets/output-buffer.png',dpi=160)
 (root/'simulations/output-buffer.json').write_text(json.dumps({'cases':{n:r for n,r,d,dc in runs},'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'circuits/output-buffer.spice',root/'checkpoints/readout/pex/readout_reduced.spice',root/'simulations/extracted-20um/rc-filled/array_reduced.spice']},'scope':'Schematic PMOS follower on qualified extracted readout and extracted array. Ideal 5/20uA reference. Generic 1ohm/5nH bond path, 5pF pad, 100ohm isolation, 100pF or 1nF board capacitance, 1Meg DC input. Optional ideal switched 20pF sampling capacitor, 100ohm acquisition switch, 1us acquisition. No specific ADC accuracy claim; typical corner only; buffer not laid out.'},indent=2)+'\n')
