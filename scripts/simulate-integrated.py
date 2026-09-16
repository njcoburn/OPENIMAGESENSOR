"""Resimulate the physically connected chip with the established load/timing.
DC calibration forces OUT with all rows selected, mux off and reset on.
It includes the integrated supply/ground network, not a standalone buffer.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,re,json,hashlib
root=Path(__file__).resolve().parents[1];pex=root/'build/integrated-pex';out=pex/'sim';out.mkdir(exist_ok=True)
assert 'Circuits match uniquely.' in (pex/'lvs.log').read_text()
verify=json.loads((root/'simulations/integrated-verification.json').read_text())
assert hashlib.sha256((root/'checkpoints/integrated/sensor_3x3.gds').read_bytes()).hexdigest()==verify['gds_sha256']
oldmap=json.loads((root/'simulations/extracted-20um/rc-filled/reduction.json').read_text())['node_map']
mapping=json.loads((pex/'reduction.json').read_text())['node_map']
def simulate(corner,temp,diode='diode_typical',step=.1,kind='RC'):
 m=runpy.run_path(str(root/'scripts/buffer-hardening.py'));f=m['combined'];g=f.__globals__;ng=g['ng']
 net=pex/({'RC':'sensor_reduced.spice','alternate':'sensor_alternate.spice','devices':'sensor_devices.spice','C':'sensor_c.spice','lowR':'sensor_lowr.spice'}[kind]);sub=next(l.split() for l in net.read_text().splitlines() if l.startswith('.subckt'))
 g['out']=out/kind;g['out'].mkdir(exist_ok=True);g['fingerprint']+=hashlib.sha256(net.read_bytes()).hexdigest()
 def connected(dest,s):
  s=re.sub(r'(?m)^\.include .*?(?:array_reduced|readout_reduced|output-buffer)\.spice\n','',s)
  s=re.sub(r'(?m)^X(?:array|readout) .*\n','',s)
  pins=['0' if p=='GND' else p for p in sub[2:]]
  s=re.sub(r'(?m)^Xbuffer .*$',f'.include {net}\nXsensor '+ ' '.join(pins)+' '+sub[1],s)
  substitutions={}
  for key,roles in oldmap.items():
   for role,node in roles.items():
    new=mapping[key][role] if kind in ['RC','alternate','lowR'] else ('GND' if role=='anode' else ('s' if role=='sense' else 'f')+key)
    substitutions['xarray.'+node]='0' if kind in ['devices','C'] and role=='anode' else 'xsensor.'+new
  s=re.sub(r'xarray\.\w+',lambda m:substitutions[m[0]],s)
  if '\ndc Vin ' in s:
   controls='Vreset VRESET 0 2\nIref VDD BIAS 0.5u\n'
   for i in range(3):controls+=f'Vr{i} RST{i} 0 3.3\nVs{i} ROW{i} 0 3.3\nVsel{i} SEL{i} 0 0\n'
   s=s.replace('.control',controls+'.control')
  assert 'xarray.' not in s and 'Xreadout ' not in s
  return ng(dest,s)
 g['ng']=connected
 name,r=f(corner,temp,40,step=step,diode=diode,variant='_startup_reset')
 r['model']=kind;r['screen_pass']=bool(r['status']=='complete' and r['brightness_order_ok'] and r['max_hold_error_mV']<.5 and r['max_tracking_error_mV']<.5)
 return kind+'/'+name,r
if __name__=='__main__':
 cases=[('typical',27,'diode_typical',.1,'RC'),('ss',-40,'diode_typical',.1,'RC'),('typical',125,'diode_ff',.1,'RC'),('typical',27,'diode_typical',.1,'devices')]
 cases += [('typical',27,'diode_typical',.1,k) for k in ['C','lowR']]
 results=dict(ThreadPoolExecutor(max_workers=4).map(lambda c:simulate(*c),cases))
 baseline=json.loads((root/'simulations/buffer-pex.json').read_text())['cases']
 for r in results.values():
  if r['status']!='complete':continue
  old=next(v for v in baseline.values() if v['buffer_model']=='RC' and (v['corner'],v['temp_C'],v['diode'])==(r['corner'],r['temp_C'],r['diode']))
  r['max_output_shift_vs_separate_blocks_mV']=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(r['samples'],old['samples']))
 d={'cases':results,'gds_sha256':verify['gds_sha256'],'reduction':json.loads((pex/'reduction.json').read_text()),'scope':'Connected extracted layout. Three sentinel RC conditions plus nominal device-only, C-only and 10%-resistance controls; not a repeat of the full 24-case matrix. Fixed nominal wire RC, ideal references and controls, generic external ADC load. DC transfer: OUT forced, all rows selected, mux off, reset on; shared supply loading may differ from active readout. Imaging transient retains rolling selection.'}
 (root/'simulations/integrated-pex.json').write_text(json.dumps(d,indent=2)+'\n')
 print('SUMMARY',sum(r['screen_pass'] for r in results.values()),'of',len(results),flush=True)
