"""Connect independently extracted array and readout blocks at ideal top-level nets."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,re,subprocess,hashlib,shutil,gzip
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];out=root/'build/readout-pex/sim';out.mkdir(parents=True,exist_ok=True)
base=(root/'circuits/readout-pex-template.spice').read_text();pex=root/'build/readout-pex'
assert 'Circuits match uniquely.' in (pex/'lvs.log').read_text()
verification=json.loads((root/'simulations/readout-verification.json').read_text())
assert hashlib.sha256((root/'checkpoints/readout/column_readout.gds').read_bytes()).hexdigest()==verification['gds_sha256']
cases=[('schematic',None),('devices','readout_devices'),('C','readout_c'),('RC','readout_reduced'),('RC_refined','readout_reduced'),('RC_alternate','readout_alternate')]
def run(case):
 name,file=case;dest=out/name;dest.mkdir(exist_ok=True);s=base
 if file:
  net=pex/(file+'.spice');sub=next(l.split() for l in net.read_text().splitlines() if l.startswith('.subckt'))
  s=re.sub(r'(?m)^(?:Xbias\d|Xref|Xmux\d|Vmeasure\d) .*\n','',s)
  s=s.replace('.control',f'.include {net}\nXreadout '+ ' '.join('0' if n=='GND' else n for n in sub[2:])+' '+sub[1]+'\n.control')
 if name=='RC_refined':s=s.replace('tran 0.2u','tran 0.1u').replace('reltol=1e-4','reltol=5e-5')
 s=re.sub(r'wrdata .*',f'wrdata {dest}/wave.txt v(COL0) v(COL1) v(COL2) v(OUT) v(SEL0) v(SEL1) v(SEL2) v(BIAS) i(Vdd)',s)
 fingerprint=hashlib.sha256((s+(net.read_text() if file else '')+(root/'simulations/extracted-20um/rc-filled/array_reduced.spice').read_text()).encode()).hexdigest()
 reuse=(dest/'success.sha256').exists() and (dest/'success.sha256').read_text()==fingerprint and (dest/'wave.txt').exists() and (dest/'run.log').exists()
 (dest/'testbench.spice').write_text(s)
 p=subprocess.CompletedProcess([],0,stdout=(dest/'run.log').read_text(),stderr='') if reuse else subprocess.run(['ngspice','-b',str(dest/'testbench.spice')],capture_output=True,text=True);(dest/'run.log').write_text(p.stdout+p.stderr)
 assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',p.stdout+p.stderr,re.I|re.M),name
 d=np.loadtxt(dest/'wave.txt',skiprows=1);assert np.isfinite(d).all() and d[-1,0]>=.00905
 samples=[]
 for r in range(3):
  for c in range(3):
   start=.006975+r*.001+c*18e-6
   at=lambda us,col:float(np.interp(start+us*1e-6,d[:,0],d[:,col]))
   samples.append({'row':r,'col':c,'output_V':at(10,4),'column_V':at(10,c+1),'tracking_error_mV':{str(us):1000*(at(us,4)-at(us,c+1)) for us in [1,2,5,10,15]}})
 pattern=np.array([[0,80,240],[240,0,80],[80,240,0]])
 volts=np.array([v['output_V'] for v in samples]).reshape(3,3)
 assert all(np.all(np.diff(volts[r,np.argsort(pattern[r])])<0) for r in range(3)),name
 result={'samples':samples,'max_tracking_error_10us_mV':max(abs(x['tracking_error_mV']['10']) for x in samples),'testbench_sha256':hashlib.sha256(s.encode()).hexdigest()}
 (dest/'success.sha256').write_text(fingerprint)
 print(name,result['max_tracking_error_10us_mV'],flush=True)
 return name,result,d
runs=list(ThreadPoolExecutor(max_workers=3).map(run,cases));data={n:r for n,r,d in runs}
def difference(a,b):return max(abs(x['output_V']-y['output_V'])*1000 for x,y in zip(data[a]['samples'],data[b]['samples']))
placement=difference('RC_alternate','RC');assert placement<.1,placement
control=difference('devices','schematic');refine=difference('RC_refined','RC');assert control<.01 and refine<.1,(control,refine)
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for n,r,d in runs:
 if n in ['devices','RC_refined','RC_alternate']:continue
 m=(d[:,0]>=.006973)&(d[:,0]<=.00703)
 ax[0].plot((d[m,0]-.00697)*1e6,d[m,4],label=n)
 ax[1].plot([1,2,5,10,15],[max(abs(x['tracking_error_mV'][str(us)]) for x in r['samples']) for us in [1,2,5,10,15]],'o-',label=n)
ax[0].set(xlabel='Time after row selection (µs)',ylabel='OUT (V)',title='Third-frame row 0')
ax[1].set(xlabel='Delay after mux selection (µs)',ylabel='Worst |OUT − selected COL| (mV)',title='All nine samples',yscale='log')
for a in ax:a.grid(alpha=.2);a.legend()
fig.savefig(root/'docs/assets/readout-pex.png',dpi=160)
summary={'cases':data,'devices_control_max_difference_mV':control,'bias_placement_max_difference_mV':placement,'refinement_max_difference_mV':refine,'RC_vs_schematic_max_output_difference_mV':difference('RC','schematic'),'gds_sha256':verification['gds_sha256'],'reduction':json.loads((pex/'reduction.json').read_text()),'scope':'Extracted array and standalone extracted readout connected by ideal wires. No parasitics between blocks, shared physical supply routing, buffer, pad/ESD, package or ADC circuitry. Ideal reference and selection drivers; typical corner; no optical calibration/noise/mismatch.'}
(root/'simulations/readout-pex.json').write_text(json.dumps(summary,indent=2)+'\n')
dest=root/'checkpoints/readout/pex';dest.mkdir(exist_ok=True)
for file in ['readout_reduced.spice','readout_alternate.spice','readout_devices.spice','readout_c.spice','reduction.json','lvs.log']:shutil.copyfile(pex/file,dest/file)
with gzip.open(dest/'readout_raw.spice.gz','wb') as archive:archive.write((pex/'readout_rc.spice').read_bytes())
print('Checks:',control,refine,summary['RC_vs_schematic_max_output_difference_mV'],flush=True)
