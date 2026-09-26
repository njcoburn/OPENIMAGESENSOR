"""Bounded coupled reset/capture/readout screen for a physically joined tile.

Capture reference freezes the local diode voltage just before capture opens.
Output references separately freeze the sampled storage voltage. The fixture
has schematic bias references, finite behavioral drivers and external ADC load.
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
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
PDK=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')
spec=importlib.util.spec_from_file_location('trace',ROOT/'scripts/diagnose-capture-transient.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--model',default='rc-port');p.add_argument('--temperature',type=float,default=27)
    p.add_argument('--step-ns',type=float,default=100);p.add_argument('--light-pa',type=float,default=0)
    p.add_argument('--timeout',type=float,default=120);p.add_argument('--transient-only',action='store_true')
    a=p.parse_args();assert a.step_ns>0 and a.timeout>0 and a.light_pa>=0
    layout=a.layout.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'trace-reader.py').write_bytes((ROOT/'scripts/diagnose-capture-transient.py').read_bytes())
    meta=json.loads((layout/'verification.json').read_text());assert meta['direct_and_resistor_collapsed_lvs']
    source=layout/(a.model+'.spice')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['hashes'][source.name]
    model=source.read_text().replace('.subckt reference ','.subckt tile ').replace('.ends reference','.ends tile')
    (out/'tile.spice').write_text(model)
    (out/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    ports=meta['ports']
    roles=meta['pixel_roles'] if a.model!='reference' else dict(sense='SENSE',anode='GND',vdd='VDD')
    def node(n):return '0' if n=='GND' else n if n in ports else 'xtile.'+n
    sense,anode=node(roles['sense']),node(roles['anode'])
    base=['Joined compact pixel/capture tile',f'.include {PDK}/design.ngspice',
          f'.lib {PDK}/sm141064.ngspice typical',f'.lib {PDK}/sm141064.ngspice diode_typical',
          f'.lib {PDK}/sm141064.ngspice mimcap_typical',f'.include {out}/tile.spice',
          f'.temp {a.temperature:g}',
          '.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method=trap maxord=2',
          'Vsource RAW 0 3.3','Rsupply RAW VDD 2','Bresetdrive VRESET 0 I=(V(VRESET)-2)/1',
          'Xtile '+' '.join('0' if n=='GND' else n for n in ports)+' tile',
          'Rbias VDD BIAS 500k','Cbias BIAS 0 1p',
          'Xref BIAS BIAS 0 0 nfet_03v3 w=2u l=2u ad=0.88p as=0.88p pd=4.88u ps=4.88u',
          'Rpref PREF 0 12.4k','Cpref PREF 0 1p',
          'Xstorage_ref PREF PREF VDD VDD pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
          'Cbus BUF 0 1p','Rbus BUF 0 1T',
          'Rbond BUF BOND 1','Lbond BOND ADC_PAD 5n','Cexternal ADC_PAD 0 1p',
          'Riso ADC_PAD ADCIN 100','Cboard ADCIN 0 100p','Rinput ADCIN 0 1Meg','Csample HOLD 0 20p',
          'Bsample ADCIN HOLD I=V(ADCIN,HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(ACQ)-1.65)/0.1)))',
          'Bsample_reset HOLD 0 I=V(HOLD)*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(RSTADC)-1.65)/0.1)))']
    for name in ['RST0','ROW0','SEL0']:
        base += [f'Bdrive_{name} {name} 0 I=(V({name})-V(CTL_{name})*V(VDD))/100',
                 f'Rpull_{name} {name} '+('VDD' if name=='RST0' else '0')+' 100k']
    base += ['Bcapture SC 0 I=(V(SC)-V(CTL_SC)*V(VDD))/100',
             'Bcapture_inv SCB 0 I=(V(SCB)-(1-V(CTL_SC))*V(VDD))/100',
             'Bselinv SELB0 0 I=(V(SELB0)-(1-V(CTL_SEL0))*V(VDD))/100']
    controls=dict(RST0='PWL(0 1 220u 1 220.01u 0 1.403m 0 1.40301m 1 2.7m 1)',
                  ROW0='PWL(0 0 1.2m 0 1.20001m 1 1.402m 1 1.40201m 0)',
                  SC='PWL(0 1 1.4m 1 1.40001m 0)',
                  SEL0='PWL(0 0 1.41m 0 1.41001m 1 1.426m 1 1.42601m 0 2.67m 0 2.67001m 1 2.686m 1 2.68601m 0)')
    adc=['Vacq ACQ 0 PWL(0 0 1.412m 0 1.41201m 3.3 1.422m 3.3 1.42201m 0 2.672m 0 2.67201m 3.3 2.682m 3.3 2.68201m 0)',
         'Vrst_adc RSTADC 0 PWL(0 3.3 1.411m 3.3 1.41101m 0 1.425m 0 1.42501m 3.3 2.671m 3.3 2.67101m 0 2.685m 0 2.68501m 3.3)']
    saved=['VDD','BIAS','PREF','RST0','ROW0','SC','SCB','SEL0','SELB0','COL0','STORE0','CBUF0','BUF','ADCIN','HOLD','ACQ','RSTADC',sense,anode]
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
            complete=bool(len(data)==1) if dc else bool(np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-.0027)<1e-12)
        record=dict(completed=complete,seconds=time.monotonic()-started,timed_out=expired,returncode=code,
                    errors=errors,points=len(data) if data is not None else 0,
                    transient_fallback='Transient op started' in log,deck_sha256=hashlib.sha256(text.encode()).hexdigest())
        (d/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
        return record,ix,data
    body=base+[f'Ilight {sense} {anode} {a.light_pa:g}p']+control_lines(controls)+adc
    transient,ix,data=execute('transient',deck(body,[f'.tran {a.step_ns:g}n 2.7m 0 {a.step_ns:g}n','run stream.raw']))
    report=dict(scope=__doc__,model=a.model,temperature_C=a.temperature,light_pA=a.light_pa,
                step_ns=a.step_ns,model_sha256=hashlib.sha256(model.encode()).hexdigest(),
                layout_gds_sha256=meta['gds_sha256'],transient=transient,completed=False,
                fixture='One capture; pixel deselected at 1.402 ms and reset at 1.403 ms; first/late output slots.',
                references_requested=not a.transient_only)
    def publish():
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    if not transient['completed']:publish();raise SystemExit(1)
    assert np.max(np.diff(data[:,0]))<=a.step_ns*1e-9*1.001
    def at(n,t):return 0. if n=='0' else float(np.interp(t,data[:,0],data[:,ix['v('+n.lower()+')']]))
    captured=.0014-1e-9
    report['capture_state']={n:at(n,captured) for n in ['COL0','STORE0','VDD',sense,anode]}
    samples=[]
    for slot,t in [('first',.001421999),('last',.002681999)]:
        values={n:at(n,t) for n in saved}
        assert values['SC']<.01 and values['SCB']>3 and values['SEL0']>3 and values['SELB0']<.01
        assert values['ROW0']<.01 and values['RST0']>3
        samples.append(dict(slot=slot,time_s=t,values=values))
    report['samples']=samples
    report['storage_reset_coupling_V']=at('STORE0',.001405)-at('STORE0',.0014025)
    if not a.transient_only:
        def reference(name,values,sense_voltage,store=None):
            fixture=base+[f'Bsense {sense} {anode} I=(V({sense},{anode})-({sense_voltage:.17g}))/1']
            if store is not None:fixture.append(f'Bstore STORE0 0 I=(V(STORE0)-({store:.17g}))/1')
            fixture+=control_lines(values)+['Vacq ACQ 0 3.3','Vrst_adc RSTADC 0 0']
            execution,ri,rd=execute(name,deck(fixture,['','optran 1 1 1 100n 400u 0','op','write op.raw']),dc=True)
            if not execution['completed']:
                report['reference_failure']=dict(name=name,execution=execution);publish();raise RuntimeError(name)
            return dict(execution=execution,values={n:float(rd[0,ri['v('+n.lower()+')']]) for n in ['COL0','STORE0','BUF','ADCIN','HOLD','VDD']})
        capture=reference('capture-reference',dict(RST0=0,ROW0=1,SC=1,SEL0=1),at(sense,captured)-at(anode,captured))
        report['capture_reference']=capture
        for sample in samples:
            t=sample['time_s'];v=sample['values']
            output=reference(sample['slot']+'-output-reference',dict(RST0=1,ROW0=0,SC=0,SEL0=1),at(sense,t)-at(anode,t),v['STORE0'])
            sample.update(output_reference=output,
                          output_tracking_error_V=v['HOLD']-output['values']['HOLD'],
                          total_capture_readout_error_V=v['HOLD']-capture['values']['HOLD'],
                          storage_capture_error_V=v['STORE0']-capture['values']['STORE0'])
        report['max_output_tracking_error_V']=max(abs(s['output_tracking_error_V']) for s in samples)
        report['max_total_capture_readout_error_V']=max(abs(s['total_capture_readout_error_V']) for s in samples)
        report['tracking_pass']=report['max_output_tracking_error_V']<500e-6
        report['capture_readout_pass']=report['max_total_capture_readout_error_V']<500e-6
    report['completed']=True
    publish()


if __name__=='__main__':main()
