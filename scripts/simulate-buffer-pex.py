"""Extracted buffer + qualified readout + extracted array, connected at ideal ports."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,types,json,hashlib,gzip,shutil
root=Path(__file__).resolve().parents[1];pex=root/'build/buffer-pex';out=pex/'sim';out.mkdir(exist_ok=True)
files={'devices':'buffer_devices','C':'buffer_c','RC':'buffer_reduced'}
verify=json.loads((root/'simulations/buffer-layout-verification.json').read_text())
assert hashlib.sha256((root/'checkpoints/output-buffer/output_buffer.gds').read_bytes()).hexdigest()==verify['gds_sha256']
assert 'Circuits match uniquely.' in (pex/'lvs.log').read_text()

def simulate(corner,temp,diode='diode_typical',kind='RC',step=.1):
 module=runpy.run_path(str(root/'scripts/buffer-hardening.py'));combined=module['combined'];g=combined.__globals__;loader=g['runpy'].run_path
 net=pex/(files[kind]+'.spice');sub=next(l.split() for l in net.read_text().splitlines() if l.startswith('.subckt'))
 g['out']=out/kind;g['out'].mkdir(exist_ok=True);g['fingerprint']+=hashlib.sha256(net.read_bytes()).hexdigest()
 def load(path):
  m=loader(path);run=m['run'];env=run.__globals__;stage=env['stage']
  def extracted_stage(*args,**kwargs):
   s=stage(*args,**kwargs)
   s=s.replace(str(root/'circuits/output-buffer.spice'),str(net))
   pins={'GND':'0','VDD':'VDD','PREF':'PREF','IN':'OUT','BUF':'BUF'}
   s=s.replace('Xbuffer OUT BUF PREF VDD 0 output_buffer','Xbuffer '+' '.join(pins[p] for p in sub[2:])+' '+sub[1])
   return s
  env['stage']=extracted_stage;return m
 g['runpy']=types.SimpleNamespace(run_path=load)
 name,r=combined(corner,temp,40,step=step,diode=diode,variant='_startup_reset')
 r['buffer_model']=kind;r['screen_pass']=bool(r['status']=='complete' and r['brightness_order_ok'] and r['max_hold_error_mV']<.5 and r['max_tracking_error_mV']<.5)
 return f'{kind}/{name}',r

if __name__=='__main__':
 cases=[(c,t,d,'RC') for c,t,d in [(c,t,'diode_typical') for c in ['typical','ff','ss','fs','sf'] for t in [-40,27,85,125]]+[('typical',t,d) for d in ['diode_ff','diode_ss'] for t in [-40,125]]]+[('typical',27,'diode_typical','devices'),('typical',27,'diode_typical','C')]
 results=dict(ThreadPoolExecutor(max_workers=4).map(lambda c:simulate(*c),cases))
 baseline=json.loads((root/'simulations/buffer-hardened-corners.json').read_text())['cases']
 for r in results.values():
  if r['status']!='complete':continue
  old=next(v for v in baseline.values() if (v['corner'],v['temp_C'],v['diode'])==(r['corner'],r['temp_C'],r['diode']))
  r['max_output_shift_vs_schematic_mV']=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(r['samples'],old['samples']))
 controls=[r for r in results.values() if r['buffer_model']=='devices'];assert len(controls)==1 and controls[0]['status']=='complete' and controls[0]['max_output_shift_vs_schematic_mV']<.01,controls
 summary={'cases':results,'reduction':json.loads((pex/'reduction.json').read_text()),'gds_sha256':verify['gds_sha256'],'scope':'Three independently extracted blocks joined by ideal wires; 40uA buffer reference, all-row 20us startup reset, 100pF board + 20pF sampler, 5us acquisition. Nominal extracted R/C held fixed across model corners/temperatures. Existing readout BIAS shunt approximation remains; buffer extraction needs no such redistribution correction. No real pads/ESD, integrated routing, physical reference/control generators or actual ADC model.'}
 (root/'simulations/buffer-pex.json').write_text(json.dumps(summary,indent=2)+'\n')
 dest=root/'checkpoints/output-buffer/pex';dest.mkdir(exist_ok=True)
 for f in ['buffer_reduced.spice','buffer_devices.spice','buffer_c.spice','reduction.json','lvs.log','extraction.log']:shutil.copyfile(pex/f,dest/f)
 with gzip.open(dest/'buffer_raw.spice.gz','wb') as archive:archive.write((pex/'buffer_rc.spice').read_bytes())
 print('SUMMARY',sum(r['screen_pass'] for r in results.values()),'of',len(results),flush=True)
