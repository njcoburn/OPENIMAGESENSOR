"""Signed-capacitance and substrate audit; never repair or clamp the model."""
from pathlib import Path
from collections import defaultdict
import json,re,shlex,argparse
R=Path(__file__).resolve().parents[1];B=R/'build/ring-candidate';out={}
def val(s):
 m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([a-z]*)',s,re.I)
 return float(m[1])*{'':1e15,'f':1,'p':1e3,'n':1e6,'u':1e9}[m[2].lower()]
parser=argparse.ArgumentParser();parser.add_argument('--variants',nargs='+',default=['baseline','combined']);parser.add_argument('--output',type=Path);args=parser.parse_args()
for variant in args.variants:
 out[variant]={}
 for case in ['fill10','corner']:
  out[variant][case]={}
  for mode in ['full','metal']:
   d=B/variant/case/mode;diagonal=defaultdict(float);neg=[];caps=[]
   for s in (d/'rc.spice').read_text().splitlines():
    if s.startswith('C'):
     t=s.split();a,b=t[1:3];c=val(t[3]);caps.append((a,b,c))
     if a!=b:diagonal[a]+=c;diagonal[b]+=c
     if c<0:neg.append({'name':t[0],'a':a,'b':b,'fF':c})
   witnesses=[{'node':n,'C_diagonal_fF':c,'energy_J_at_1V':.5*c*1e-15} for n,c in diagonal.items() if n!='0' and c < -1e-10]
   witnesses.sort(key=lambda x:x['C_diagonal_fF'])
   witness_names={x['node'] for x in witnesses}
   raw_witnesses=[]
   for line in (d/'coupon.res.ext').read_text().splitlines():
    if line.startswith('rnode '):
     t=line.split()
     if t[1].strip(chr(34)) in witness_names:raw_witnesses.append(line)
   aliases=[s for s in (d/'coupon.ext').read_text().splitlines() if s.startswith('equiv ') and any(x in s for x in ['VSS','DVSS'])]
   warnings=[s for s in (d/'extraction.log').read_text().splitlines() if any(k in s.lower() for k in ['missing rptr','error:', 'snapped to grid'])]
   data={'raw_rnode_witnesses':raw_witnesses,'extraction_diagnostics':warnings,'negative_capacitors':neg,'negative_sum_fF':sum(x['fF'] for x in neg),'capacitors':len(caps),'negative_diagonal_count':len(witnesses),'energy_witnesses':witnesses[:10],'ground_aliases_ext':aliases,'capacitance_gate':'reject_negative_energy' if witnesses else ('unresolved_signed_network' if neg else 'nonnegative_capacitor_network')}
   (d/'capacitance-audit.json').write_text(json.dumps(data,indent=2)+'\n');out[variant][case][mode]=data
(args.output or B/'capacitance-audit.json').write_text(json.dumps(out,indent=2)+'\n')
for v,cases in out.items():
 for c,modes in cases.items():
  for m,d in modes.items():print(v,c,m,'negative',len(d['negative_capacitors']),'diagonal witnesses',d['negative_diagonal_count'],d['capacitance_gate'])
