"""Confirm both corrections in one executable and audit fresh block records."""
from pathlib import Path
from collections import Counter
import subprocess,json
R=Path(__file__).resolve().parents[1];B=R/'build/combined-patch';out={}
for block in ['buffer','readout']:
 def records(mode):
  lines=(B/block/mode/f'{block}_rc.spice').read_text().splitlines()
  caps=Counter();devices=[];edges=[]
  for s in lines:
   t=s.split()
   if not t:continue
   if t[0].startswith('C'):caps[(*sorted(t[1:3]),*t[3:])]+=1
   if t[0].startswith('X'):devices.append(t)
   if t[0].startswith('R'):edges.append(t[:3])
  return caps,devices,edges
 a,b=records('baseline'),records('combined')
 out[block]={'same_capacitance_multiset':a[0]==b[0],'same_devices':a[1]==b[1],'same_resistor_connectivity':a[2]==b[2]}
 out[block]['note']='Exact record comparison only: fresh extraction may renumber internal terminals and round capacitance differently. Connectivity is independently gated by LVS.'
for case,expected in [('two_end_columns',.10514803612590749),('all_cuts',.09383720124224756)]:
 d=B/case;d.mkdir(exist_ok=True)
 commands='scalegrid 1 10\ntech load /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech\n'+(R/'build/extraction-diagnostics'/case/'extract.tcl').read_text().replace('ext2spice -o rc.spice','ext2spice -o rc.spice rail')
 (d/'commands.txt').write_text(commands)
 p=subprocess.run([str(B/'magic-combined'),'-dnull','-rcfile','/dev/null'],input=''.join(':'+s+'\n' for s in commands.splitlines()),text=True,cwd=d,capture_output=True,timeout=60)
 (d/'extract.log').write_text(p.stdout+p.stderr)
 scale=next(float(s.split()[1]) for s in (d/'rail.res.ext').read_text().splitlines() if s.startswith('scale '))
 raw=[float(s.split()[-1])*scale*.001 for s in (d/'rail.res.ext').read_text().splitlines() if s.startswith('resist ')]
 exported=[float(s.split()[-1]) for s in (d/'rc.spice').read_text().splitlines() if s.startswith('R')]
 assert len(raw)==len(exported)==1
 out[case]={'raw_ohm':raw[0],'exported_ohm':exported[0],'unreduced_reference_ohm':expected,'pass':abs(raw[0]/expected-1)<2e-6 and abs(exported[0]-raw[0])<1e-9}
 assert out[case]['pass']
(B/'controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
