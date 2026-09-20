"""PDK-free reproducer for ngspice 47 capacitor-multiplier parser failure.
Explicitly unconnected to full-chip numerical acceptance.
"""
from pathlib import Path
import subprocess,json,hashlib,re,os
R=Path(__file__).resolve().parents[1];B=R/'build/ngspice-version-comparison';D=B/'multiplier-reproducer';D.mkdir(exist_ok=True)
template='''Behavioral capacitor multiplier parser reproducer -- no PDK
Vdrive drive 0 1
Rdrive drive n 1k
.subckt nonlinear_cap p n
Ctest p n C='1p*(1+0.1*tanh(v(p,n)))'
.ends nonlinear_cap
Xcap n 0 nonlinear_cap MULTIPLIER
.control
op
print v(n) i(Vdrive)
quit
.endc
.end
'''
rows=[]
for name,m in [('default',''),('m1','m=1'),('m8','m=8'),('m70','m=70')]:
 for version in ['46','47']:
  d=D/f'{name}-{version}';d.mkdir(exist_ok=True);deck=template.replace('MULTIPLIER',m);(d/'test.spice').write_text(deck)
  exe=B/f'install-{version}/bin/ngspice'
  with (d/'ngspice.log').open('w') as f:
   p=subprocess.run([str(exe),'-b','test.spice'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=15,env={**os.environ,'SPICE_USERINIT_DIR':str(R/'checkpoints/clamp-review/package/init')})
  log=(d/'ngspice.log').read_text();errors=re.findall(r'^.*(?:unknown parameter|Error|interrupted).*$',log,re.I|re.M);passed=p.returncode==0 and not errors and 'v(n)' in log
  row=dict(case=name,version=version,passed=bool(passed),errors=errors,returncode=p.returncode,deck_sha256=hashlib.sha256(deck.encode()).hexdigest());rows.append(row);print(row,flush=True)
r=dict(cases=rows,scope='PDK-free operating-point parser reproducer only; no transient or chip qualification',source_location='ngspice-47/src/frontend/inpcom.c capacitance formulation: tprintf appends e9 to mstr; eval_mvalue may already return scientific notation or expression.');(D/'results.json').write_text(json.dumps(r,indent=2)+'\n')
