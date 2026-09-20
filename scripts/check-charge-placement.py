"""Nominal coupon AC/load-step comparison for two explicit lumped-C placements."""
from pathlib import Path
import json,subprocess,concurrent.futures,argparse,os,re
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced'
parser=argparse.ArgumentParser();parser.add_argument('--sparse-corner',action='store_true');parser.add_argument('--flat-corner',action='store_true');parser.add_argument('--practical-corner',action='store_true');args=parser.parse_args();prefix='practical-' if args.practical_corner else ('flat-' if args.flat_corner else ('sparse-' if args.sparse_corner else ''));model_prefix='sparse-' if args.sparse_corner else ''
def run(job):
 case,mode=job;d=B/case/(prefix+mode);d.mkdir(exist_ok=True);model=(B/case/f'{model_prefix}{mode}.spice').read_text();ports=next(s.split()[2:] for s in model.splitlines() if s.startswith('.subckt'))
 audit=json.loads((R/'build/charge-reference'/case/'audit.json').read_text());sub=audit['substrate'];extra=''
 if sub not in ports:
  model=model.replace(sub,'SUBREF').replace('.subckt coupon '+' '.join(ports),'.subckt coupon '+' '.join(ports)+' SUBREF');extra=' 0'
 (d/'model.spice').write_text(model)
 pins={'VDD_A':'feed','DVDD_A':'feed','VSS_A':'0','DVSS_A':'0','VDD_B':'vb','VSS_B':'gb','DVDD_B':'db','DVSS_B':'dg'}
 dut=f"Xdut {' '.join(pins[p] for p in ports)}{extra} coupon"
 if args.flat_corner or args.practical_corner:
  flat=[];mapping={**pins,'SUBREF':'0'}
  for line in model.splitlines():
   t=line.split()
   if not t or t[0].lower() in ['.subckt','.ends']:continue
   if t[0].startswith(('R','C')):t[1:3]=[mapping.get(n,n) for n in t[1:3]]
   elif t[0].startswith(('X','D')):
    end=next(i for i,x in enumerate(t[1:],1) if x.startswith(('nfet_','pfet_','cap_nmos_','ppolyf_','diode_')))
    t[1:end]=[mapping.get(n,n) for n in t[1:end]]
   flat.append(' '.join(t))
  (d/'model.spice').write_text('\n'.join(flat)+'\n');dut=''
 lib='/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice'
 deck=f'''Charge placement {case} {mode}: illustrative supply fixture
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib {lib} typical
.lib {lib} diode_typical
.lib {lib} res_typical
.lib {lib} moscap_typical
.include model.spice
.temp 27
.options gmin=1e-17 reltol=1e-6 abstol=1e-14 method=gear
Vsrc src 0 DC 3.3 AC 1
Rsource src feed 2
{dut}
Rstandby1 vb gb 100k
Rstandby2 db dg 100k
Iload1 vb gb PULSE(0 1m 1u 1n 1n 1u 10u)
Iload2 db dg PULSE(0 1m 1u 1n 1n 1u 10u)
.control
set numdgt=12
set wr_singlescale
set wr_vecnames
ac dec 20 1k 1g
let ha = v(vb)-v(gb)
let hd = v(db)-v(dg)
wrdata ac.dat real(ha) imag(ha) real(hd) imag(hd)
tran 1n 3u 0 1n
wrdata tran.dat v(vb,gb) v(db,dg)
quit
.endc
.end
'''
 if args.practical_corner:
  deck=deck.replace('reltol=1e-6 abstol=1e-14','reltol=5e-5 abstol=1e-12 chgtol=1e-16 trtol=3').replace('.control','.control\nset klu\nset num_threads=1')
 (d/'test.spice').write_text(deck)
 record={'case':case,'placement':mode}
 try:
  with (d/'ngspice.log').open('w') as log:
   p=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,text=True,timeout=180 if args.practical_corner else 120,env={**os.environ,**({'SPICE_USERINIT_DIR':str(R/'checkpoints/pad-closure/ngspice-init')} if args.practical_corner else {})})
  errors=[s for s in (d/'ngspice.log').read_text().splitlines() if re.search('aborted|timestep too small|^Error',s,re.I)]
  assert not errors,errors[-3:]
  ac=np.loadtxt(d/'ac.dat',skiprows=1,ndmin=2);tran=np.loadtxt(d/'tran.dat',skiprows=1,ndmin=2)
  assert p.returncode==0 and np.isfinite(ac).all() and np.isfinite(tran).all() and ac[-1,0]>=.999e9 and tran[-1,0]>=.999*3e-6
  record.update(completed=True,voltage_range_V=[float(np.min(tran[:,1:])),float(np.max(tran[:,1:]))],points=len(tran))
 except Exception as e:record.update(completed=False,error=str(e))
 print(record,flush=True);return record
jobs=[(c,m) for c in (['corner-full'] if (args.sparse_corner or args.flat_corner or args.practical_corner) else ['fill10-full','fill10-metal','corner-full','corner-metal']) for m in ['nominal','remote']]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:runs=list(pool.map(run,jobs))
comparisons={}
for case in dict(jobs):
 if not all(x['completed'] for x in runs if x['case']==case):continue
 a,b=[np.loadtxt(B/case/(prefix+m)/'ac.dat',skiprows=1) for m in ['nominal','remote']];assert np.allclose(a[:,0],b[:,0])
 ha=a[:,1]+1j*a[:,2];hb=b[:,1]+1j*b[:,2];da=a[:,3]+1j*a[:,4];db=b[:,3]+1j*b[:,4]
 aa,bb=[np.loadtxt(B/case/(prefix+m)/'tran.dat',skiprows=1) for m in ['nominal','remote']];times=np.unique(np.r_[aa[:,0],bb[:,0]]);dif=np.stack([np.interp(times,aa[:,0],aa[:,i])-np.interp(times,bb[:,0],bb[:,i]) for i in [1,2]],axis=1)
 comparisons[case]={'max_waveform_difference_V':float(np.max(abs(dif))),'sample_1p5us_difference_V':[float(np.interp(1.5e-6,aa[:,0],aa[:,i])-np.interp(1.5e-6,bb[:,0],bb[:,i])) for i in [1,2]],'max_transfer_difference_through_1MHz':float(max(np.max(abs(ha-hb)[a[:,0]<=1e6]),np.max(abs(da-db)[a[:,0]<=1e6]))),'max_transfer_difference_through_1GHz':float(max(np.max(abs(ha-hb)),np.max(abs(da-db))))}
result={'fixture':'27C typical, 3.3V, shared 2ohm source, two 100kohm standby loads and simultaneous 1mA/rail 1ns-rise steps. AC 1kHz–1GHz is a diagnostic sweep, not a claimed valid technology bandwidth. No package inductance.','runs':runs,'comparisons':comparisons,'scope':'Two geometric anchor placements only; not a worst-case bound or integrated camera/ADC acceptance test.'}
(B/('placement-practical.json' if args.practical_corner else ('placement-flat.json' if args.flat_corner else ('placement-sparse.json' if args.sparse_corner else 'placement.json')))).write_text(json.dumps(result,indent=2)+'\n');assert all(x['completed'] for x in runs)
