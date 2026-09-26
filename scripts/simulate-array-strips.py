"""Settling and free-integration fixtures for isolated extracted array strips.
Frozen-sense diagnostics separate interconnect/readout settling from exposure skew.
All transistor and diode models remain nonlinear; no pad or clamp model is implied.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, runpy, shutil, subprocess, time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1];PDK=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')
read_raw=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pwl(intervals,level=1):
    pts=[(0,0)]
    for t,w in intervals:pts.extend([(t,0),(t+1e-8,level),(t+w,level),(t+w+1e-8,0)])
    assert all(b[0]>a[0] for a,b in zip(pts,pts[1:])),pts
    return 'PWL('+' '.join(f'{t:.12g} {v:.12g}' for t,v in pts)+')'
def execute(d,deck,timeout,init,reuse=None):
    d.mkdir(parents=True,exist_ok=False);(d/'test.spice').write_text(deck)
    if reuse is not None:
        original=(reuse/'test.spice').read_text()
        assert original.replace(str(reuse.parent),'/CASE')==deck.replace(str(d.parent),'/CASE'),'Transient deck changed; cannot reuse trace'
        for filename in [('stream.raw' if d.name=='transient' else 'op.raw'),'ngspice.log']:os.link(reuse/filename,d/filename)
        if d.name=='transient' and (reuse.parent/'result.json').exists():
            previous=json.loads((reuse.parent/'result.json').read_text())['execution'];assert previous['completed']
        else:
            log=(reuse/'ngspice.log').read_text()
            assert re.search(r'No. of Data Rows.*ngspice-\d+ done',log,re.S)
            errors=[l for l in log.splitlines() if re.search('timestep too small|aborted|^Error',l,re.I)];assert not errors
            previous={'completed':True,'returncode':None,'timed_out':False,'errors':errors,'warnings':[l for l in log.splitlines() if 'Warning:' in l],'transient_op_fallback':'Transient op started' in log,'evidence':'Completed simulator log; raw trace finiteness and stop time independently checked on reuse.'}
        return {**previous,'deck_sha256':sha(d/'test.spice'),('reused_transient_from' if d.name=='transient' else 'reused_dc_from'):str(reuse)}
    start=time.monotonic()
    with (d/'ngspice.log').open('w') as f:
        p=subprocess.Popen(['ngspice','-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'SPICE_USERINIT_DIR':str(init),'OMP_NUM_THREADS':'1'})
        try:p.wait(timeout=timeout);timedout=False
        except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10);timedout=True
    log=(d/'ngspice.log').read_text();errors=[l for l in log.splitlines() if re.search('timestep too small|aborted|^Error',l,re.I)]
    return {'seconds':time.monotonic()-start,'timed_out':timedout,'returncode':p.returncode,'errors':errors,'warnings':[l for l in log.splitlines() if 'Warning:' in l],'transient_op_fallback':'Transient op started' in log,'deck_sha256':sha(d/'test.spice'),'completed':not timedout and p.returncode==0 and not errors}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--reuse-transients');p.add_argument('--reuse-dc');p.add_argument('--dc-workers',type=int,default=1);p.add_argument('--dc-timeout',type=float,default=120);p.add_argument('--output',required=True);p.add_argument('--cases',nargs='+',default=['r1c3','r3c1','r1c64','r64c1']);p.add_argument('--modes',nargs='+',default=['devices','capacitance','rc-port']);p.add_argument('--fixture',choices=['settling','imaging'],default='settling');p.add_argument('--step-ns',type=float,default=200);p.add_argument('--method',choices=['trap','gear'],default='trap');p.add_argument('--timeout',type=float,default=600);p.add_argument('--slot-us',type=float,default=50);p.add_argument('--reltol',type=float,default=1e-5);p.add_argument('--abstol',type=float,default=1e-16);p.add_argument('--chgtol',type=float,default=1e-18);p.add_argument('--transient-only',action='store_true');p.add_argument('--column-storage-pf',type=float);p.add_argument('--reset-after-capture',action='store_true');p.add_argument('--temperature',type=float,default=27);p.add_argument('--solver',choices=['klu','sparse'],default='klu');p.add_argument('--capture-edge-ns',type=float,default=10);p.add_argument('--capture-reference');p.add_argument('--dc-op-us',type=float,default=200);p.add_argument('--acquisition-us',type=float,default=30);p.add_argument('--pref-ohm',type=float,default=49900);p.add_argument('--pivrel',type=float);p.add_argument('--seed-storage-op',action='store_true');p.add_argument('--read-delay-us',type=float,default=0);p.add_argument('--bias-ohm',type=float,default=5.1e6);p.add_argument('--vntol',type=float);a=p.parse_args()
    source=Path(a.source).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes());init=out/'init';init.mkdir();(init/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    results=[];slot=a.slot_us*1e-6;start=.0012;width=slot-4e-6
    assert a.acquisition_us>0 and a.pref_ohm>0 and a.bias_ohm>0 and a.read_delay_us>=0
    assert not a.read_delay_us or a.column_storage_pf
    assert slot>=(a.acquisition_us+6)*1e-6 and 0<a.capture_edge_ns<1000
    solver_command='set klu' if a.solver=='klu' else 'unset klu'
    assert not (a.reset_after_capture or a.seed_storage_op) or a.column_storage_pf
    assert a.column_storage_pf is None or (a.column_storage_pf>0 and a.fixture=='imaging'), 'Column storage is an imaging architecture experiment'
    for case in a.cases:
      meta=json.loads((source/case/'extraction.json').read_text());nr=meta['rows'];nc=meta['columns'];count=nr*nc;read_start=start+(.00021+a.read_delay_us*1e-6 if a.column_storage_pf else 0);stop=read_start+count*slot+10e-6
      assert not a.column_storage_pf or nr==1, 'Column-storage fixture currently supports one row only'
      for mode in a.modes:
        d=out/f'{case}-{mode}';d.mkdir();shutil.copyfile(source/case/f'{mode}.spice',d/'array.spice');shutil.copyfile(R/'circuits/output-buffer.spice',d/'buffer.spice')
        capture_ref=json.loads(Path(a.capture_reference).read_text()) if a.capture_reference else None
        if capture_ref:assert a.column_storage_pf and capture_ref['model_sha256']==sha(d/'array.spice')
        roles=meta['roles']['rc' if mode.startswith('rc') else mode];ports=meta['ports']
        def node(n):return '0' if n=='GND' else n if n in ports else 'xarray.'+n
        base=['Extracted strip '+a.fixture,f'.include {PDK}/design.ngspice',f'.lib {PDK}/sm141064.ngspice typical',f'.lib {PDK}/sm141064.ngspice diode_typical',f'.include {d}/array.spice',f'.include {d}/buffer.spice',f'.temp {a.temperature:g}',f'.options gmin=1e-17 abstol={a.abstol:g} reltol={a.reltol:g} chgtol={a.chgtol:g} trtol=1 method='+a.method+(f' pivrel={a.pivrel:g}' if a.pivrel else '')+(f' vntol={a.vntol:g}' if a.vntol is not None else ''),'Vsource RAW 0 3.3','Rsupply RAW VDD 2','Bresetdrive VRESET 0 I=(V(VRESET)-2)/1','Xarray '+' '.join('0' if x=='GND' else x for x in ports)+' array']
        # Explicit finite-driver abstraction; peripheral wiring is not extracted.
        controls={};intervals={}
        for r in range(nr):
            intervals[f'ROW{r}']=[(start+r*nc*slot, nc*slot-2e-6+(read_start-start))]
            # Identical integration age at first sample of each row; longer rows retain skew.
            intervals[f'RST{r}']=[(start+r*nc*slot-.001,20e-6)] if a.fixture=='imaging' else []
        if a.reset_after_capture:
            intervals['ROW0']=[(start,.000202)]
            intervals['RST0'].append((start+.000203,stop-start-.000203+1e-6))
        for c in range(nc):intervals[f'SEL{c}']=[(read_start+(r*nc+c)*slot,width) for r in range(nr)]
        for name,ints in intervals.items():
            controls[name]=f'Vctl_{name} CTL_{name} 0 '+(pwl(ints) if ints else '0')
            if a.fixture=='imaging' and name.startswith('RST'):
                controls[name]=controls[name].replace(f'PWL(0 0 {ints[0][0]:.12g} 0',f'PWL(0 1 {ints[0][0]:.12g} 1')
            base += [f'Bdrive_{name} {name} 0 I=(V({name})-V(CTL_{name})*V(VDD))/100',f'Rpull_{name} {name} '+('VDD' if name.startswith('RST') else '0')+' 100k']
        held={};photocurrents={}
        for key,v in roles.items():
            r,c=map(int,key.split('_'));idx=r*nc+c;level=[1.95,1.75,1.3][idx%3];light=[0,80,240][idx%3];photocurrents[key]=light
            if a.fixture=='settling':
                held[key]=f'Bsense_{key} {node(v["sense"]) } {node(v["anode"]) } I=(V({node(v["sense"]) },{node(v["anode"]) })-{level})/1'
            else:held[key]=f'Ilight_{key} {node(v["sense"]) } {node(v["anode"]) } {light}p'
        geom='nfet_03v3 w=2u l=2u ad=0.88p as=0.88p pd=4.88u ps=4.88u'
        base+=[('Rbias VDD BIAS 5.1Meg' if a.bias_ohm==5.1e6 else f'Rbias VDD BIAS {a.bias_ohm:g}'),'Cbias BIAS 0 1p','Xref BIAS BIAS 0 0 '+geom]
        for c in range(nc):
            base += [f'Xbias{c} COL{c} BIAS 0 0 '+geom]
            if not a.column_storage_pf:base += [f'Xmux{c} OUT SEL{c} COL{c} 0 nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u']
        base+=['Cout OUT 0 1p','Rout OUT 0 1T','Xbuffer OUT BUF PREF VDD 0 output_buffer',('Rpref PREF 0 49.9k' if a.pref_ohm==49900 else f'Rpref PREF 0 {a.pref_ohm:g}'),'Cpref PREF 0 1p','Rbond BUF BOND 1','Lbond BOND ADC_PAD 5n','Cexternal ADC_PAD 0 1p','Riso ADC_PAD ADCIN 100','Cboard ADCIN 0 100p','Rinput ADCIN 0 1Meg','Csample HOLD 0 20p','Bsample ADCIN HOLD I=V(ADCIN,HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(ACQ)-1.65)/0.1)))','Bsample_reset HOLD 0 I=V(HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(RSTADC)-1.65)/0.1)))']
        if a.column_storage_pf:
            # Schematic architecture candidate: simultaneous transistor-switch capture,
            # one PMOS buffer per stored column, then transistor mux to shared ADC.
            # Explicit linear storage capacitors; no physical S/H layout qualification.
            base=[l for l in base if not l.startswith(('Cout ','Rout ','Xbuffer '))]
            base += ['Xstorage_ref PREF PREF VDD VDD pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
                     'Cbus BUF 0 1p','Rbus BUF 0 1T',
                     'Bcapture SC 0 I=(V(SC)-V(CTL_SC)*V(VDD))/100',
                     'Bcapture_inv SCB 0 I=(V(SCB)-(1-V(CTL_SC))*V(VDD))/100']
            controls['SC']='Vctl_sc CTL_SC 0 PWL(0 1 '+f'{start+.0002:.12g} 1 {start+.0002+a.capture_edge_ns*1e-9:.12g} 0)'
            for c in range(nc):
                base += [f'Cstore{c} STORE{c} 0 {a.column_storage_pf:g}p',
                         f'Bselinv{c} SELB{c} 0 I=(V(SELB{c})-(1-V(CTL_SEL{c}))*V(VDD))/100',
                         f'Xholdn{c} COL{c} SC STORE{c} 0 nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
                         f'Xholdp{c} COL{c} SCB STORE{c} VDD pfet_03v3 w=2u l=0.5u ad=0.88p as=0.88p pd=4.88u ps=4.88u',
                         f'Xstoreload{c} CBUF{c} PREF VDD VDD pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
                         f'Xstorefollow{c} 0 STORE{c} CBUF{c} VDD pfet_03v3 w=20u l=0.5u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
                         f'Xmuxn{c} BUF SEL{c} CBUF{c} 0 nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
                         f'Xmuxp{c} BUF SELB{c} CBUF{c} VDD pfet_03v3 w=2u l=0.5u ad=0.88p as=0.88p pd=4.88u ps=4.88u']
        if a.seed_storage_op:
            base += ['.nodeset v(VDD)=3.28 v(BIAS)=0.71 v(PREF)=1.9 '+ ' '.join(f'v(CBUF{c})=1.5 v(STORE{c})=0' for c in range(nc))]
        controls['ACQ']='Vacq ACQ 0 '+pwl([(read_start+i*slot+2e-6,a.acquisition_us*1e-6) for i in range(count)],3.3)
        controls['RSTADC']='Vrst_adc RSTADC 0 '+pwl([(read_start+i*slot,1e-6) for i in range(count)],3.3).replace(f'PWL(0 0 {read_start:.12g} 0',f'PWL(0 3.3 {read_start:.12g} 3.3')
        saves=['v(VDD)','v(BIAS)','v(PREF)','v(OUT)','v(BUF)','v(ADCIN)','v(HOLD)','v(ACQ)','v(RSTADC)','i(Vsource)']+[f'v(COL{c})' for c in range(nc)]
        saves += [f'v({node(n)})' for v in roles.values() for n in v.values()]
        saves += [f'v({prefix}{n})' for n in intervals for prefix in ['']]
        if a.column_storage_pf:saves.remove('v(OUT)');saves += ['v(SC)','v(SCB)']+[f'v({prefix}{c})' for c in range(nc) for prefix in ['STORE','CBUF']]
        saves=list(dict.fromkeys(x.lower() for x in saves))
        deck='\n'.join(base+list(held.values())+list(controls.values())+['.save '+' '.join(saves),f'.tran {a.step_ns}n {stop:.12g} 0 {a.step_ns}n','.control',solver_command,'set num_threads=1','set filetype=binary','run stream.raw','quit','.endc','.end'])+'\n'
        if capture_ref:
            if 'normalized_transient_sha256' in capture_ref:assert capture_ref['normalized_transient_sha256']==hashlib.sha256(deck.replace(str(d),'/CASE').encode()).hexdigest(), 'Capture target and transient fixture differ'
            (d/'capture-reference.json').write_text(json.dumps(capture_ref,indent=2)+'\n')
        result={'case':case,'mode':mode,'fixture':a.fixture,'rows':nr,'columns':nc,'step_ns':a.step_ns,'method':a.method,'slot_us':a.slot_us,'acquisition_us':a.acquisition_us,'pref_ohm':a.pref_ohm,'bias_ohm':a.bias_ohm,'read_delay_us':a.read_delay_us,'tolerances':{'reltol':a.reltol,'abstol':a.abstol,'chgtol':a.chgtol,'vntol':a.vntol if a.vntol is not None else 1e-6},'transient_only':a.transient_only,'column_storage_pF':a.column_storage_pf,'reset_after_capture':a.reset_after_capture,'temperature_C':a.temperature,'solver':a.solver,'pivrel':a.pivrel,'seed_storage_op':a.seed_storage_op,'capture_edge_ns':a.capture_edge_ns,'capture_reference':a.capture_reference,'accuracy_scope':('Total deterministic capture and readout error relative to the DC column target at the common capture state' if capture_ref else 'Output tracking relative to the actual sampled state' if not a.transient_only else 'Transient waveform only'),'dc_op_us':a.dc_op_us,'dc_timeout_s':a.dc_timeout,'capture_time_s':start+.0002 if a.column_storage_pf else None,'model_sha256':sha(d/'array.spice'),'simulator_sha256':sha(Path(shutil.which('ngspice'))),'runner_sha256':sha(out/'runner.py'),'completed':False,'samples':[]}
        result['execution']=execute(d/'transient',deck,a.timeout,init,Path(a.reuse_transients).resolve()/d.name/'transient' if a.reuse_transients else None)
        if result['execution']['completed']:
          names,data=read_raw(d/'transient/stream.raw');assert np.isfinite(data).all();assert data[-1,0]>=stop-1e-12
          def wave(n):
              n=n.lower()
              aliases={f'v(xarray.{p.lower()})':f'v({p.lower()})' for p in ports}
              n=aliases.get(n,n)
              if n in ['v(gnd)','v(0)']:return np.zeros(len(data))
              return data[:,names.index(n)]
          def at(n,t):return float(np.interp(t,data[:,0],wave(n)))
          if a.transient_only:
            for idx in range(count):
              r,c=divmod(idx,nc);v=roles[f'{r}_{c}'];t=read_start+idx*slot+(2+a.acquisition_us)*1e-6-1e-9
              result['samples'].append({'row':r,'column':c,'time_s':t,'capture':{n:at(f'v({n})',t) for n in (['VDD','BUF','ADCIN','HOLD'] if a.column_storage_pf else ['VDD','OUT','BUF','ADCIN','HOLD'])},'sense_differential_V':at(f'v({node(v["sense"])})',t)-at(f'v({node(v["anode"])})',t)})
            if a.column_storage_pf:
              for x in result['samples']:
                c=x['column'];x['storage']={'before_capture_V':at(f'v(STORE{c})',start+.0002-1e-9),'after_capture_V':at(f'v(STORE{c})',start+.000201),'at_readout_V':at(f'v(STORE{c})',x['time_s']),'column_before_capture_V':at(f'v(COL{c})',start+.0002-1e-9)}
            result.update(completed=True,end_s=float(data[-1,0]),points=len(data),qualification='Transient comparison only; no matched DC tracking screen.')
            (d/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
            print(json.dumps({k:v for k,v in result.items() if k!='samples'}),flush=True)
            continue
          dcerrors=[];samples=[];delays=[]
          def sample_one(idx):
            r,c=divmod(idx,nc);key=f'{r}_{c}';v=roles[key];edge=read_start+idx*slot;sampletime=edge+(2+a.acquisition_us)*1e-6-1e-9
            # Matched DC state: hold every sense node at its sampled local diode voltage.
            dcbase=base.copy();dccontrols=[]
            for n,ints in intervals.items():
                high=any(t<sampletime<t+w for t,w in ints)
                if a.fixture=='imaging' and n.startswith('RST'):high=high or sampletime<ints[0][0]+ints[0][1]
                dccontrols += [f'Vctl_{n} CTL_{n} 0 {int(high)}']
            dccontrols+=['Vacq ACQ 0 3.3','Vrst_adc RSTADC 0 0']
            if a.column_storage_pf:
                dccontrols += ['Vctl_sc CTL_SC 0 0']+[f'Bstorefix{cc} STORE{cc} 0 I=(V(STORE{cc})-({(capture_ref['column_targets_V'][str(cc)] if capture_ref else at(f"v(STORE{cc})",sampletime)):.16g}))/1' for cc in range(nc)]
            dcsenses=[f'Bsense_{k} {node(v2["sense"]) } {node(v2["anode"]) } I=(V({node(v2["sense"]) },{node(v2["anode"]) })-({at("v("+node(v2["sense"])+")",sampletime)-at("v("+node(v2["anode"])+")",sampletime):.16g}))/1' for k,v2 in roles.items()]
            dcdeck='\n'.join(dcbase+dcsenses+dccontrols+['.save v(HOLD) v(ADCIN) v(VDD) v(BIAS) v(PREF) i(Vsource)','.control',solver_command,'set num_threads=1','set filetype=binary',f'optran 1 1 1 100n {a.dc_op_us:g}u 0','op','write op.raw','quit','.endc','.end'])+'\n'
            previous=Path(a.reuse_dc).resolve()/d.name/f'dc-{idx:03d}' if a.reuse_dc else None
            if previous and (not (previous/'op.raw').exists() or not re.search(r'ngspice-\d+ done',(previous/'ngspice.log').read_text())):previous=None
            op=execute(d/f'dc-{idx:03d}',dcdeck,a.dc_timeout,init,previous);assert op['completed'],op
            dn,dd=read_raw(d/f'dc-{idx:03d}/op.raw');assert dd.shape==(1,len(dn)) and np.isfinite(dd).all()
            ref={n:float(dd[0,j]) for j,n in enumerate(dn)}
            capture={n:at(f'v({n})',sampletime) for n in (['VDD','BIAS','PREF','BUF','ADCIN','HOLD'] if a.column_storage_pf else ['VDD','BIAS','PREF','OUT','BUF','ADCIN','HOLD'])}
            assert abs(ref['v(hold)']-ref['v(adcin)'])<1e-8, 'DC reference retains ADC capacitor current; extend optran and cross-check'
            target=ref['v(hold)'];errs={f'{us:g}':at('v(HOLD)',edge+(2+us)*1e-6-1e-9)-target for us in [a.acquisition_us/6,a.acquisition_us/2,a.acquisition_us]}
            if a.fixture=='settling':
                expected=[1.95,1.75,1.3][idx%3]
                measured=at(f'v({node(v["sense"])})',sampletime)-at(f'v({node(v["anode"])})',sampletime)
                assert abs(expected-measured)<1e-6,(key,expected,measured)
            # Settling is only meaningful against a fixed sense state.
            settled=None
            if a.fixture=='settling':
                mask=(data[:,0]>=edge+2e-6)&(data[:,0]<=sampletime);tt=data[mask,0];ee=np.abs(wave('v(HOLD)')[mask]-target);bad=np.flatnonzero(ee>500e-6)
                if len(tt) and (not len(bad) or bad[-1]<len(tt)-1):settled=float((tt[0 if not len(bad) else bad[-1]+1]-edge-2e-6)*1e6)
            sample={'row':r,'column':c,'time_s':sampletime,'photocurrent_pA':photocurrents[key] if a.fixture=='imaging' else None,'sense_differential_V':at(f'v({node(v["sense"]) })',sampletime)-at(f'v({node(v["anode"]) })',sampletime),'capture':capture,'dc':ref,'errors_V':errs,'settled_within_500uV_after_acquisition_us':settled,'supply_current_A':-at('i(Vsource)',sampletime),'local_vdd_drop_V':capture['VDD']-at(f'v({node(v["vdd"]) })',sampletime),'local_ground_V':at(f'v({node(v["gnd"]) })',sampletime),'dc_execution':op}
            return sample
          with ThreadPoolExecutor(max_workers=a.dc_workers) as pool:samples=list(pool.map(sample_one,range(count)))
          # Gate propagation measured independently at each row's rising edge.
          for key,v in roles.items():
            r,c=map(int,key.split('_'));edge=start+r*nc*slot;target=.5*at('v(VDD)',edge+1e-6);y=wave(f'v({node(v["select_gate"]) })');mask=(data[:,0]>=edge)&(data[:,0]<edge+2e-6);inds=np.flatnonzero(mask & (y>=target));cross=None
            if len(inds):
                j=inds[0];cross=float((np.interp(target,y[j-1:j+1],data[j-1:j+1,0])-edge)*1e9)
            delays.append({'pixel':key,'gate_50pct_after_source_edge_ns':cross})
          result.update(completed=True,end_s=float(data[-1,0]),points=len(data),samples=samples,gate_delays=delays,max_tracking_error_V=max(abs(x['errors_V'][f'{a.acquisition_us:g}']) for x in samples),max_local_vdd_drop_V=max(x['local_vdd_drop_V'] for x in samples),max_local_ground_V=max(x['local_ground_V'] for x in samples),max_supply_current_A=max(x['supply_current_A'] for x in samples),min_vdd_V=float(wave('v(VDD)').min()),max_gate_50pct_ns=max(x['gate_50pct_after_source_edge_ns'] for x in delays if x['gate_50pct_after_source_edge_ns'] is not None))
          result['tracking_screen_pass']=result['max_tracking_error_V']<500e-6
          if a.fixture=='settling':
            samelevelgroups=[[x for x in samples if (x['row']*nc+x['column'])%3==i] for i in range(3)]
            result['brightness_order_correct']=all(x['capture']['HOLD']>y['capture']['HOLD'] for i in range(3) for j in range(i+1,3) for x in samelevelgroups[i] for y in samelevelgroups[j])
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ['samples','gate_delays']}),flush=True)
if __name__=='__main__':main()
