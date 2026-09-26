"""Bounded matched-terminal test of a physical capture column.

Three input levels, two device temperatures, first/last readout slots and step
refinement. Inputs and supply are controlled fixture terminals, not a pixel row.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import subprocess
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
PDK=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')


def raw(path):
    with path.open('rb') as f:
        lines=[]
        while True:
            line=f.readline()
            assert line, 'Incomplete raw header'
            if line==b'Binary:\n':break
            lines.append(line)
        offset=f.tell()
    header=b''.join(lines).decode();assert 'Flags: real' in header
    names=[line.split()[1].lower() for line in header.split('Variables:\n')[1].splitlines() if line.strip()]
    data=np.fromfile(path,dtype=np.float64,offset=offset).reshape(-1,len(names))
    assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    assert data[-1,0]>=.0027-1e-12
    return {n:i for i,n in enumerate(names)},data


def case(out,models,temp,level,step,method,fixed_bias):
    d=out/f'{temp}-{level:g}-{step}';d.mkdir()
    lines=['Physical capture column matched-terminal fixture',
        f'.include {PDK}/design.ngspice',f'.lib {PDK}/sm141064.ngspice typical',
        f'.lib {PDK}/sm141064.ngspice mimcap_typical',
        f'.temp {temp}',
        f'.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method={method} maxord=2',
        'Vdd VDD 0 3.3','Rbias VDD BIAS 500k','Cbias BIAS 0 1p',
        'Xref BIAS BIAS 0 0 nfet_03v3 w=2u l=2u ad=0.88p as=0.88p pd=4.88u ps=4.88u',
        'Rpref PREF 0 12.4k','Cpref PREF 0 1p',
        'Xpref PREF PREF VDD VDD pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
        f'Vcol COL 0 PWL(0 2 1.2m 2 1.21m {level:g} 2.7m {level:g})',
        'Vsc CTLSC 0 PWL(0 1 1.4m 1 1.40001m 0)',
        'Vsel CTLSEL 0 PWL(0 0 1.41m 0 1.41001m 1 1.426m 1 1.42601m 0 2.67m 0 2.67001m 1 2.686m 1 2.68601m 0)',
        'Vacq ACQ 0 PWL(0 0 1.412m 0 1.41201m 3.3 1.422m 3.3 1.42201m 0 2.672m 0 2.67201m 3.3 2.682m 3.3 2.68201m 0)',
        'Vreset RSTADC 0 PWL(0 3.3 1.411m 3.3 1.41101m 0 1.425m 0 1.42501m 3.3 2.671m 3.3 2.67101m 0 2.685m 0 2.68501m 3.3)']
    if fixed_bias:
        # Calibrate the unchanged reference fixture independently, then impose
        # those DC terminal voltages for an isolated-column comparison.
        calibration=lines[:next(i for i,line in enumerate(lines) if line.startswith('Vcol '))]+['.control','set num_threads=1','set numdgt=15','op',
            'wrdata bias.txt v(BIAS) v(PREF)','quit','.endc','.end']
        assert any(line.startswith('Xpref ') for line in calibration)
        (d/'bias.spice').write_text('\n'.join(calibration)+'\n')
        result=subprocess.run(['ngspice','-b','bias.spice'],cwd=d,capture_output=True,text=True,timeout=30)
        (d/'bias.log').write_text(result.stdout+result.stderr);assert result.returncode==0
        values=np.loadtxt(d/'bias.txt');bias,pref=float(values[1]),float(values[3])
        assert 0<bias<3.3 and 0<pref<3.3
        lines=[line for line in lines if line.split()[0] not in ['Rbias','Cbias','Xref','Rpref','Cpref','Xpref']]
        lines += [f'Vfixedbias BIAS 0 {bias:.17g}',f'Vfixedpref PREF 0 {pref:.17g}']
    saves=['v(col)','v(bias)','v(pref)']
    for name,path in models.items():
        lines += [f'.include {path}',f'X{name} COL STORE_{name} CBUF_{name} BUF_{name} SC_{name} SCB_{name} SEL_{name} SELB_{name} BIAS PREF VDD 0 {name}',
            f'Bsc_{name} SC_{name} 0 I=(V(SC_{name})-V(CTLSC)*V(VDD))/100',
            f'Bscb_{name} SCB_{name} 0 I=(V(SCB_{name})-(1-V(CTLSC))*V(VDD))/100',
            f'Bsel_{name} SEL_{name} 0 I=(V(SEL_{name})-V(CTLSEL)*V(VDD))/100',
            f'Bselb_{name} SELB_{name} 0 I=(V(SELB_{name})-(1-V(CTLSEL))*V(VDD))/100',
            f'Rbond_{name} BUF_{name} BOND_{name} 1',f'Lbond_{name} BOND_{name} PAD_{name} 5n',
            f'Cexternal_{name} PAD_{name} 0 1p',f'Riso_{name} PAD_{name} ADC_{name} 100',
            f'Cboard_{name} ADC_{name} 0 100p',f'Rinput_{name} ADC_{name} 0 1Meg',
            f'Csample_{name} HOLD_{name} 0 20p',f'Cbus_{name} BUF_{name} 0 1p',f'Rbus_{name} BUF_{name} 0 1T',
            f'Bsample_{name} ADC_{name} HOLD_{name} I=V(ADC_{name},HOLD_{name})*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(ACQ)-1.65)/0.1)))',
            f'Breset_{name} HOLD_{name} 0 I=V(HOLD_{name})*(1e-12+(0.01-1e-12)*(0.5+0.5*tanh((V(RSTADC)-1.65)/0.1)))']
        saves += [f'v({node}_{name})' for node in ['store','cbuf','buf','hold','sc','scb','sel','selb']]
    lines += ['.save '+' '.join(saves),f'.tran {step}n 2.7m 0 {step}n',
        '.control','set klu','set num_threads=1','set filetype=binary','run stream.raw','quit','.endc','.end']
    (d/'test.spice').write_text('\n'.join(lines)+'\n')
    start=time.monotonic()
    with (d/'ngspice.log').open('w') as log:
        result=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=240)
    assert result.returncode==0,(d,result.returncode)
    ix,data=raw(d/'stream.raw');t=data[:,0]
    sample={}
    for slot,when in [('first',.0014215),('last',.0026815)]:
        sample[slot]={name:{node:float(np.interp(when,t,data[:,ix[f'v({node}_{name})']])) for node in ['store','cbuf','buf','hold','sc','scb','sel','selb']} for name in models}
        for values in sample[slot].values():
            assert values['sc']<.01 and values['scb']>3.29
            assert values['sel']>3.29 and values['selb']<.01
    report=dict(temperature_C=temp,input_V=level,max_step_ns=step,stop_s=float(t[-1]),points=len(t),
        seconds=time.monotonic()-start,samples=sample,
        source_sha256=hashlib.sha256((d/'test.spice').read_bytes()).hexdigest())
    (d/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{d.name}: complete in {report["seconds"]:.1f}s',flush=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--extraction',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--levels',type=float,nargs='+',default=[1.2,1.6,2.0])
    p.add_argument('--temperatures',type=int,nargs='+',default=[27,125])
    p.add_argument('--steps',type=int,nargs='+',default=[100,50])
    p.add_argument('--method',choices=['trap','gear'],default='gear')
    p.add_argument('--fixed-bias',action='store_true',help='Impose independently calibrated DC BIAS/PREF terminal voltages; excludes reference dynamics.')
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    models={}
    for name,source,sub in [('rc',a.extraction/'rc-port.spice','flat'),('rcfar',a.extraction/'rc-far.spice','flat'),('physical',a.extraction/'reference.spice','reference')]:
        text=source.read_text().replace('.subckt '+sub+' ','.subckt '+name+' ').replace('.ends '+sub,'.ends '+name)
        models[name]=out/(name+'.spice');models[name].write_text(text)
    text=models['physical'].read_text().replace('.subckt physical ','.subckt ideal ').replace('.ends physical','.ends ideal')
    lines=[line for line in text.splitlines() if not line.startswith('Xplate')]
    lines.insert(-1,'Cstore STORE GND 40p')
    models['ideal']=out/'ideal.spice';models['ideal'].write_text('\n'.join(lines)+'\n')
    jobs=[(temp,level,step) for temp in a.temperatures for level in a.levels for step in a.steps]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(lambda job:case(out,models,*job,a.method,a.fixed_bias),jobs))
    comparisons=[]
    for temp in a.temperatures:
        for level in a.levels:
            runs=[r for r in results if r['temperature_C']==temp and r['input_V']==level]
            best=min(runs,key=lambda r:r['max_step_ns'])
            for slot in ('first','last'):
                values=best['samples'][slot]
                comparisons.append(dict(temperature_C=temp,input_V=level,slot=slot,
                    rc_minus_ideal_hold_V=values['rc']['hold']-values['ideal']['hold'],
                    rc_minus_physical_hold_V=values['rc']['hold']-values['physical']['hold'],
                    physical_minus_ideal_hold_V=values['physical']['hold']-values['ideal']['hold'],
                    shunt_placement_hold_V=values['rcfar']['hold']-values['rc']['hold'],
                    max_refinement_hold_V=max(abs(r['samples'][slot][name]['hold']-values[name]['hold']) for r in runs for name in models)))
    report=dict(scope=__doc__,method=a.method,fixed_bias_terminals=a.fixed_bias,results=results,comparisons=comparisons,
        max_rc_minus_ideal_hold_V=max(abs(r['rc_minus_ideal_hold_V']) for r in comparisons),
        max_rc_minus_physical_hold_V=max(abs(r['rc_minus_physical_hold_V']) for r in comparisons),
        max_refinement_hold_V=max(r['max_refinement_hold_V'] for r in comparisons),
        max_shunt_placement_hold_V=max(abs(r['shunt_placement_hold_V']) for r in comparisons),
        model_sha256={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in models.items()})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k.startswith('max_')},indent=2))


if __name__=='__main__':main()
