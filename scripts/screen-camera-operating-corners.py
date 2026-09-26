"""Bounded full-layout normal-operation load/PVT screen; never startup/full RC signoff.

Use stock nonlinear capacitors for each DC bias solve, then freeze their values
using the installed PDK equation and corner multiplier. Preserve all other chip
records. Check the approximation along each captured trajectory, and compare
samples with DC references at the captured nine-pixel charge state.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse, hashlib, json, math, os, re, runpy, shutil, subprocess, time
import numpy as np

R = Path(__file__).resolve().parents[1]
SOURCE = R/'build/shared-circuit/three-frame-reset-norton-extended-20260924'
F = R/'build/functional-pad-model'
LIB = Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice')
read_raw = runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
DEFAULT = dict(mos='typical', diode='typical', resistor='typical', moscap='typical', temp_C=27, supply_V=3.3, board_pF=100, sample_pF=20, input_ohm=1e6)
CASES = {
    'heavy-cap': dict(board_pF=470, sample_pF=100),
    'heavy-resistive': dict(input_ohm=100e3),
    'heavy-board-only': dict(board_pF=470),
    'heavy-sample-only': dict(sample_pF=100),
    'supply-low': dict(supply_V=3.0),
    'supply-high': dict(supply_V=3.6),
    'ss-hot-low': dict(mos='ss', diode='ss', resistor='ss', moscap='ss', temp_C=125, supply_V=3.0),
    'ff-cold-high': dict(mos='ff', diode='ff', resistor='ff', moscap='ff', temp_C=-40, supply_V=3.6),
    'fs-hot': dict(mos='fs', temp_C=125),
    'sf-cold': dict(mos='sf', temp_C=-40),
    'heavy-cap-slow': dict(board_pF=470, sample_pF=100, timing='slow'),
    'heavy-cap-slow-drive2': dict(board_pF=470, sample_pF=100, timing='slow', pref_ohm=24900),
    'heavy-cap-slow-drive4-terminated': dict(board_pF=470, sample_pF=100, timing='slow', pref_ohm=12400, unused_pad_shunt_ohm=100e3),
    'heavy-cap-slow-drive3': dict(board_pF=470, sample_pF=100, timing='slow', pref_ohm=16500),
    'heavy-board-slow': dict(board_pF=470, timing='slow'),
    'heavy-sample-slow': dict(sample_pF=100, timing='slow'),
    'warm-terminated': dict(unused_pad_shunt_ohm=100e3),
    'ff-cold-terminated': dict(mos='ff', diode='ff', resistor='ff', moscap='ff', temp_C=-40, supply_V=3.6, unused_pad_shunt_ohm=100e3),
    'sf-cold-terminated': dict(mos='sf', temp_C=-40, unused_pad_shunt_ohm=100e3),

}

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(4*1024*1024): h.update(chunk)
    return h.hexdigest()

def write(path, obj): path.write_text(json.dumps(obj, indent=2)+'\n')

def replace(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

def density(v): return .001107 + .00107*np.tanh(6.25*np.asarray(v)-4.1875)

def invoke(dest, deck, simulator, timeout, init):
    dest.mkdir(parents=True, exist_ok=False)
    (dest/'test.spice').write_text(deck)
    start=time.monotonic()
    with (dest/'ngspice.log').open('w') as log:
        proc=subprocess.Popen([simulator,'-b','test.spice'],cwd=dest,stdout=log,stderr=subprocess.STDOUT,
            env={**os.environ,'SPICE_USERINIT_DIR':str(init),'OMP_NUM_THREADS':'1'})
        expired=False
        try: proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            expired=True; proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    log=(dest/'ngspice.log').read_text()
    errors=[l for l in log.splitlines() if re.search(r'^Error|aborted|timestep too small',l,re.I)]
    result=dict(seconds=time.monotonic()-start,timed_out=expired,returncode=proc.returncode,solver_errors=errors,
                deck_sha256=digest(dest/'test.spice'),completed=not expired and proc.returncode==0 and not errors and 'Using KLU as Direct Linear Solver' in log)
    write(dest/'execution.json',result)
    return result

def dc_deck(base, vectors):
    return base+'\n.control\nset klu\nset num_threads=1\nset numdgt=17\nset wr_singlescale\nset wr_vecnames\nsave '+' '.join(vectors)+'\nop\nwrdata op.dat '+' '.join(vectors)+'\nquit\n.endc\n.end\n'

def read_dc(dest, vectors):
    d=np.loadtxt(dest/'op.dat',skiprows=1,ndmin=2)
    assert d.shape==(1,len(vectors)+1) and np.isfinite(d).all()
    return dict(zip(vectors,d[0,1:].tolist()))

def timing(base, profile):
    """Keep reset/illumination history; move/lengthen readout within each 1 ms row.

    Slow readout begins earlier, so charge states differ from the regression
    baseline. Its matching DC reference uses the actual captured charge state.
    The last row control ends before the next row-reset pulse starts.
    """
    assert profile in ['original','slow']
    if profile=='original':return base, dict(first_sample_s=.002185,column_slot_s=18e-6,acquisition_s=5e-6,row_select_s=.00217,row_width_s=60e-6)
    row_start=.00206;column_start=.002065;slot=50e-6;acq_start=.002075;duration=30e-6
    for r in range(3):
        base,n=re.subn(rf'^Vs{r} CTL_ROW{r} 0 PULSE\(.*\)$',f'Vs{r} CTL_ROW{r} 0 PULSE(0 1 {row_start+r*.001:.12g} 10n 10n 160u 3m)',base,flags=re.M);assert n==1
    for c in range(3):
        base,n=re.subn(rf'^Vsel{c} CTL_SEL{c} 0 PULSE\(.*\)$',f'Vsel{c} CTL_SEL{c} 0 PULSE(0 1 {column_start+c*slot:.12g} 10n 10n 46u 1m)',base,flags=re.M);assert n==1
    for source,node,offset,width in [('VACQ','ACQ',0,duration),('VRSTADC','RSTADC',-2e-6,1e-6)]:
        points=[(0.,0.)]
        for f in range(3):
            for r in range(3):
                for c in range(3):
                    t=acq_start+f*.003+r*.001+c*slot+offset
                    points += [(t,0),(t+10e-9,3.3),(t+width,3.3),(t+width+10e-9,0)]
        assert all(b[0]>a[0] for a,b in zip(points,points[1:]))
        line=f'{source} {node} 0 PWL('+ ' '.join(f'{t:.12g} {v:g}' for t,v in points)+')'
        base,n=re.subn(rf'^{source} {node} 0 PWL\(.*\)$',line,base,flags=re.M);assert n==1
    assert acq_start+2*slot+duration < row_start+160e-6 < .00225
    return base,dict(first_sample_s=acq_start+duration,column_slot_s=slot,acquisition_s=duration,row_select_s=row_start,row_width_s=160e-6)


def run_case(root, name, config, args, simulator):
    dest=root/name; dest.mkdir(exist_ok=False)
    init=dest/'init'; init.mkdir(); shutil.copyfile(SOURCE/'init/.spiceinit',init/'.spiceinit')
    capinfo=json.loads((F/'caps.json').read_text())
    stock=(F/'stock-model.spice').read_text()
    frozen_meta=json.loads((F/'frozen-model.json').read_text())
    assert hashlib.sha256(stock.encode()).hexdigest()==frozen_meta['stock_sha256']
    assert digest(SOURCE/'model.spice')==frozen_meta['frozen_sha256']
    pixels=json.loads((R/'simulations/final-chip-pixel-map.json').read_text())['pixels']
    original=(SOURCE/'test.spice').read_text()
    base=original.split('.save ')[0]
    changes=[]
    for old,new in [
        (f'{LIB} typical\n',f'{LIB} {config["mos"]}\n'),
        (f'{LIB} diode_typical\n',f'{LIB} diode_{config["diode"]}\n'),
        (f'{LIB} res_typical\n',f'{LIB} res_{config["resistor"]}\n'),
        (f'{LIB} moscap_typical\n',f'{LIB} moscap_{config["moscap"]}\n'),
        ('.temp 27\n',f'.temp {config["temp_C"]}\n'),
        ('Vsource RAW 0 3.3\n',f'Vsource RAW 0 {config["supply_V"]:g}\n'),
        ('Cboard ADCIN GND 100p\n',f'Cboard ADCIN GND {config["board_pF"]:g}p\n'),
        ('Csample HOLD GND 20p\n',f'Csample HOLD GND {config["sample_pF"]:g}p\n'),
        ('Rinput ADCIN GND 1Meg\n',f'Rinput ADCIN GND {config["input_ohm"]:g}\n')]:
        base=replace(base,old,new)
        if old!=new: changes.append(dict(original=old.strip(),replacement=new.strip()))
    if 'pref_ohm' in config:
        assert config['pref_ohm']>0
        replacement=f"Rpref PAD_PREF GND {config['pref_ohm']:.17g}\n"
        base=replace(base,'Rpref PAD_PREF GND 49.9k\n',replacement)
        changes.append(dict(original='Rpref PAD_PREF GND 49.9k',replacement=replacement.strip(),scope='Proposed external buffer-reference resistor change'))
    base, schedule=timing(base,config.get('timing','original'))
    if config.get('timing','original')!='original':changes.append(dict(timing_profile=config['timing'],schedule=schedule))
    if 'unused_pad_shunt_ohm' in config:
        resistance=config['unused_pad_shunt_ohm'];assert resistance>0
        pads=['NC_P10','NC_P11','NC_P12','NC_P15']
        base+=''.join(f'Runused_{pad} {pad} GND {resistance:.17g}\n' for pad in pads)
        changes.append(dict(external_unused_pad_termination_ohm=resistance,pads=pads,scope='Proposed external pad termination; requires corresponding physical connection before fabrication'))
    # Keep original nodeset guesses: only convergence hints, not voltage clamps.
    (dest/'stock-model.spice').write_text(stock)
    meta=dict(name=name,configuration=config,changes=changes,source_deck_sha256=digest(SOURCE/'test.spice'),
        stock_model_sha256=digest(dest/'stock-model.spice'),simulator_sha256=digest(Path(simulator)),
        init_sha256=digest(init/'.spiceinit'),frames=args.frames,max_step_ns=args.step_ns,
        completed=False,screen_pass=False,accepted_full_chip=False,schedule=schedule)
    write(dest/'result.json',meta)
    try:
        pairs=[tuple(x) for x in capinfo['pairs']]
        assert all(n=='GND' for p,n in pairs)
        vectors=[f'v({p})' for p,n in pairs]+['v(PAD_BIAS)','v(PAD_PREF)','i(Vsource)']
        biasbase=replace(base,'.include model.spice','.include ../stock-model.spice')
        op=invoke(dest/'stock-op',dc_deck(biasbase,vectors),simulator,120,init)
        assert op['completed'], 'Stock nonlinear-capacitor operating point did not complete'
        bias=read_dc(dest/'stock-op',vectors)
        scale={'typical':1.,'ff':.9,'ss':1.1}[config['moscap']]
        records=[]; replacements={}
        for c in capinfo['capacitors']:
            v=bias[f'v({c["p"]})']; cv=float(c['area_m2']*scale*density(v))
            assert math.isfinite(cv) and cv>0
            replacements[c['line']]=f'Cfreeze_{c["name"]} {c["p"]} {c["n"]} {cv:.17g}'
            records.append(dict(name=c['name'],p=c['p'],n=c['n'],area_m2=c['area_m2'],bias_V=v,frozen_F=cv))
        model='\n'.join(replacements.get(l,l) for l in stock.splitlines())+'\n'
        assert len(replacements)==1680
        assert [l for l in stock.splitlines() if l not in replacements]==[l for l in model.splitlines() if not l.startswith('Cfreeze_')]
        (dest/'model.spice').write_text(model)
        write(dest/'frozen-caps.json',dict(corner_multiplier=scale,stock_op=bias,other_records_unchanged=True,capacitors=records))
        meta['model_sha256']=digest(dest/'model.spice')
        # OP equivalence must hold after replacing nonlinear capacitors.
        frozenbase=replace(base,'.include model.spice','.include ../model.spice')
        op2=invoke(dest/'frozen-op',dc_deck(frozenbase,vectors),simulator,120,init)
        assert op2['completed'], 'Frozen operating point did not complete'
        frozenbias=read_dc(dest/'frozen-op',vectors)
        meta['stock_frozen_op_max_voltage_difference_V']=max(abs(bias[k]-frozenbias[k]) for k in vectors if k.startswith('v('))
        assert meta['stock_frozen_op_max_voltage_difference_V']<1e-6, 'Stock/frozen DC bias mismatch'
        stop=.00425+(args.frames-1)*.003
        save=original.split('.save ')[1].splitlines()[0]
        deck=frozenbase+f'.save {save}\n.tran {args.step_ns:g}n {stop:.12g} 0 {args.step_ns:g}n\n.control\nset klu\nset num_threads=1\nset filetype=binary\nrun stream.raw\nquit\n.endc\n.end\n'
        print(name+': starting transient',flush=True)
        execution=invoke(dest/'transient',deck,simulator,args.timeout,init)
        meta['execution']=execution
        names,data=read_raw(dest/'transient/stream.raw')
        assert len(data)>1 and np.isfinite(data).all() and np.all(np.diff(data[:,0])>=0)
        meta.update(end_s=float(data[-1,0]),points=len(data),vectors=len(names))
        meta['completed']=bool(execution['completed'] and data[-1,0]>=stop-1e-12)
        def value(n,t):
            assert t<=data[-1,0]
            return float(np.interp(t,data[:,0],data[:,names.index('v('+n.lower()+')')]))
        ranges=[]
        for p,n in pairs:
            v=data[:,names.index('v('+p.lower()+')')]
            c0=float(density(bias[f'v({p})']))
            rel=float(np.max(np.abs(density(v)/c0-1)))
            # Also bound differential d(V*C(V))/dV, covering charge-form semantics.
            z=6.25*v-4.1875
            differential=density(v)+v*.00107*6.25*(1-np.tanh(z)**2)
            diffrel=float(np.max(np.abs(differential/c0-1)))
            ranges.append(dict(p=p,n=n,min_V=float(v.min()),max_V=float(v.max()),max_C_relative_error=rel,max_differential_C_relative_error=diffrel))
        meta['frozen_cap_bias_ranges']=ranges
        meta['cap_approximation_limit_relative']=.001
        meta['cap_approximation_pass']=all(max(x['max_C_relative_error'],x['max_differential_C_relative_error'])<.001 for x in ranges)
        samples=[]
        for frame in range(1,args.frames+1):
            for px in pixels:
                r,c=px['row'],px['column'];t=schedule['first_sample_s']+r*.001+c*schedule['column_slot_s']+(frame-1)*.003
                if t>data[-1,0]: continue
                sample=dict(frame=frame,row=r,column=c,time_s=t,photocurrent_pA=[0,80,240][(c+2*r)%3])
                sample.update({n:value(n,t) for n in ['HOLD','ADCIN','VDD','PAD_BIAS','PAD_PREF']})
                controls={f'CTL_{k}{i}':value(f'CTL_{k}{i}',t) for k in ['RST','ROW','SEL'] for i in range(3)}
                controls.update(ACQ=value('ACQ',t),RSTADC=value('RSTADC',t))
                sample['controls_valid']=all(abs(controls[f'CTL_{k}{i}']-int((k=='ROW' and i==r) or (k=='SEL' and i==c)))<1e-8 for k in ['RST','ROW','SEL'] for i in range(3)) and abs(controls['ACQ']-3.3)<1e-8 and abs(controls['RSTADC'])<1e-8
                lines=[]
                for line in frozenbase.splitlines():
                    f=line.split()
                    if f and f[0].startswith('V') and len(f)>=4 and f[1] in controls:
                        line=' '.join(f[:3])+f' DC {controls[f[1]]:.17g}'
                    lines.append(line)
                stored={p['sense']:value(p['sense'],t) for p in pixels}
                lines += [f'Vstored{i} {node} GND {v:.17g}' for i,(node,v) in enumerate(stored.items())]
                dv=['v(HOLD)','v(ADCIN)','v(VDD)','v(PAD_BIAS)','v(PAD_PREF)']+[f'v({node})' for node in stored]
                refdir=dest/f'dc-f{frame}r{r}c{c}'
                ref=invoke(refdir,dc_deck('\n'.join(lines)+'\n',dv),simulator,120,init)
                sample['dc_completed']=ref['completed']
                if ref['completed']:
                    dc=read_dc(refdir,dv)
                    assert all(abs(dc[f'v({node})']-v)<1e-10 for node,v in stored.items())
                    sample['dc']=dc
                    sample['hold_minus_dc_V']=sample['HOLD']-dc['v(HOLD)']
                    sample['adc_minus_dc_V']=sample['ADCIN']-dc['v(ADCIN)']
                    sample['bias_relative_error']=max(abs(sample[n]-dc[f'v({n})'])/max(abs(dc[f'v({n})']),1e-12) for n in ['VDD','PAD_BIAS','PAD_PREF'])
                samples.append(sample)
        meta['samples']=samples
        full=len(samples)==args.frames*9
        meta['brightness_order_pass']=full and all(x['HOLD']>y['HOLD'] for x in samples for y in samples if x['frame']==y['frame'] and x['row']==y['row'] and x['photocurrent_pA']<y['photocurrent_pA'])
        meta['controls_pass']=full and all(x['controls_valid'] for x in samples)
        refs=[x for x in samples if x['dc_completed']]
        meta['max_tracking_error_V']=max((max(abs(x['hold_minus_dc_V']),abs(x['adc_minus_dc_V'])) for x in refs),default=None)
        meta['tracking_pass']=full and len(refs)==len(samples) and meta['max_tracking_error_V']<.0005
        meta['bias_pass']=full and len(refs)==len(samples) and all(x['bias_relative_error']<.01 for x in refs)
        meta['frame_repeatability_pass']=None
        if args.frames==3 and full:
            lookup={(s['frame'],s['row'],s['column']):s for s in samples}
            meta['frame_2_to_3_max_V']=max(abs(lookup[3,r,c]['HOLD']-lookup[2,r,c]['HOLD']) for r in range(3) for c in range(3))
            meta['frame_repeatability_pass']=meta['frame_2_to_3_max_V']<50e-6
        meta['screen_pass']=all(meta[k] for k in ['completed','cap_approximation_pass','brightness_order_pass','controls_pass','tracking_pass','bias_pass']) and meta['frame_repeatability_pass'] is not False
    except Exception as exc:
        meta['error']=repr(exc)
    write(dest/'result.json',meta)
    print(json.dumps({k:meta[k] for k in ['name','completed','screen_pass','end_s','max_tracking_error_V','error'] if k in meta}),flush=True)
    return meta

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('name');p.add_argument('--cases',nargs='+',choices=list(CASES),default=['heavy-cap','heavy-resistive','supply-low','supply-high','ss-hot-low','ff-cold-high','fs-hot','sf-cold'])
    p.add_argument('--frames',type=int,choices=[1,3],default=1);p.add_argument('--step-ns',type=float,default=1000)
    p.add_argument('--timeout',type=float,default=1800);p.add_argument('--workers',type=int,default=4)
    args=p.parse_args(); assert re.fullmatch(r'[A-Za-z0-9_-]+',args.name)
    assert args.step_ns>0 and args.timeout>0 and 1<=args.workers<=4 and len(set(args.cases))==len(args.cases)
    simulator=shutil.which('ngspice');assert simulator
    # Fail if the installed MOS-cap law differs from the formula we use.
    lib=LIB.read_text(); definition=lib.split('.subckt cap_nmos_06v0 ')[1].split('.ends cap_nmos_06v0')[0]
    for text in ['cvar1=0.001107','cvar2=0.00107','cvar3=6.25','cvar4=-4.1875',"cap_nmos_06v0_corner*c_length*c_width*(cvar1+cvar2*tanh(cvar3*v(1,2)+cvar4))"]: assert text in definition
    for section,factor in [('typical','1'),('ff','0.9'),('ss','1.1')]:
        assert f'.param cap_nmos_06v0_corner={factor}\n' in lib.split(f'.lib moscap_{section}\n')[1].split('.endl')[0]
    root=R/'build/camera-operating-corners'/args.name;root.mkdir(parents=True,exist_ok=False)
    (root/'runner.py').write_bytes(Path(__file__).read_bytes())
    configurations={n:{**DEFAULT,**CASES[n]} for n in args.cases}
    meta=dict(scope=__doc__,planned_cases=configurations,frames=args.frames,step_ns=args.step_ns,timeout_s=args.timeout,
        pdk_sha256={str(f):digest(f) for f in [LIB,LIB.parent/'design.ngspice']},simulator_sha256=digest(Path(simulator)),
        script_sha256=digest(Path(__file__)),capacitor_model_definition=definition,
        engineering_screens=dict(tracking_V=.0005,frame_2_to_3_V=50e-6,bias_relative=.01,cap_approximation_relative=.001),
        missing_coverage=['Full process/diode/resistor/capacitor cross-product','Interconnect R/C corners and distributed wire resistance','Startup, noise, mismatch, optical/dark-current calibration','Real ADC conversion and external component tolerances'],cases={})
    write(root/'summary.json',meta)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(run_case,root,n,c,args,simulator):n for n,c in configurations.items()}
        for future in as_completed(futures):
            name=futures[future]
            try: meta['cases'][name]=future.result()
            except Exception as exc: meta['cases'][name]=dict(name=name,completed=False,screen_pass=False,error=repr(exc))
            write(root/'summary.json',meta)
    print('Finished bounded screen:',root,flush=True)

if __name__=='__main__':main()
