"""Buildable board-resistor bias on the unchanged extracted sensor core."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,re,json,hashlib
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'build/bias-reference';out.mkdir(exist_ok=True)
model=root/'checkpoints/integrated/pex/sensor_reduced.spice'
verify=json.loads((root/'simulations/integrated-verification.json').read_text())
assert hashlib.sha256((root/'checkpoints/integrated/sensor_3x3.gds').read_bytes()).hexdigest()==verify['gds_sha256']
assert model.read_bytes()==(root/'build/integrated-pex/sensor_reduced.spice').read_bytes()
fingerprint=''.join(hashlib.sha256(p.read_bytes()).hexdigest() for p in [model,root/'circuits/board-bias.spice'])
def value(s):
 m=re.fullmatch(r'([\d.eE+-]+)([a-zA-Z]*)',s);return float(m[1])*{'':1,'n':1e-9,'u':1e-6,'m':1e-3}[m[2]]
def base(corner,temp,supply,diode='diode_typical',rc=1,rb=1,cext=5,ramp_us=0,scan=False):
 s=(root/'circuits'/('bias-scan-template.spice' if scan else 'bias-dc-template.spice')).read_text()
 s=s.replace('sm141064.ngspice typical',f'sm141064.ngspice {corner}').replace('sm141064.ngspice diode_typical',f'sm141064.ngspice {diode}').replace('.temp 27',f'.temp {temp}')
 s=re.sub(r'(?m)^I(?:ref|bufref) .*\n','',s)
 s+=f'.include {root}/circuits/board-bias.spice\nXbias VDD 0 BIAS PREF board_bias RCOL={5.1e6*rc:.12g} RBUF={49900*rb:.12g} CEXT={cext}p\n'
 s=re.sub(r'(?m)^Vdd .*$',f'Vdd VDD 0 {supply}',s)
 delay=(ramp_us+200)*1e-6 if scan else 0
 if scan:
  s=re.sub(r'(?m)^Vdd .*$',f'Vdd VDD 0 PWL(0 0 {ramp_us*1e-6:.12g} {supply})',s)
  s=re.sub(r'(?m)^Vreset .*$',f'Vreset VRESET 0 PWL(0 0 {ramp_us*1e-6:.12g} 2)',s)
  # External controller holds every reset high through power-up and bias settling.
  # Its reset outputs track VDD, preventing a powered input on an unpowered chip.
  def pwl(m):
   name,node,points=m.groups();p=points.split();q=[];is_reset=bool(re.fullmatch(r'Vr[0-2]',name))
   for i in range(0,len(p),2):
    t=float(p[i]);v=float(p[i+1]);q += [f'{t+delay if t else 0:.12g}',f'{v/3.3 if is_reset else v:.12g}']
   if is_reset:return f'{name} CTL_{node} 0 PWL('+ ' '.join(q)+f')\nBdrive_{node} {node} 0 V=V(CTL_{node})*V(VDD)'
   return f'{name} {node} 0 PWL('+ ' '.join(q)+')'
  s=re.sub(r'(?m)^(V\w+) (\w+) 0 PWL\(([^\n]+)\)$',lambda m:m[0] if m[1] in ['Vdd','Vreset'] else pwl(m),s)
  def pulse(m):
   name,node,params=m.groups();q=params.split();q[1]=str(supply);q[2]=f'{value(q[2])+delay:.12g}'
   return f'{name} {node} 0 PULSE('+ ' '.join(q)+')'
  s=re.sub(r'(?m)^(V(?:s[0-2]|sel[0-2])) (\w+) 0 PULSE\(([^\n]+)\)$',pulse,s)
 else:
  s=re.sub(r'(?m)^(V(?:r|s)[0-2] \w+ 0) 3.3$',rf'\g<1> {supply}',s)
 assert not re.search(r'(?m)^I(?:ref|bufref) ',s)
 return s,delay
def ng(folder,s):
 folder.mkdir(parents=True,exist_ok=True);stamp=folder/'success.sha256';key=hashlib.sha256((s+fingerprint).encode()).hexdigest()
 if stamp.exists() and stamp.read_text()==key:return np.loadtxt(folder/'wave.txt',skiprows=1,ndmin=2)
 (folder/'testbench.spice').write_text(s)
 try:
  with (folder/'run.log').open('w') as log:p=subprocess.run(['ngspice','-b',str(folder/'testbench.spice')],stdout=log,stderr=subprocess.STDOUT,timeout=600)
 except subprocess.TimeoutExpired as e:
  raise RuntimeError(f'600s timeout: {folder}')
 log=(folder/'run.log').read_text()
 assert p.returncode==0 and not re.search('aborted|timestep too small|^Error',log,re.I|re.M),str(folder)
 a=np.loadtxt(folder/'wave.txt',skiprows=1,ndmin=2);assert np.isfinite(a).all();stamp.write_text(key);return a
def control(folder,analysis,vectors):return f'.control\nset num_threads=1\nset wr_singlescale\nset wr_vecnames\n{analysis}\nwrdata {folder}/wave.txt {vectors}\nquit\n.endc\n.end\n'
def tag(c,t,v,d,rc,rb):return f'{c}_{t}C_{v}V_{d}_rc{rc}_rb{rb}'
def op(case):
 c,t,v,d,rc,rb=case;name=tag(*case);dest=out/'op'/name;s,_=base(*case[:4],rc=rc,rb=rb)
 try:
  a=ng(dest,s+control(dest,'op','v(BIAS) v(PREF) i(Vdd)'))[0]
  r={'status':'complete','column_reference_uA':(v-a[1])/(5.1e6*rc)*1e6,'buffer_reference_uA':a[2]/(49900*rb)*1e6,'bias_V':a[1],'pref_V':a[2],'supply_power_uW':-v*a[3]*1e6}
 except Exception as e:r={'status':'failed','error':str(e)}
 r.update(corner=c,temp_C=t,supply_V=v,diode=d,rcol_scale=rc,rbuf_scale=rb)
 (dest/'result.json').write_text(json.dumps(r,indent=2)+'\n');return name,r
def scan(c,t,v,d='diode_typical',rc=1,rb=1,ramp_us=1,cext=5,step=.1):
 name=tag(c,t,v,d,rc,rb)+f'_ramp{ramp_us}us_C{cext}p_step{step}us';dest=out/'scan'/name;dest.mkdir(parents=True,exist_ok=True)
 s,delay=base(c,t,v,d,rc,rb,cext,ramp_us,True)
 if step<.1:s=s.replace('reltol=5e-5','reltol=1e-5')
 try:
  a=ng(dest,s+control(dest,f'tran {step}u {delay+.00905:.12g} uic','v(OUT) v(BUF) v(ADCIN) i(Vdd) v(HOLD) v(BIAS) v(PREF) v(VDD)'))
  assert a[-1,0]>=delay+.00905-1e-12
  dc=dest/'dc';h,_=base(c,t,v,d,rc,rb,cext)
  if step<.1:h=h.replace('reltol=5e-5','reltol=1e-5')
  transfer=ng(dc,h+control(dc,'dc Vin 0 1.4 .002','v(ADCIN)'))
  samples=[]
  for row in range(3):
   for col in range(3):
    tm=delay+.006975+row*.001+col*18e-6+10e-6;at=lambda k:float(np.interp(tm,a[:,0],a[:,k]))
    assert transfer[0,0]<=at(1)<=transfer[-1,0]
    expected=float(np.interp(at(1),transfer[:,0],transfer[:,1]))
    samples.append({'row':row,'col':col,'input_V':at(1),'output_V':at(3),'hold_error_mV':1000*(at(5)-expected),'tracking_error_mV':1000*(at(3)-expected)})
  matrix=np.array([x['output_V'] for x in samples]).reshape(3,3);pattern=np.array([[0,80,240],[240,0,80],[80,240,0]])
  ordering=all(np.all(np.diff(matrix[i,np.argsort(pattern[i])])<0) for i in range(3))
  ib=(a[:,8]-a[:,6])/(5.1e6*rc)*1e6;ip=a[:,7]/(49900*rb)*1e6
  # Last 10us of startup hold, compared with the steady tail of frame three.
  startup=(a[:,0]>=delay-10e-6)&(a[:,0]<=delay)
  stable=(a[:,0]>=delay+.006)&(a[:,0]<=delay+.009)
  duration=a[stable,0][-1]-a[stable,0][0]
  bmean=float(np.trapezoid(ib[stable],a[stable,0])/duration);pmean=float(np.trapezoid(ip[stable],a[stable,0])/duration)
  startup_error=max(float(np.max(abs(ib[startup]/bmean-1))),float(np.max(abs(ip[startup]/pmean-1))))
  r={'status':'complete','samples':samples,'max_hold_error_mV':max(abs(x['hold_error_mV']) for x in samples),'max_tracking_error_mV':max(abs(x['tracking_error_mV']) for x in samples),'brightness_order_ok':bool(ordering),'mean_column_reference_uA':bmean,'mean_buffer_reference_uA':pmean,'startup_reference_relative_error':startup_error,'mean_VDD_power_uW':float(np.trapezoid(-a[stable,8]*a[stable,4],a[stable,0])/(a[stable,0][-1]-a[stable,0][0])*1e6)}
  r['screen_pass']=bool(ordering and r['max_hold_error_mV']<.5 and r['max_tracking_error_mV']<.5 and startup_error<.01)
 except Exception as e:r={'status':'failed','error':str(e),'screen_pass':False}
 r.update(corner=c,temp_C=t,supply_V=v,diode=d,rcol_scale=rc,rbuf_scale=rb,ramp_us=ramp_us,external_bias_C_pF=cext,step_us=step,scan_delay_s=delay)
 (dest/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(name,r['status'],r.get('max_hold_error_mV'),flush=True);return name,r
if __name__=='__main__':
 cases=[(c,t,v,'diode_typical',1,1) for c in ['typical','ff','ss','fs','sf'] for t in [-40,27,85,125] for v in [3.0,3.3,3.6]]
 cases += [('typical',t,v,d,1,1) for d in ['diode_ff','diode_ss'] for t in [-40,125] for v in [3.0,3.3,3.6]]
 cases += [(c,t,v,'diode_typical',rc,rb) for c,t,v in [('typical',27,3.3),('ss',-40,3.0),('ff',125,3.6)] for rc in [.99,1.01] for rb in [.99,1.01]]
 results=dict(ThreadPoolExecutor(max_workers=4).map(op,cases))
 (root/'simulations/bias-reference-dc.json').write_text(json.dumps({'cases':results,'gds_sha256':verify['gds_sha256'],'resistors_ohm':{'column':5.1e6,'buffer':49900}},indent=2)+'\n')
 print('DC complete',sum(r['status']=='complete' for r in results.values()),'/',len(results))
