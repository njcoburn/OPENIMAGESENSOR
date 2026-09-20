"""Normal-operation final-layout candidate with bias-frozen MOS capacitance.
This is not distributed-R qualification or an ADS1115 conversion model.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'checkpoints/clamp-review/package';B=R/'build/filled-electrical-baseline'
parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['op','frame','three-frames']);parser.add_argument('--step-ns',type=float,default=100);parser.add_argument('--method',choices=['trap','gear'],default='trap');args=parser.parse_args()
assert args.step_ns>0
F=R/'build/functional-pad-model';capinfo=json.loads((F/'caps.json').read_text());red=json.loads((B/'reduction.json').read_text());assert red['completed'] and red['devices_unchanged']
assert capinfo['source_sha256']==red['output_sha256']
mp=json.loads((R/'simulations/final-chip-pixel-map.json').read_text());audit=json.loads((B/'audit.json').read_text());assert mp['source_sha256']==audit['reference_sha256'] and audit['device_records_match']
D=R/'build/functional-camera'/(f'{args.stage}-{args.step_ns:g}ns'+('-gear' if args.method=='gear' else ''));D.mkdir(parents=True,exist_ok=True);assert not (D/'result.json').exists(), 'Refuse to overwrite existing run'
if args.stage=='op':model=(F/'stock-model.spice').read_text()
else:
 model=(F/'frozen-model.spice').read_text();assert json.loads((F/'frozen-model.json').read_text())['op_complete']
(D/'model.spice').write_text(model)
template=(R/'circuits/bias-scan-template.spice').read_text();delay=.0012
lines=['Final filled 3x3 normal-operation candidate; no startup qualification', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice']
lib='/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice'
lines += [f'.lib {lib} {c}' for c in ['typical','diode_typical','res_typical','moscap_typical']]
lines += ['.temp 27','.options gmin=1e-17 reltol=1e-6 abstol=1e-12 chgtol=1e-16 trtol=3 method=trap','.include model.spice','Vsource RAW 0 3.3','Rsupply RAW VDD 2','Vresetdrive RESETDRV GND 2','Rresetdrive RESETDRV PAD_VRESET 1','Rbias VDD PAD_BIAS 5.1Meg','Rpref PAD_PREF GND 49.9k','Cbias_board PAD_BIAS GND 1p','Cpref_board PAD_PREF GND 1p']
def value(v):
 m=re.fullmatch(r'([\d.eE+-]+)([a-zA-Z]*)',v);return float(m[1])*{'':1,'n':1e-9,'u':1e-6,'m':1e-3}[m[2]]
for l in template.splitlines():
 m=re.fullmatch(r'(Vr[012]) (RST[012]) 0 PWL\((.*)\)',l)
 if m:
  name,node,s=m.groups();p=list(map(float,s.split()));q=[]
  for t,v in zip(p[::2],p[1::2]):q.extend([f'{t+delay if t else 0:.12g}',f'{v/3.3:.12g}'])
  lines += [f'{name} CTL_{node} 0 PWL('+ ' '.join(q)+')',f'Bdrive_{node} DRIVE_{node} GND V=V(CTL_{node})*V(VDD,GND)',f'Rdrive_{node} DRIVE_{node} PAD_{node} 100',f'Rpull_{node} PAD_{node} VDD 100k']
 m=re.fullmatch(r'(Vs[012]|Vsel[012]) ((?:ROW|SEL)[012]) 0 PULSE\((.*)\)',l)
 if m:
  name,node,s=m.groups();q=s.split();q[1]='1';q[2]=f'{value(q[2])+delay:.12g}'
  lines += [f'{name} CTL_{node} 0 PULSE('+ ' '.join(q)+')',f'Bdrive_{node} DRIVE_{node} GND V=V(CTL_{node})*V(VDD,GND)',f'Rdrive_{node} DRIVE_{node} PAD_{node} 100',f'Rpull_{node} PAD_{node} GND 100k']
 m=re.fullmatch(r'(VACQ|VRSTADC) (ACQ|RSTADC) 0 PWL\((.*)\)',l)
 if m:
  name,node,s=m.groups();p=list(map(float,s.split()));q=[]
  for t,v in zip(p[::2],p[1::2]):q.extend([f'{t+delay if t else 0:.12g}',f'{v:.12g}'])
  lines.append(f'{name} {node} 0 PWL('+ ' '.join(q)+')')
pattern=[[0,80,240],[240,0,80],[80,240,0]]
for px in mp['pixels']:
 i,j=px['row'],px['column'];lines.append(f'Ilight{i}{j} {px["sense"]} GND {pattern[i][j]}p')
# External fast sample/hold regression fixture, not an ADS1115 or complete PCB model.
lines += ['Rbond PAD_BUF BOND 1','Lbond BOND ADC_PAD 5n','Cexternal ADC_PAD GND 1p','Riso ADC_PAD ADCIN 100','Cboard ADCIN GND 100p','Rinput ADCIN GND 1Meg','Csample HOLD GND 20p','Bsample ADCIN HOLD I=V(ADCIN,HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(ACQ)-1.65)/0.1)))','Bsample_reset HOLD GND I=V(HOLD,GND)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(RSTADC)-1.65)/0.1)))']
stop={'op':0,'frame':.00425,'three-frames':.01025}[args.stage]
# Initial guesses only: these unused protected pads have no external DC drive.
# .nodeset is released for the final OP solution; it adds no circuit load.
lines += ['.nodeset V(NC_P10)=1.65 V(NC_P11)=1.65 V(NC_P12)=1.65 V(NC_P15)=1.65 V(VDD)=3.3']
vectors=['v(VDD,GND)','v(PAD_BIAS,GND)','v(PAD_PREF,GND)','v(sensor_3x3_0.OUT,GND)','v(PAD_BUF,GND)','v(ADCIN,GND)','v(HOLD,GND)','i(Vsource)']+[f'v({p["sense"]},GND)' for p in mp['pixels']]
vectors=[v.replace(',GND)',')') for v in vectors]
base_vector_count=len(vectors)
assert all(b=='GND' for a,b in capinfo['pairs'])
vectors += [f'v({a})' for a,b in capinfo['pairs']]
assert 'sensor_3x3_0.OUT' in model
lines += ['.control','set klu','set num_threads=1','set numdgt=15','set wr_singlescale','set wr_vecnames','save '+' '.join(vectors),('op' if args.stage=='op' else f'tran {args.step_ns:g}n {stop:.12g} 0 {args.step_ns:g}n'),'wrdata tran.dat '+' '.join(vectors),'quit','.endc','.end']
s='\n'.join(lines).replace('method=trap',f'method={args.method}')+'\n';(D/'test.spice').write_text(s);(D/'tran.dat').unlink(missing_ok=True);start=time.monotonic();err=None;summary=None
try:
 with (D/'ngspice.log').open('w') as f:p=subprocess.run(['ngspice','-b','test.spice'],cwd=D,stdout=f,stderr=subprocess.STDOUT,timeout=1200,env={**os.environ,'SPICE_USERINIT_DIR':str(P/'init')})
 log=(D/'ngspice.log').read_text();assert p.returncode==0 and not re.search(r'aborted|timestep too small|^Error',log,re.I|re.M)
 z=np.loadtxt(D/'tran.dat',skiprows=1,ndmin=2);assert np.isfinite(z).all() and z[-1,0]>=stop-1e-12
 summary=dict(base_vector_count=base_vector_count,points=len(z),end_s=float(z[-1,0]),last_values=z[-1,1:].tolist(),vectors=vectors)
except Exception as e:
 err=repr(e)
 if (D/'ngspice.log').exists():
  err+='; '+'; '.join(re.findall(r'^.*(?:aborted|timestep too small|^Error).*$',(D/'ngspice.log').read_text(),re.I|re.M))
r=dict(stage=args.stage,method=args.method,completed=err is None,error=err,seconds=time.monotonic()-start,timeout_s=1200,summary=summary,step_ns=args.step_ns,deck_sha256=hashlib.sha256(s.encode()).hexdigest(),source_model_sha256=red['output_sha256'],candidate_sha256=hashlib.sha256((D/'model.spice').read_bytes()).hexdigest(),scope='Normal operation at settled nominal supply; MOS capacitance frozen at stock-model operating point, all other devices retained. Final-layout lumped wiring C; no distributed wire R, no startup/ESD/PVT/ADS1115 qualification. In-run capacitor range validation required.',accepted_full_chip=False)
(D/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
