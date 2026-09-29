"""Measure stored-voltage changes around the controls in a completed bank trace."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    import numpy as np
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'runner.py').write_bytes(Path(__file__).read_bytes())
    spec=importlib.util.spec_from_file_location('reader',ROOT/'scripts/diagnose-capture-transient.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    result=json.loads((a.run/'result.json').read_text())
    assert result['completed'] and result['phase']=='full'
    path=a.run/'transient/stream.raw';ix,data=reader.trace(path)
    assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    assert abs(data[-1,0]-result['stop_s'])<1e-12
    events=[('before_capture_open',.0014-1e-9),('after_capture_open',.001401),
            ('before_row_off',.001402-1e-9),('after_row_off',.0014025),
            ('before_pixel_reset',.001403-1e-9),('after_pixel_reset',.001405),
            ('before_first_select',.00141-1e-9)]
    def at(n,t):return float(np.interp(t,data[:,0],data[:,ix['v('+n.lower()+')']]))
    plates=[line.split()[1:3] for line in (a.run/'tile.spice').read_text().splitlines()
            if line.startswith('X') and len(line.split())>3 and line.split()[3].startswith('cap_mim_')]
    physical_probes=all('v(xtile.'+n.lower()+')' in ix for plate in plates for n in plate)
    columns=[]
    for c in range(result['columns']):
        samples=[s for s in result['samples'] if s['column']==c]
        times=events+[(s['slot']+'_read',s['time_s']) for s in samples]
        values=[dict(event=name,time_s=t,values={n:at(n,t) for n in
                ['VDD','BIAS','PREF','SC','SCB','ROW0','RST0',f'STORE{c}',f'COL{c}',f'CBUF{c}']}) for name,t in times]
        if physical_probes:
            local=[plate for plate in plates if re.fullmatch(f'STORE{c}(?:[.].*)?',plate[0])]
            assert len(local)==8 and all(n.startswith('GND.') for _,n in local)
            for v in values:
                for terminal,name in [(0,'mim_average_store_V'),(1,'mim_average_ground_V')]:
                    v['values'][name]=sum(at('xtile.'+plate[terminal],v['time_s']) for plate in local)/8
                v['values']['mim_average_differential_V']=v['values']['mim_average_store_V']-v['values']['mim_average_ground_V']
        stores={v['event']:v['values'][f'STORE{c}'] for v in values}
        reference=result['capture_references'][c]['values'][f'STORE{c}']
        parts=dict(pre_capture_vs_reference=stores['before_capture_open']-reference,
                   capture_open=stores['after_capture_open']-stores['before_capture_open'],
                   capture_to_row=stores['before_row_off']-stores['after_capture_open'],
                   row_off=stores['after_row_off']-stores['before_row_off'],
                   row_to_reset=stores['before_pixel_reset']-stores['after_row_off'],
                   pixel_reset=stores['after_pixel_reset']-stores['before_pixel_reset'],
                   reset_to_select=stores['before_first_select']-stores['after_pixel_reset'],
                   select_to_first_read=stores['first_read']-stores['before_first_select'],
                   first_to_late_read=stores['last_read']-stores['first_read'])
        assert abs(sum(parts.values())-(stores['last_read']-reference))<1e-14
        columns.append(dict(column=c,light_pA=result['lights_pA'][c],events=values,
                            store_changes_uV={k:v*1e6 for k,v in parts.items()}))
    files=[path,a.run/'result.json',a.run/'tile.spice',a.out/'runner.py',ROOT/'scripts/diagnose-capture-transient.py']
    hashes={str(f.resolve().relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    report=dict(scope=__doc__,source=str(a.run),columns=columns,physical_mim_probes=physical_probes,evidence_hashes=hashes,
                limits='Port voltages around finite time windows; correlated events do not establish causation or a layout fix.')
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([dict(column=c['column'],**c['store_changes_uV']) for c in columns],indent=2))


if __name__=='__main__':main()
