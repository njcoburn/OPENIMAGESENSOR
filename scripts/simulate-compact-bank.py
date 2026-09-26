"""Bounded capture and multiplexed readout screen for a compact shared bank.

Capture reference freezes the local diode voltage just before capture opens.
Output references separately freeze the sampled storage voltage. The fixture
has physical shared reference MOS, external bias resistors, finite behavioral
drivers and an external ADC load. Each pixel is frozen in the DC controls.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
PDK=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')


def readout_schedule(columns):
    """Keep the two-column timing, delaying the second scan for a full bank."""
    if not 2 <= columns <= 64:
        raise ValueError('The compact bank supports 2 through 64 columns')
    first = .00141
    period = 20e-6
    late = max(.00267, first + columns * period)
    slots = [(name, c, start + c * period)
             for name, start in [('first', first), ('last', late)]
             for c in range(columns)]
    return slots, late + (columns - 1) * period + 30e-6


def main():
    import numpy as np
    spec=importlib.util.spec_from_file_location('trace',ROOT/'scripts/diagnose-capture-transient.py')
    trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--model',default='rc-port');p.add_argument('--temperature',type=float,default=27)
    p.add_argument('--step-ns',type=float,default=100);p.add_argument('--lights-pa',default='0,240')
    p.add_argument('--timeout',type=float,default=120);p.add_argument('--transient-only',action='store_true')
    a=p.parse_args();assert a.step_ns>0 and a.timeout>0
    layout=a.layout.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'trace-reader.py').write_bytes((ROOT/'scripts/diagnose-capture-transient.py').read_bytes())
    meta=json.loads((layout/'verification.json').read_text());assert meta['direct_and_resistor_collapsed_lvs']
    source=layout/(a.model+'.spice')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['hashes'][source.name]
    model=source.read_text().replace('.subckt reference ','.subckt tile ').replace('.ends reference','.ends tile')
    (out/'tile.spice').write_text(model)
    (out/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    ports=meta['ports'];nc=meta['columns']
    lights=[float(v) for v in a.lights_pa.split(',')];assert len(lights)==nc and all(v>=0 for v in lights)
    slots,stop=readout_schedule(nc)
    roles=meta['pixel_roles'] if a.model!='reference' else {str(c):dict(sense=f'SENSE{c}',anode='GND',vdd='VDD') for c in range(nc)}
    def node(n):return '0' if n=='GND' else n if n in ports else 'xtile.'+n
    pixels=[(node(roles[str(c)]['sense']),node(roles[str(c)]['anode'])) for c in range(nc)]
    base=['Compact shared pixel/capture bank',f'.include {PDK}/design.ngspice',
          f'.lib {PDK}/sm141064.ngspice typical',f'.lib {PDK}/sm141064.ngspice diode_typical',
          f'.lib {PDK}/sm141064.ngspice mimcap_typical',f'.include {out}/tile.spice',
          f'.temp {a.temperature:g}',
          '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2',
          'Vsource RAW 0 3.3','Rsupply RAW VDD 2','Bresetdrive VRESET 0 I=(V(VRESET)-2)/1',
          'Xtile '+' '.join('0' if n=='GND' else n for n in ports)+' tile',
          'Rbias VDD BIAS 500k','Cbias BIAS 0 1p',
          'Rpref PREF 0 12.4k','Cpref PREF 0 1p',
          'Cbus BUF 0 1p','Rbus BUF 0 1T',
          'Rbond BUF BOND 1','Lbond BOND ADC_PAD 5n','Cexternal ADC_PAD 0 1p',
          'Riso ADC_PAD ADCIN 100','Cboard ADCIN 0 100p','Rinput ADCIN 0 1Meg','Csample HOLD 0 20p',
          'Bsample ADCIN HOLD I=V(ADCIN,HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(ACQ)-1.65)/0.1)))',
          'Bsample_reset HOLD 0 I=V(HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(RSTADC)-1.65)/0.1)))']
    for name in ['RST0','ROW0']+[f'SEL{c}' for c in range(nc)]:
        base += [f'Bdrive_{name} {name} 0 I=(V({name})-V(CTL_{name})*V(VDD))/100',
                 f'Rpull_{name} {name} '+('VDD' if name=='RST0' else '0')+' 100k']
    base += ['Bcapture SC 0 I=(V(SC)-V(CTL_SC)*V(VDD))/100',
             'Bcapture_inv SCB 0 I=(V(SCB)-(1-V(CTL_SC))*V(VDD))/100']
    base += [f'Bselinv{c} SELB{c} 0 I=(V(SELB{c})-(1-V(CTL_SEL{c}))*V(VDD))/100' for c in range(nc)]
    controls=dict(RST0='PWL(0 1 220u 1 220.01u 0 1.403m 0 1.40301m 1)',
                  ROW0='PWL(0 0 1.2m 0 1.20001m 1 1.402m 1 1.40201m 0)',
                  SC='PWL(0 1 1.4m 1 1.40001m 0)')
    def pwl(points):return 'PWL('+' '.join(f'{t:.12g} {v:g}' for t,v in points)+')'
    for c in range(nc):
        points=[(0,0)]
        for _,col,start in slots:
            if col==c:points += [(start,0),(start+1e-8,1),(start+16e-6,1),(start+16.01e-6,0)]
        controls[f'SEL{c}']=pwl(points)
    acq=[(0,0)];reset=[(0,3.3)]
    for _,_,start in slots:
        acq += [(start+2e-6,0),(start+2.01e-6,3.3),(start+12e-6,3.3),(start+12.01e-6,0)]
        reset += [(start+1e-6,3.3),(start+1.01e-6,0),(start+15e-6,0),(start+15.01e-6,3.3)]
    adc=['Vacq ACQ 0 '+pwl(acq),'Vrst_adc RSTADC 0 '+pwl(reset)]
    saved=['VDD','BIAS','PREF','RST0','ROW0','SC','SCB','BUF','ADCIN','HOLD','ACQ','RSTADC']
    saved += [f'{n}{c}' for c in range(nc) for n in ['SEL','SELB','COL','STORE','CBUF']]
    saved += list(dict.fromkeys(n for pair in pixels for n in pair))
    saves=list(dict.fromkeys('v('+n.lower()+')' for n in saved if n!='0'))
    def control_lines(values):return [f'Vctl_{name} CTL_{name} 0 {value}' for name,value in values.items()]
    def deck(body,analysis):
        return '\n'.join(body+['.save '+' '.join(saves),*analysis[:1],'.control','unset klu','set num_threads=1','set filetype=binary',*analysis[1:],'quit','.endc','.end'])+'\n'
    def execute(name,text,dc=False):
        d=out/name;d.mkdir();(d/'test.spice').write_text(text)
        started=time.monotonic();expired=False
        with (d/'ngspice.log').open('w') as handle:
            try:
                result=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=handle,stderr=subprocess.STDOUT,
                    env={**os.environ,'SPICE_USERINIT_DIR':str(out),'OMP_NUM_THREADS':'1'},timeout=a.timeout)
                code=result.returncode
            except subprocess.TimeoutExpired:expired=True;code=None
        log=(d/'ngspice.log').read_text()
        errors=[line for line in log.splitlines() if re.search(r'timestep too small|aborted|^Error|no such command',line,re.I)]
        ix,data=trace.trace(d/('op.raw' if dc else 'stream.raw'))
        complete=not expired and code==0 and not errors and data is not None and len(data)>0 and bool(np.isfinite(data).all())
        if complete:
            complete=bool(len(data)==1) if dc else bool(np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-stop)<1e-12)
        record=dict(completed=complete,seconds=time.monotonic()-started,timed_out=expired,returncode=code,
                    errors=errors,points=len(data) if data is not None else 0,
                    transient_fallback='Transient op started' in log,deck_sha256=hashlib.sha256(text.encode()).hexdigest())
        (d/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
        return record,ix,data
    body=base+[f'Ilight{c} {sense} {anode} {lights[c]:g}p' for c,(sense,anode) in enumerate(pixels)]+control_lines(controls)+adc
    transient,ix,data=execute('transient',deck(body,[f'.tran {a.step_ns:g}n {stop:.12g} 0 {a.step_ns:g}n','run stream.raw']))
    report=dict(scope=__doc__,model=a.model,temperature_C=a.temperature,lights_pA=lights,columns=nc,stop_s=stop,
                step_ns=a.step_ns,model_sha256=hashlib.sha256(model.encode()).hexdigest(),
                layout_gds_sha256=meta['gds_sha256'],transient=transient,completed=False,
                readout_slots=[dict(slot=name,column=c,start_s=start) for name,c,start in slots],
                fixture='One capture; pixel deselected at 1.402 ms and reset at 1.403 ms; first/late output slots.',
                references_requested=not a.transient_only)
    def publish():
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    if not transient['completed']:publish();raise SystemExit(1)
    assert np.max(np.diff(data[:,0]))<=a.step_ns*1e-9*1.001
    def at(n,t):return 0. if n=='0' else float(np.interp(t,data[:,0],data[:,ix['v('+n.lower()+')']]))
    captured=.0014-1e-9
    report['capture_state']={n:at(n,captured) for n in ['VDD']+[f'{n}{c}' for c in range(nc) for n in ['COL','STORE']]+[n for pair in pixels for n in pair]}
    samples=[]
    for slot,c,start in slots:
        t=start+11.999e-6
        values={n:at(n,t) for n in saved}
        assert values['SC']<.01 and values['SCB']>3 and values[f'SEL{c}']>3 and values[f'SELB{c}']<.01
        assert values['ROW0']<.01 and values['RST0']>3
        assert all(values[f'SEL{other}']<.01 and values[f'SELB{other}']>3 for other in range(nc) if other!=c)
        samples.append(dict(slot=slot,column=c,time_s=t,values=values))
    report['samples']=samples
    report['storage_reset_window_change_V']=[at(f'STORE{c}',.001405)-at(f'STORE{c}',.0014025) for c in range(nc)]
    if not a.transient_only:
        def reference(name,values,t,stores=False):
            fixture=base.copy()
            for c,(sense,anode) in enumerate(pixels):
                voltage=at(sense,t)-at(anode,t)
                fixture.append(f'Bsense{c} {sense} {anode} I=(V({sense},{anode})-({voltage:.17g}))/1')
                if stores:fixture.append(f'Bstore{c} STORE{c} 0 I=(V(STORE{c})-({at(f"STORE{c}",t):.17g}))/1')
            fixture+=control_lines(values)+['Vacq ACQ 0 3.3','Vrst_adc RSTADC 0 0']
            execution,ri,rd=execute(name,deck(fixture,['','optran 1 1 1 100n 400u 0','op','write op.raw']),dc=True)
            if not execution['completed']:
                report['reference_failure']=dict(name=name,execution=execution);publish();raise RuntimeError(name)
            measured=['BUF','ADCIN','HOLD','VDD']+[f'{n}{c}' for c in range(nc) for n in ['COL','STORE']]
            return dict(execution=execution,values={n:float(rd[0,ri['v('+n.lower()+')']]) for n in measured})
        captures=[]
        for c in range(nc):
            values=dict(RST0=0,ROW0=1,SC=1,**{f'SEL{i}':int(i==c) for i in range(nc)})
            captures.append(reference(f'capture{c}-reference',values,captured))
        report['capture_references']=captures
        for sample in samples:
            t=sample['time_s'];v=sample['values'];c=sample['column']
            values=dict(RST0=1,ROW0=0,SC=0,**{f'SEL{i}':int(i==c) for i in range(nc)})
            output=reference(f'{sample["slot"]}{c}-output-reference',values,t,stores=True)
            sample.update(output_reference=output,
                          output_tracking_error_V=v['HOLD']-output['values']['HOLD'],
                          total_capture_readout_error_V=v['HOLD']-captures[c]['values']['HOLD'],
                          storage_capture_error_V=v[f'STORE{c}']-captures[c]['values'][f'STORE{c}'])
        report['max_output_tracking_error_V']=max(abs(s['output_tracking_error_V']) for s in samples)
        report['max_total_capture_readout_error_V']=max(abs(s['total_capture_readout_error_V']) for s in samples)
        report['tracking_pass']=report['max_output_tracking_error_V']<500e-6
        report['capture_readout_pass']=report['max_total_capture_readout_error_V']<500e-6
    report['completed']=True
    publish()


if __name__=='__main__':main()
