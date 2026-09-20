"""Independent SPICE check of the raw constructed graphs, without export conversion."""
from pathlib import Path
import json,shlex,subprocess,re
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/network-investigation';results=json.loads((base/'construction-results.json').read_text())
for name,r in results.items():
 d=base/name;edges=[shlex.split(s)[1:] for s in (d/'rail.res.ext').read_text().splitlines() if s.startswith('resist ')]
 deck=['Raw constructed graph','Itest 0 VDD_A 1','Vground VDD_B 0 0']+[f'R{i} {a} {b} {v}' for i,(a,b,v) in enumerate(edges)]+['.control','set numdgt=12','op','print v(VDD_A)','quit','.endc','.end']
 (d/'raw.cir').write_text('\n'.join(deck)+'\n')
 with (d/'raw-ngspice.log').open('w') as f:p=subprocess.run(['ngspice','-b',str(d/'raw.cir')],stdout=f,stderr=subprocess.STDOUT,timeout=30,check=True)
 m=re.search(r'v\(vdd_a\)\s*=\s*([-+0-9.eE]+)',(d/'raw-ngspice.log').read_text(),re.I);assert m
 r['ngspice_R_ohm']=float(m[1]);assert abs(r['ngspice_R_ohm']/r['R_ohm']-1)<1e-7
for case in ['two_end_columns','all_cuts']:
 a=results[case+'-fixed']['R_ohm'];b=results[case+'-unreduced']['R_ohm'];assert abs(a/b-1)<2e-6
results['scope']='Six raw networks independently solved in ngspice; triangle-candidate agreement with unreduced matrix solve checked within 2e-6 relative, accounting for printed precision.'
(base/'construction-verification.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
