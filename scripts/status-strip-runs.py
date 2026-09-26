"""Read strip-run progress without loading binary waveforms or modifying evidence."""
import argparse
import json
from pathlib import Path
import re

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('patterns',nargs='*',default=['build/array-strip-capture40-*20260924',
                                          'build/array-strip-vntol9-*20260924'])
a=p.parse_args()
roots=sorted({root for pattern in a.patterns for root in Path('.').glob(pattern)})
for root in roots:
    for deck in sorted(root.glob('r*c*/transient/test.spice')):
        result=deck.parent.parent/'result.json'
        if result.exists():
            r=json.loads(result.read_text())
            status='COMPLETE' if r['completed'] else 'TIMEOUT' if r['execution'].get('timed_out') else 'INCOMPLETE'
            print(f'{root.name}/{result.parent.name}: {status}'
                  +(f", error {r['max_tracking_error_V']*1e6:.3f} uV" if 'max_tracking_error_V' in r else ''))
            continue
        log=deck.parent/'ngspice.log'
        if not log.exists():continue
        with log.open('rb') as stream:
            stream.seek(max(0,log.stat().st_size-4096))
            tail=stream.read().decode(errors='replace')
        progress=re.findall(r'Reference value\s*:\s*([\deE+.-]+)',tail)
        stop=re.search(r'(?m)^\.tran\s+\S+\s+(\S+)',deck.read_text())
        state='STOPPED' if (root/'stopped-reason.json').exists() else 'NO RESULT YET'
        detail=f'last logged time {float(progress[-1])*1e3:.3f} ms / {float(stop[1])*1e3:.3f} ms' if progress and stop else 'initial solve or no transient progress in log tail'
        print(f'{root.name}/{deck.parent.parent.name}: {state}; {detail}')
