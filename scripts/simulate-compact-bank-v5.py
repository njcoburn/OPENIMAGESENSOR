"""Version 5: 12.5 us acquisition and physical series-switch node observability.

The original runner remains unchanged as an immutable evidence dependency.

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
import struct
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

ROOT=Path(__file__).resolve().parents[1]
PDK=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')


def trace_sampler(ix,data):
    """Use the same NumPy interpolation on the two bracketing saved records.

    Avoid repeatedly copying whole strided waveforms from large binary traces.
    Each sampling time's bracket is shared by all saved nodes and references.
    """
    import numpy as np
    times=np.array(data[:,0],copy=True)
    @lru_cache(maxsize=None)
    def window(t):
        i=int(np.searchsorted(times,t))
        return slice(max(0,i-1),min(len(times),i+1))
    def at(n,t):
        if n=='0':return 0.
        s=window(t)
        return float(np.interp(t,times[s],data[s,ix['v('+n.lower()+')']]))
    return at


def saved_progress(path):
    """Last fully written binary record; partial/buffered output is not progress."""
    if not path.exists():return None
    with path.open('rb') as handle:
        header=b''
        while len(header)<131072:
            line=handle.readline()
            if not line:return None
            if line==b'Binary:\n':break
            header+=line
        else:raise ValueError('Oversized SPICE header')
        fields=header.decode()
        assert 'Flags: real' in fields
        names=[line.split()[1].lower() for line in fields.split('Variables:\n')[1].splitlines() if line.strip()]
        assert names[0]=='time'
        offset=handle.tell();count=(path.stat().st_size-offset)//(8*len(names))
        if not count:return None
        handle.seek(offset+(count-1)*8*len(names))
        return struct.unpack('d',handle.read(8))[0]


def voltage_driver(line):
    """Exact Thevenin form of a linear finite-resistance behavioral driver."""
    match=re.fullmatch(r'(B(?:resetdrive|drive_\w+|capture(?:_inv)?|selinv\d+)) (\w+) 0 I=\(V\(\2\)-(.*)\)/(\d+)',line)
    if not match:return [line]
    name,node,target,resistance=match.groups()
    return [f'{name} DRIVE_{node} 0 V={target}',f'R{name[1:]} DRIVE_{node} {node} {resistance}']


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


def acquisition_timing(acquisition_us):
    """End, falling-edge end and sample offsets within the fixed 20 µs slot."""
    if acquisition_us == 10:
        return 12e-6, 12.01e-6, 11.999e-6
    if acquisition_us == 12:
        return 14e-6, 14.01e-6, 13.999e-6
    if acquisition_us == 12.5:
        return 14.5e-6, 14.51e-6, 14.499e-6
    raise ValueError('Only 10, 12 and 12.5 us acquisition are supported')


def main():
    import numpy as np
    spec=importlib.util.spec_from_file_location('trace',ROOT/'scripts/diagnose-capture-transient.py')
    trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mos-corner',choices=['typical','ss','ff','fs','sf'],default='typical')
    p.add_argument('--model',default='rc-port');p.add_argument('--temperature',type=float,default=27)
    p.add_argument('--step-ns',type=float,default=100);p.add_argument('--lights-pa',default='0,240')
    p.add_argument('--timeout',type=float,default=120);p.add_argument('--transient-only',action='store_true')
    p.add_argument('--phase',choices=['full','op','reset','capture'],default='full',
                   help='Diagnostic endpoint; non-full phases never claim readout qualification')
    p.add_argument('--solver',choices=['sparse','klu'],default='sparse')
    p.add_argument('--method',choices=['trap','gear'],default='trap')
    p.add_argument('--driver-form',choices=['current','voltage'],default='current',
                   help='Equivalent finite-resistance driver representation; requires numerical comparison')
    p.add_argument('--equivalent-bank-model',type=Path,
                   help='Resistor-only reduction; deterministically audited against the selected extracted model')
    p.add_argument('--reuse-transient',type=Path,help='Completed full run to audit and copy instead of resimulating')
    p.add_argument('--reuse-manifest',type=Path,help='Prior evidence report containing hashes of the reused run')
    p.add_argument('--reuse-references',action='store_true',help='Audit and copy completed source references; simulate missing ones')
    p.add_argument('--reference-workers',type=int,choices=range(1,9),default=1)
    p.add_argument('--reference-timeout',type=float,help='Separate per-reference watchdog; defaults to --timeout')
    p.add_argument('--acquisition-us',type=float,choices=[10,12,12.5],default=12.5)
    p.add_argument('--deck-only',action='store_true',help='Generate a diagnostic deck without running ngspice')
    p.add_argument('--save-mim-terminals',action='store_true',
                   help='Save physical storage-plate terminal voltages for ground-motion diagnosis')
    a=p.parse_args();assert a.step_ns>0 and a.timeout>0
    acquisition_end, acquisition_fall, sample_offset = acquisition_timing(a.acquisition_us)
    assert a.reference_timeout is None or a.reference_timeout > 0
    assert not a.reuse_references or a.reuse_transient, 'Reference reuse requires transient reuse'
    assert bool(a.reuse_transient)==bool(a.reuse_manifest), 'Reuse requires both source and prior manifest'
    assert not a.reuse_transient or (a.phase=='full' and not a.transient_only), 'Reuse is for full-run reference qualification'
    assert not a.reuse_transient and not a.reuse_references, 'Process runs require fresh evidence; v3 reuse remains unchanged'
    spec=importlib.util.spec_from_file_location('bank_process_common',ROOT/'scripts/bank-process-common.py')
    process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
    provenance = process.pdk_provenance(PDK)
    layout=a.layout.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'process-helper.py').write_bytes((ROOT/'scripts/bank-process-common.py').read_bytes())
    (out/'pdk-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (out/'trace-reader.py').write_bytes((ROOT/'scripts/diagnose-capture-transient.py').read_bytes())
    meta=json.loads((layout/'verification.json').read_text());assert meta['direct_and_resistor_collapsed_lvs']
    source=layout/(a.model+'.spice')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['hashes'][source.name]
    equivalent_audit=None
    if a.equivalent_bank_model:
        assert a.model!='reference', 'Reduction requires an extracted resistor network'
        helper=ROOT/'scripts/compact-bank-resistors.py'
        spec=importlib.util.spec_from_file_location('resistors',helper)
        resistors=importlib.util.module_from_spec(spec);spec.loader.exec_module(resistors)
        target=a.equivalent_bank_model.resolve()
        equivalent_audit=resistors.verify_files(source,target)
        equivalent_audit.update(source_sha256=resistors.digest(source),model_sha256=resistors.digest(target))
        (out/'resistor-reduction.py').write_bytes(helper.read_bytes())
        source=target
    model=source.read_text().replace('.subckt reference ','.subckt tile ').replace('.ends reference','.ends tile')
    (out/'tile.spice').write_text(model)
    (out/'.spiceinit').write_text('set ngbehavior=hsa\nset wnflag=1\n')
    ports=meta['ports'];nc=meta['columns']
    lights=[float(v) for v in a.lights_pa.split(',')];assert len(lights)==nc and all(v>=0 for v in lights)
    slots,stop=readout_schedule(nc)
    if a.phase=='reset':stop=.00025
    elif a.phase=='capture':stop=.001405
    roles=meta['pixel_roles'] if a.model!='reference' else {str(c):dict(sense=f'SENSE{c}',anode='GND',vdd='VDD') for c in range(nc)}
    def node(n):return '0' if n=='GND' else n if n in ports else 'xtile.'+n
    pixels=[(node(roles[str(c)]['sense']),node(roles[str(c)]['anode'])) for c in range(nc)]
    base=['Compact shared pixel/capture bank',f'.include {PDK}/design.ngspice',
          f'.lib {PDK}/sm141064.ngspice {a.mos_corner}',f'.lib {PDK}/sm141064.ngspice diode_typical',
          f'.lib {PDK}/sm141064.ngspice mimcap_typical',f'.include {out}/tile.spice',
          f'.temp {a.temperature:g}',
          f'.options gmin=1e-17 abstol=1e-16 reltol=1e-6 chgtol=1e-18 trtol=1 method={a.method} maxord=2',
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
    if a.driver_form=='voltage':
        converted=[voltage_driver(line) for line in base]
        assert sum(len(records)==2 for records in converted)==2*nc+5
        base=[record for records in converted for record in records]
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
        acq += [(start+2e-6,0),(start+2.01e-6,3.3),(start+acquisition_end,3.3),(start+acquisition_fall,0)]
        reset += [(start+1e-6,3.3),(start+1.01e-6,0),(start+15e-6,0),(start+15.01e-6,3.3)]
    adc=['Vacq ACQ 0 '+pwl(acq),'Vrst_adc RSTADC 0 '+pwl(reset)]
    saved=['VDD','BIAS','PREF','RST0','ROW0','SC','SCB','BUF','ADCIN','HOLD','ACQ','RSTADC']
    saved += [f'{n}{c}' for c in range(nc) for n in ['SEL','SELB','COL','STORE','CBUF']]
    saved += list(dict.fromkeys(n for pair in pixels for n in pair))
    if meta.get('capture_series_devices') == 3:
        assert len(meta['stack_paths']) == nc
        private=[node(n['extracted_node']) for path in meta['stack_paths'] for n in path['private_nodes']]
        assert len(private)==len(set(private))==2*nc
        saved += private
    if a.save_mim_terminals:
        plates=[line.split() for line in model.splitlines()
                if line.startswith('X') and len(line.split())>3 and line.split()[3].startswith('cap_mim_')]
        assert len(plates)==8*nc
        saved += list(dict.fromkeys(node(n) for plate in plates for n in plate[1:3]))
    saves=list(dict.fromkeys('v('+n.lower()+')' for n in saved if n!='0'))
    def control_lines(values):return [f'Vctl_{name} CTL_{name} 0 {value}' for name,value in values.items()]
    def deck(body,analysis):
        return '\n'.join(body+['.save '+' '.join(saves),*analysis[:1],'.control',
            'set klu' if a.solver=='klu' else 'unset klu','set num_threads=1','set filetype=binary',*analysis[1:],'quit','.endc','.end'])+'\n'
    def execute(name,text,dc=False):
        d=out/name;d.mkdir();(d/'test.spice').write_text(text)
        started=time.monotonic();expired=False;progress=[];next_mark=0
        watchdog = a.reference_timeout if dc and a.reference_timeout is not None else a.timeout
        marks=sorted({t for t in [0,.00022001,.00025,.00120001,.00140001,.00140301,.00141,stop] if t<=stop})
        with (d/'ngspice.log').open('w') as handle:
            with subprocess.Popen(['ngspice','-b','test.spice'],cwd=d,stdout=handle,stderr=subprocess.STDOUT,
                    env={**os.environ,'SPICE_USERINIT_DIR':str(out),'OMP_NUM_THREADS':'1'}) as process:
                while True:
                    elapsed=time.monotonic()-started
                    last=None if dc else saved_progress(d/'stream.raw')
                    while last is not None and next_mark<len(marks) and last>=marks[next_mark]-1e-12:
                        progress.append(dict(simulated_threshold_s=marks[next_mark],observed_wall_seconds=elapsed,
                                             last_saved_time_s=last));next_mark+=1
                    if process.poll() is not None:code=process.returncode;break
                    if elapsed>=watchdog:
                        expired=True;process.kill();process.wait();code=None;break
                    time.sleep(min(.25,watchdog-elapsed))
        log=(d/'ngspice.log').read_text()
        errors=[line for line in log.splitlines() if re.search(r'timestep too small|aborted|^Error|no such command',line,re.I)]
        ix,data=trace.trace(d/('op.raw' if dc else 'stream.raw'))
        complete=not expired and code==0 and not errors and data is not None and len(data)>0 and bool(np.isfinite(data).all())
        if complete:
            complete=bool(len(data)==1) if dc else bool(np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-stop)<1e-12)
        record=dict(completed=complete,seconds=time.monotonic()-started,timed_out=expired,returncode=code,
                    errors=errors,points=len(data) if data is not None else 0,
                    transient_fallback='Transient op started' in log,deck_sha256=hashlib.sha256(text.encode()).hexdigest())
        record.update(progress_observations=progress,
                      progress_scope='Wall time when buffered trace records were observed; not exact event execution times.',
                      last_complete_trace_time_s=float(data[-1,0]) if not dc and data is not None and len(data) else None)
        (d/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
        return record,ix,data
    body=base+[f'Ilight{c} {sense} {anode} {lights[c]:g}p' for c,(sense,anode) in enumerate(pixels)]+control_lines(controls)+adc
    analysis=['','op','write op.raw'] if a.phase=='op' else [f'.tran {a.step_ns:g}n {stop:.12g} 0 {a.step_ns:g}n','run stream.raw']
    if a.deck_only:
        (out/'transient').mkdir()
        (out/'transient/test.spice').write_text(deck(body,analysis))
        (out/'result.json').write_text(json.dumps(dict(deck_only=True,diagnostic_only=True,
            completed=False,electrical_accuracy_qualified=False,acquisition_us=a.acquisition_us,mos_corner=a.mos_corner,
            diode_corner='typical',mim_corner='typical',pdk_provenance=provenance,
            columns=nc,stop_s=stop),indent=2)+'\n')
        return
    reuse=None
    if a.reuse_transient:
        helper=ROOT/'scripts/compact-bank-reuse-v2.py'
        spec=importlib.util.spec_from_file_location('reuse',helper)
        reused=importlib.util.module_from_spec(spec);spec.loader.exec_module(reused)
        expected=dict(columns=nc,phase='full',solver=a.solver,method=a.method,driver_form=a.driver_form,
                      model=a.model,temperature_C=a.temperature,step_ns=a.step_ns,lights_pA=lights,
                      layout_gds_sha256=meta['gds_sha256'],stop_s=stop,
                      acquisition_us=a.acquisition_us,sample_offset_s=sample_offset,
                      readout_slots=[dict(slot=name,column=c,start_s=start) for name,c,start in slots])
        old,reuse=reused.audit(a.reuse_transient,a.reuse_manifest,ROOT,expected,deck(body,analysis),
                              out/'tile.spice',model,(out/'.spiceinit').read_text(),out/'trace-reader.py')
        # Independent copies retain the original deck, log and execution hashes.
        source_run=a.reuse_transient.resolve();(out/'transient').mkdir()
        for name in ['test.spice','execution.json','ngspice.log','stream.raw']:
            shutil.copyfile(source_run/'transient'/name,out/'transient'/name)
            assert reused.sha(out/'transient'/name)==reuse['source_hashes']['transient/'+name]
        (out/'reuse-audit.py').write_bytes(helper.read_bytes())
        (out/'reuse-audit.json').write_text(json.dumps(reuse,indent=2)+'\n')
        (out/'regenerated-transient.spice').write_text(deck(body,analysis))
        transient=old['transient'];ix,data=trace.trace(out/'transient/stream.raw')
        assert data is not None and len(data)==transient['points'] and np.isfinite(data).all()
        assert abs(data[0,0])<1e-15 and np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-stop)<1e-12
    else:transient,ix,data=execute('transient',deck(body,analysis),dc=a.phase=='op')
    report=dict(scope=__doc__,model=a.model,mos_corner=a.mos_corner,diode_corner='typical',mim_corner='typical',pdk_provenance=provenance,temperature_C=a.temperature,lights_pA=lights,columns=nc,stop_s=None if a.phase=='op' else stop,
                step_ns=a.step_ns,model_sha256=hashlib.sha256(model.encode()).hexdigest(),
                layout_gds_sha256=meta['gds_sha256'],transient=transient,completed=False,
                readout_slots=[dict(slot=name,column=c,start_s=start) for name,c,start in slots],
                fixture='One capture; pixel deselected at 1.402 ms and reset at 1.403 ms; first/late output slots.',
                references_requested=not a.transient_only and a.phase=='full',phase=a.phase,solver=a.solver,method=a.method,
                driver_form=a.driver_form,acquisition_us=a.acquisition_us,sample_offset_s=sample_offset,
                full_bank_accuracy_qualified=False,full_chip_qualified=False)
    if reuse is not None:report['transient_reuse']=reuse
    if a.reuse_references:report['reference_reuse']={}
    report['reference_workers']=a.reference_workers
    report['reference_timeout_s']=a.reference_timeout if a.reference_timeout is not None else a.timeout
    if equivalent_audit is not None:report['equivalent_model_audit']=equivalent_audit
    def publish():
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    if not transient['completed']:publish();raise SystemExit(1)
    if a.phase!='full':
        report.update(completed=True,diagnostic_only=True,electrical_accuracy_qualified=False)
        publish();return
    assert np.max(np.diff(data[:,0]))<=a.step_ns*1e-9*1.001
    at=trace_sampler(ix,data)
    captured=.0014-1e-9
    report['capture_state']={n:at(n,captured) for n in ['VDD']+[f'{n}{c}' for c in range(nc) for n in ['COL','STORE']]+[n for pair in pixels for n in pair]}
    samples=[]
    for slot,c,start in slots:
        t=start+sample_offset
        values={n:at(n,t) for n in saved}
        assert values['SC']<.01 and values['SCB']>3 and values[f'SEL{c}']>3 and values[f'SELB{c}']<.01
        assert values['ROW0']<.01 and values['RST0']>3
        assert all(values[f'SEL{other}']<.01 and values[f'SELB{other}']>3 for other in range(nc) if other!=c)
        samples.append(dict(slot=slot,column=c,time_s=t,values=values))
    report['samples']=samples
    report['storage_reset_window_change_V']=[at(f'STORE{c}',.001405)-at(f'STORE{c}',.0014025) for c in range(nc)]
    if not a.transient_only:
        report['reference_progress']=dict(completed=0,expected=3*nc)
        def reference(name,values,t,stores=False):
            fixture=base.copy()
            for c,(sense,anode) in enumerate(pixels):
                voltage=at(sense,t)-at(anode,t)
                fixture.append(f'Bsense{c} {sense} {anode} I=(V({sense},{anode})-({voltage:.17g}))/1')
                if stores:fixture.append(f'Bstore{c} STORE{c} 0 I=(V(STORE{c})-({at(f"STORE{c}",t):.17g}))/1')
            fixture+=control_lines(values)+['Vacq ACQ 0 3.3','Vrst_adc RSTADC 0 0']
            reference_text=deck(fixture,['','optran 1 1 1 100n 400u 0','op','write op.raw'])
            prior=reused.audit_reference(source_run,name,a.reuse_manifest.resolve(),ROOT,reference_text,trace) if a.reuse_references else None
            if prior is not None:
                execution,ri,rd,hashes=prior
                destination=out/name;destination.mkdir()
                for filename,digest in hashes.items():
                    shutil.copyfile(source_run/name/filename,destination/filename)
                    assert reused.sha(destination/filename)==digest
            else:
                execution,ri,rd=execute(name,reference_text,dc=True)
            if not execution['completed']:
                return dict(execution=execution,values=None)
            measured=['BUF','ADCIN','HOLD','VDD']+[f'{n}{c}' for c in range(nc) for n in ['COL','STORE']]
            record=dict(execution=execution,values={n:float(rd[0,ri['v('+n.lower()+')']]) for n in measured})
            if prior is not None:record['reused_source_hashes']=hashes
            return record
        def batch(jobs):
            results={}
            with ThreadPoolExecutor(max_workers=a.reference_workers) as pool:
                pending={pool.submit(reference,*job):job[0] for job in jobs}
                for future in as_completed(pending):
                    name=pending[future];result=future.result();results[name]=result
                    if 'reused_source_hashes' in result:report['reference_reuse'][name]=result['reused_source_hashes']
                    if not result['execution']['completed']:
                        report['reference_failure']=dict(name=name,execution=result['execution'])
                        for other in pending:other.cancel()
                        publish();raise RuntimeError(name)
                    report['reference_progress']['completed']+=1
                    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
                    print(f'Reference {report["reference_progress"]["completed"]}/{3*nc}: {name}',flush=True)
            return results
        capture_jobs=[]
        for c in range(nc):
            values=dict(RST0=0,ROW0=1,SC=1,**{f'SEL{i}':int(i==c) for i in range(nc)})
            capture_jobs.append((f'capture{c}-reference',values,captured))
        capture_results=batch(capture_jobs)
        captures=[capture_results[job[0]] for job in capture_jobs]
        report['capture_references']=captures
        output_jobs=[]
        for sample in samples:
            t=sample['time_s'];v=sample['values'];c=sample['column']
            values=dict(RST0=1,ROW0=0,SC=0,**{f'SEL{i}':int(i==c) for i in range(nc)})
            output_jobs.append((f'{sample["slot"]}{c}-output-reference',values,t,True))
        output_results=batch(output_jobs)
        for sample in samples:
            v=sample['values'];c=sample['column']
            output=output_results[f'{sample["slot"]}{c}-output-reference']
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
