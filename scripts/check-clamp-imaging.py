"""Camera imaging with clamp pair and one-millisecond supply soft-start."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import runpy,os,json,hashlib
root=Path(__file__).resolve().parents[1]
os.environ['SPICE_USERINIT_DIR']=str(root/'checkpoints/pad-closure/ngspice-init')
e=runpy.run_path(str(root/'scripts/simulate-pad-layout.py'))
model=root/'checkpoints/pad-closure/supply-pad-models.spice';pair=root/'circuits/sensor-supply-pads.spice'
def test(case):
 c,t,v,d,clamped=case;g=e['engine']('res_ss');base=g['base'];mode='with-clamps' if clamped else 'matched-control';g['out']=root/'build/clamp-imaging'/mode;g['fingerprint']+=hashlib.sha256(model.read_bytes()+pair.read_bytes()).hexdigest()+'hsa-wnflag1'
 def supply(*args,**kw):
  s,delay=base(*args,**kw)
  if clamped:s+=f'.include {model}\n.include {pair}\nXsupply VDD 0 sensor_supply_pads\n'
  return s,delay
 g['base']=supply
 name,r=g['scan'](c,t,v,d,ramp_us=1000,cext=1);return mode+'/'+name,r
if __name__=='__main__':
 tasks=[(c,t,v,d,clamped) for c,t,v,d in [('typical',27,3.3,'diode_typical'),('typical',125,3.0,'diode_ff')] for clamped in [False,True]];rows={}
 with ThreadPoolExecutor(max_workers=3) as pool:
  for f in as_completed([pool.submit(test,t) for t in tasks]):
   name,r=f.result();rows[name]=r;(root/'simulations/clamp-imaging.json').write_text(json.dumps({'cases':rows,'scope':'Two matched camera conditions with/without foundry clamp pair. HSPICE compatibility and width-per-finger binning. 1ms ideal supply ramp, 200us post-ramp reset hold; primary/local protection and extracted core retained. Typical MOS-cap section; res_ss. Finite source-impedance tests are separate.'},indent=2)+'\n')
