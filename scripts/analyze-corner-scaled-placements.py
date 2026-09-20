"""Compare completed corner placements; this is not a timestep or spatial-error bound."""
from pathlib import Path
from bisect import bisect_right
import json
R=Path(__file__).resolve().parents[1];B=R/'build/corner-scaled-candidate'
r=json.loads((B/'result.json').read_text());assert r['both_complete']
def read(name):
 a=[list(map(float,l.split())) for l in (B/name/'tran.dat').read_text().splitlines()[1:]];return [x[0] for x in a],a
x,a=read('nominal');y,b=read('remote')
def interp(ts,z,t,j):
 k=min(max(1,bisect_right(ts,t)),len(ts)-1);f=(t-ts[k-1])/(ts[k]-ts[k-1]);return z[k-1][j]*(1-f)+z[k][j]*f
t=sorted(set(x+y));delta=[[abs(interp(x,a,q,j)-interp(y,b,q,j)) for j in range(1,4)] for q in t]
summary=dict(full_trace_max=[max(d[j] for d in delta) for j in range(3)],post_startup_max=[max(d[j] for q,d in zip(t,delta) if q>=150e-6) for j in range(3)],at_151_5us=[abs(interp(x,a,151.5e-6,j)-interp(y,b,151.5e-6,j)) for j in range(1,4)],column_units=['rail V','digital rail V','source A'],scope='Two recorded lumped-capacitor placements on one full corner coupon at 50 ns maximum step; not a spatial worst-case bound or refined performance claim')
r['placement_comparison']=summary;(B/'result.json').write_text(json.dumps(r,indent=2)+'\n');(R/'simulations/corner-scaled-candidate.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(summary,indent=2))
