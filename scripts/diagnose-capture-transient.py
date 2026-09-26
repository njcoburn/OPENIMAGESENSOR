"""Isolate one column model from the retained four-model transient fixture.

Each run has a watchdog and records incomplete traces as failures. No simulator
tolerances or terminal stimuli are changed by selecting a single model.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import subprocess
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
NAMES=('rc','rcfar','physical','ideal')


def trace(path):
    if not path.exists():return None,None
    with path.open('rb') as f:
        header=b''
        while True:
            line=f.readline()
            if not line:return None,None
            if line==b'Binary:\n':break
            header+=line
        offset=f.tell()
    text=header.decode()
    names=[line.split()[1].lower() for line in text.split('Variables:\n')[1].splitlines() if line.strip()]
    count=(path.stat().st_size-offset)//(len(names)*8)
    data=np.memmap(path,mode='r',dtype=np.float64,offset=offset,shape=(count,len(names)))
    return dict(zip(names,range(len(names)))),data


def isolate(source,name):
    output=[]
    for line in source.splitlines():
        fields=line.split()
        if not fields:continue
        token=fields[0]
        if token=='.include' and Path(fields[1]).stem in NAMES:
            if Path(fields[1]).stem!=name:continue
        elif token in ['X'+n for n in NAMES]:
            if token!='X'+name:continue
        elif any(token.endswith('_'+n) for n in NAMES):
            if not token.endswith('_'+name):continue
        elif token=='.save':
            line='.save '+' '.join(n for n in fields[1:] if not any(n.endswith('_'+other+')') for other in NAMES if other!=name))
        output.append(line)
    assert sum(line.startswith('X'+name+' ') for line in output)==1
    return '\n'.join(output)+'\n'


def transform_model(text,mode):
    lines=text.splitlines();parent={}
    def find(n):
        parent.setdefault(n,n)
        if parent[n]!=n:parent[n]=find(parent[n])
        return parent[n]
    resistors=[l.split() for l in lines if l.startswith('R')]
    for r in resistors:parent[find(r[1])]=find(r[2])
    ports=next(l.split()[2:] for l in lines if l.startswith('.subckt'))
    canonical={find(n):n for n in ports};assert len(canonical)==len(ports)
    output=[]
    for line in lines:
        f=line.split()
        if not f:continue
        kind=f[0][0]
        if mode=='r-only' and kind=='C':continue
        if mode=='c-only' and kind=='R':continue
        if mode=='ground-collapsed' and kind=='R' and find(f[1])==find('GND'):continue
        if mode=='c-only' or mode=='ground-collapsed':
            count=(2 if f[3].startswith('cap_mim_') else 4) if kind=='X' else 2 if kind in 'RC' else 0
            for i in range(1,count+1):
                if mode=='c-only' or find(f[i])==find('GND'):f[i]=canonical[find(f[i])]
            if kind=='C' and f[1]==f[2]:continue
            line=' '.join(f)
        output.append(line)
    return '\n'.join(output)+'\n'


def run_case(out,source,name,step,timeout,solver,method,transform):
    d=out/f'{name}-{step}';d.mkdir()
    deck=isolate(source,name)
    if transform!='full':
        pattern=r'(?m)^\.include (.+/'+name+r'\.spice)$'
        path=Path(re.search(pattern,deck)[1])
        (d/'original-model.spice').write_bytes(path.read_bytes())
        (d/'model.spice').write_text(transform_model(path.read_text(),transform))
        deck=re.sub(pattern,'.include '+str(d/'model.spice'),deck)
    deck=re.sub(r'(?m)^\.tran .*',f'.tran {step}n 2.7m 0 {step}n',deck)
    deck,count=re.subn(r'(?m)^(?:set|unset) klu$',
                       'set klu' if solver=='klu' else 'unset klu',deck)
    assert count==1, 'Expected exactly one solver-selection command'
    if method:deck=re.sub(r'method=\w+','method='+method,deck)
    (d/'test.spice').write_text(deck)
    start=time.monotonic();expired=False
    with (d/'ngspice.log').open('w') as log:
        try:
            process=subprocess.run(['ngspice','-b','test.spice'],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
            rc=process.returncode
        except subprocess.TimeoutExpired:
            expired=True;rc=None
    ix,data=trace(d/'stream.raw')
    last=float(data[-1,0]) if data is not None and len(data) else None
    log=(d/'ngspice.log').read_text()
    errors=[line for line in log.splitlines() if re.search(r'^Error:|no such command|simulation\(s\) aborted',line,re.I)]
    complete=rc==0 and not expired and last is not None and last>=.0027-1e-12 and not errors
    result=dict(model=name,transform=transform,step_ns=step,solver=solver,method=method,timeout=expired,
        returncode=rc,seconds=time.monotonic()-start,stop_s=last,complete=complete,
        points=len(data) if data is not None else 0,errors=errors,deck_sha256=hashlib.sha256(deck.encode()).hexdigest())
    if complete:
        assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
        result['samples']={slot:{node:float(np.interp(t,data[:,0],data[:,ix[f'v({node}_{name})']])) for node in ['hold','store','cbuf','buf','sc','scb','sel','selb']} for slot,t in [('first',.0014215),('last',.0026815)]}
    (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='samples'}),flush=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'build/capture-column-screen-v2-singlethread-20260925/27-1.6-100/test.spice')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--models',choices=NAMES,nargs='+',default=list(NAMES))
    p.add_argument('--steps',type=int,nargs='+',default=[100,50])
    p.add_argument('--timeout',type=float,default=60)
    p.add_argument('--solver',choices=['klu','sparse'],default='klu')
    p.add_argument('--method',choices=['trap','gear'])
    p.add_argument('--transform',choices=['full','r-only','c-only','ground-collapsed'],default='full')
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    source=a.source.read_text();(out/'source.spice').write_text(source)
    jobs=[(name,step) for name in a.models for step in a.steps]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda job:run_case(out,source,*job,a.timeout,a.solver,a.method,a.transform),jobs))
    (out/'report.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),runs=results),indent=2)+'\n')


if __name__=='__main__':main()
