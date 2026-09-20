"""Track redistributed capacitance per original node without confusing it with node shunts."""
from pathlib import Path
from collections import defaultdict
import shlex,re,json
R=Path(__file__).resolve().parents[1];out={}
for variant in ['combined','area-fixed']:
 out[variant]={}
 for case in ['fill10','corner']:
  out[variant][case]={}
  for mode in ['full','metal']:
   d=R/'build/ring-candidate'/variant/case/mode;orig={};aliases={};couple=defaultdict(float)
   for s in (d/'coupon.ext').read_text().splitlines():
    if s.startswith(('node ','substrate ')):
     t=shlex.split(s);orig[t[1]]=float(t[3])
    elif s.startswith('equiv '):
     t=shlex.split(s);aliases[t[2]]=t[1]
    elif s.startswith('cap '):
     t=shlex.split(s);couple[t[1]]+=float(t[3]);couple[t[2]]+=float(t[3])
   groups=defaultdict(float);counts=defaultdict(int);negative=defaultdict(int)
   for s in (d/'coupon.res.ext').read_text().splitlines():
    if not s.startswith('rnode '):continue
    t=s.split();name=re.sub(r'\.[nt][0-9]+$','',t[1].strip('"'))
    while name in aliases:name=aliases[name]
    if name not in orig and name+'#' in orig:name+='#'
    assert name in orig,(name,d)
    value=float(t[3]);groups[name]+=value;counts[name]+=1;negative[name]+=value<0
   rows=[]
   for n,total in groups.items():
    expected=couple[n];error=(total-expected)/max(abs(expected),1e-30) if expected else total
    rows.append({'net':n,'original_node_shunt_aF':orig[n],'incident_coupling_aF':expected,'redistributed_sum_aF':total,'relative_error':error,'rnodes':counts[n],'negative_rnodes':negative[n]})
   out[variant][case][mode]=rows
   print(variant,case,mode,'max relative coupling redistribution error',max(abs(x['relative_error']) for x in rows),flush=True)
(R/'build/capacitance-candidate/conservation.json').write_text(json.dumps(out,indent=2)+'\n')
