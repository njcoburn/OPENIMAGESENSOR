"""Small dead-end metal branches exercise one-breakpoint area allocation."""
from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1];B=R/'build/capacitance-candidate/controls'
for shape,rects in [('tee',[(0,0,2,20),(2,8,10,10)]),('long-tee',[(0,0,2,20),(2,8,18,10)])]:
 for rotate in [False,True]:
  case=shape+('-rotated' if rotate else '')
  for variant,exe in [('combined','build/combined-patch/magic-combined'),('area-fixed','build/capacitance-candidate/magic-area-fixed')]:
   d=B/case/variant;d.mkdir(parents=True,exist_ok=True)
   for name in ['coupon.mag','coupon.ext','coupon.res.ext','rc.spice']:(d/name).unlink(missing_ok=True)
   commands=['scalegrid 1 10','tech load /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.tech','drc off']
   for x1,y1,x2,y2 in rects:
    if rotate:x1,y1,x2,y2=y1,x1,y2,x2
    commands += [f'box values {x1}um {y1}um {x2}um {y2}um','paint m5']
   commands += ['box values 0um 0um 20um 20um','paint m4','box values 5um 5um 5.01um 5.01um','label REF center m4','port make 3']
   for i,(x,y) in enumerate([(1,0),(1,19.99)],1):
    if rotate:x,y=y,x
    commands += [f'box values {x}um {y}um {x+.01}um {y+.01}um',f'label {"A" if i==1 else "B"} center m5',f'port make {i}']
   commands += ['save coupon','extract do capacitance','extract do coupling','extract do resistance','extresist threshold 0','extresist minres 1','extresist mindelay 0','extresist simplify off','extresist include B','extract all','ext2spice lvs','ext2spice cthresh 0','ext2spice extresist on','ext2spice subcircuits top on','ext2spice -o rc.spice coupon','quit -noprompt']
   (d/'commands.txt').write_text('\n'.join(commands)+'\n')
   p=subprocess.run([str(R/exe),'-dnull','-rcfile','/dev/null'],input=''.join(':'+s+'\n' for s in commands),cwd=d,text=True,capture_output=True,timeout=30)
   (d/'extract.log').write_text(p.stdout+p.stderr);assert p.returncode==0
   net=(d/'rc.spice').read_text();ports=next(s.split()[2:] for s in net.splitlines() if s.startswith('.subckt'));assert set(ports)=={'A','B','REF'},net
   assert any(s.startswith('R') for s in net.splitlines()),net
   print(case,variant,net,flush=True)
