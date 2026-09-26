"""Collect physical-column evidence, including incomplete transient attempts."""
from pathlib import Path
import hashlib
import json
import re
import struct

ROOT=Path(__file__).resolve().parents[1]


def trace_status(path):
    if not path.exists():return None
    with path.open('rb') as stream:
        header=b''
        while True:
            line=stream.readline()
            if not line:return {'complete_header':False}
            if line==b'Binary:\n':break
            header+=line
        count=int(re.search(rb'No\. Variables:\s*(\d+)',header)[1])
        offset=stream.tell();rows=(path.stat().st_size-offset)//(8*count)
        stream.seek(offset+(rows-1)*8*count)
        last=struct.unpack('d',stream.read(8))[0] if rows else None
    return dict(complete_header=True,complete_records=rows,last_time_s=last,
                reaches_stop=last is not None and last>=.0027-1e-12)


def main():
    physical=ROOT/'build/capture-column-v2-20260925/verification.json'
    capacitor=ROOT/'build/capture-capacitance-v3-20260925/report.json'
    attempts=[]
    for path in sorted((ROOT/'build').glob('capture-column-*20260925/*/test.spice')):
        deck=path.read_text();logpath=path.parent/'ngspice.log'
        log=logpath.read_text() if logpath.exists() else ''
        trace=trace_status(path.parent/'stream.raw')
        attempts.append(dict(path=str(path.parent.relative_to(ROOT)),
            deck_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            trace=trace,explicit_abort='simulation(s) aborted' in log,
            setup_failure='section definition mim_typical not found' in log,
            integration_method=re.search(r'method=(\w+)',deck)[1],
            single_thread='set num_threads=1' in deck,
            solver='KLU' if '\nset klu\n' in deck else 'SPARSE',
            fixed_bias_terminals='Vfixedbias' in deck,
            accepted=False))
    assert attempts and not any(a['trace'] and a['trace'].get('reaches_stop') for a in attempts), 'Review any completed transient before updating report'
    report=dict(scope='First isolated physical column; physical/device-model checks pass, transient accuracy unqualified.',
        physical=json.loads(physical.read_text()),capacitor_control=json.loads(capacitor.read_text()),
        physical_pass=True,capacitor_control_pass=True,transient_qualified=False,
        timestep_qualified=False,capacitance_placement_qualified=False,
        manufacturing_option_selected=False,attempts=attempts,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [physical,capacitor]})
    (ROOT/'simulations/physical-capture-column.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'physical_pass':True,'capacitor_control_pass':True,'transient_qualified':False,'attempted_decks':len(attempts)}))


if __name__=='__main__':main()
