"""Verify serialized reference netlists against original pair capacitances and R/device records."""
from pathlib import Path
from collections import defaultdict
import json,re,shlex,hashlib
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reference';out={}
def capvalue(s):
 m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([a-z]*)',s,re.I)
 return float(m[1])*{'':1e15,'f':1,'p':1e3}[m[2]]
for d in sorted(p for p in B.iterdir() if p.is_dir()):
 a=json.loads((d/'audit.json').read_text());src=R/a['source'];old=(src/'rc.spice').read_text().splitlines();new=(d/'reference.spice').read_text().splitlines()
 unchanged=[s for s in old if s.startswith(('R','X','D'))]==[s for s in new if s.startswith(('R','X','D'))];assert unchanged
 aliases={};expected=defaultdict(float);orig=[];sub=None
 for s in (src/'coupon.ext').read_text().splitlines():
  if s.startswith('equiv '):t=shlex.split(s);aliases[t[2]]=t[1]
  elif s.startswith('substrate '):sub=shlex.split(s)[1]
 def canonical(n):
  seen=set()
  while n in aliases:
   assert n not in seen;seen.add(n);n=aliases[n]
  return n
 for s in (src/'coupon.ext').read_text().splitlines():
  if s.startswith(('node ','substrate ')):
   t=shlex.split(s);orig.append((t[1],sub,float(t[3])*.001))
  elif s.startswith('cap '):t=shlex.split(s);orig.append((t[1],t[2],float(t[3])*.001))
 for x,y,c in orig:
  x,y=canonical(x),canonical(y)
  if x!=y and c:expected[tuple(sorted((x,y)))]+=c
 reverse={v['anchor']:canonical(k) for k,v in a['mapping'].items()};observed=defaultdict(float)
 for s in new:
  if s.startswith('C'):
   t=s.split();x,y=reverse[t[1]],reverse[t[2]];v=capvalue(t[3]);assert v>=0
   if x!=y:observed[tuple(sorted((x,y)))]+=v
 assert set(expected)==set(observed)
 error=max([abs(expected[p]-observed[p]) for p in expected] or [0]);assert error<1e-9
 out[d.name]={'unchanged_resistors_and_devices':unchanged,'max_serialized_pair_error_fF':error,'capacitance_pairs':len(observed),'reference_sha256':hashlib.sha256((d/'reference.spice').read_bytes()).hexdigest()}
(B/'serialized-audit.json').write_text(json.dumps(out,indent=2)+'\n');print('All 8 serialized models preserve R/devices and original capacitance pairs')
