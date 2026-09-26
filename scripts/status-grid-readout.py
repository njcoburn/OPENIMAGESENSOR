"""Read exact streamed progress and reference counts without changing evidence."""
from pathlib import Path
import argparse
import json
import re
import struct

p=argparse.ArgumentParser()
p.add_argument('root',nargs='?',type=Path,default=Path('build/grid-readout-20260924'))
a=p.parse_args()
for statusfile in sorted(a.root.glob('*-status.json')):
    status=json.loads(statusfile.read_text());name=statusfile.name.removesuffix('-status.json')
    if not re.fullmatch(r'(27|125)-(100|200)',name):continue
    d=a.root/name/'r1c64-rc-port';raw=d/'transient/stream.raw'
    detail='initial operating-point solve'
    if raw.exists():
        with raw.open('rb') as f:
            header=[]
            while True:
                line=f.readline()
                if line==b'Binary:\n' or not line:break
                header.append(line)
            if line==b'Binary:\n':
                n=int(re.search(rb'No. Variables:\s*(\d+)',b''.join(header))[1])
                offset=f.tell();count=(raw.stat().st_size-offset)//(n*8)
                if count:
                    f.seek(offset+(count-1)*n*8);t=struct.unpack('d',f.read(8))[0]
                    samples=max(0,min(64,int((t-.001421999)/.00002)+1)) if t>=.001421999 else 0
                    detail=f't={t:.15g} s, {count} records, {samples}/64 sample times reached'
    matched=a.root/(name+'-matched')/'r1c64-rc-port'
    retry=a.root/(name+'-matched-parallel')/'r1c64-rc-port'
    if retry.exists():matched=retry
    if matched.exists():
        detail+=f", {len(list(matched.glob('dc-*/op.raw')))}/64 reference files"
    if status.get('matched_completed'):detail+=f", matched error {status['max_output_error_V']*1e6:.3f} µV"
    if retry.exists():
        result=retry/'result.json'
        detail+='; wider reference retry'
        if result.exists():
            r=json.loads(result.read_text())
            if r['completed']:detail+=f", matched error {r['max_tracking_error_V']*1e6:.3f} µV"
    elif status.get('error'):detail+='; '+status['error']
    print(name+': '+detail)
