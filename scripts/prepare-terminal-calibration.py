"""Straight M5 strips: analytic, finite-volume and Magic terminal controls."""
from pathlib import Path
import json
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/terminal-calibration';out.mkdir(parents=True,exist_ok=True)
prior=json.loads((ROOT/'build/filler-stitch/geometry.json').read_text());l=k.Layout();l.dbu=.001;c=l.create_cell('calibration');rects={z:[] for z in [34,36,42,46,81,35,38,40,41]};ports=[];cases={}
for i,(name,length,width) in enumerate([('thin10',10,.4),('thin20',20,.4),('wide10',10,2),('wide20',20,2)]):
 y=i*10;box=[round(-length/2*1000),round(y*1000),round(length/2*1000),round((y+width)*1000)];rects[81].append(box);c.shapes(l.layer(81,0)).insert(k.Box(*box))
 for side,x in [('A',-length/2+.1),('B',length/2-.1)]:ports.append({'name':name+'_'+side,'x':x,'y':y+width/2,'half_x_um':.1,'half_y_um':width/2})
 cases[name]={'length_um':length,'width_um':width,'electrode_width_um':.2,'analytic_equipotential_R_ohm':.04*(length-.4)/width,'lower_left_point_distance_R_ohm':.04*(length-.2)/width}
l.write(str(out/'calibration.gds'))
data={'dbu_um':.001,'rects':rects,'sheet_ohm_per_square':prior['sheet_ohm_per_square'],'via_ohm_per_cut':prior['via_ohm_per_cut'],'ports':ports,'seam_dbu':0,'expected_intervals':4,'cases':cases,'tech_sha256':prior['tech_sha256']}
(out/'geometry.json').write_text(json.dumps(data,indent=2)+'\n')
for mode in ['area','point']:
 d=out/('magic-'+mode);d.mkdir(exist_ok=True);t=['drc off',f'gds read {out}/calibration.gds','load calibration','select top cell']
 for idx,p in enumerate(ports,1):
  hx=p['half_x_um'];hy=p['half_y_um'] if mode=='area' else .05;x=p['x'];y=p['y']
  t += [f'box values {x-hx}um {y-hy}um {x+hx}um {y+hy}um',f'label {p["name"]} center m5',f'port make {idx}',f'port {p["name"]} class '+('input' if p['name'].endswith('_A') else 'output')]
 t += ['extract do capacitance','extract do coupling','extract do resistance','extresist threshold 0','extresist minres 1','extresist mindelay 0','extresist simplify off','extract all','ext2spice lvs','ext2spice cthresh 0','ext2spice extresist on','ext2spice subcircuits top on','ext2spice -o rc.spice','quit -noprompt']
 (d/'extract.tcl').write_text('\n'.join(t)+'\n')
print('Four analytic strips prepared:',cases)
