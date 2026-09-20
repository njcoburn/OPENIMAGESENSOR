"""Provisional custom-carrier placement. No signal/power routes or sign-off claim."""
from pathlib import Path
from collections import Counter
import json,csv,hashlib
import klayout.db as k
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path(__file__).resolve().parents[1];B=R/'build/pad-proposal';B.mkdir(exist_ok=True)
L=k.Layout();L.dbu=.001;u=lambda a:round(a/L.dbu)
source=k.Layout();source.read('/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/gds/gf180mcu_fd_io.gds')
cells={}
for name in ['cor','asig_5p0','dvdd','dvss','fill10']:
 c=L.create_cell('gf180mcu_fd_io__'+name);c.copy_tree(source.cell(c.name));cells[name]=c
core_source=k.Layout();core_source.read(str(R/'checkpoints/integrated/sensor_3x3.gds'))
core=L.create_cell('sensor_3x3');core.copy_tree(core_source.cell('sensor_3x3'))
top=L.create_cell('demonstrator_pad_proposal');W=1210
corebox=core.dbbox();dx=(W-corebox.width())/2-corebox.left;dy=(W-corebox.height())/2-corebox.bottom
assert abs(dx*1000-round(dx*1000))<1e-5 and abs(dy*1000-round(dy*1000))<1e-5
ct=k.Trans(u(dx),u(dy));top.insert(k.CellInstArray(core.cell_index(),ct))
box=ct.trans(core.bbox()).to_dtype(L.dbu)
assert box.left>355 and box.bottom>355 and box.right<W-355 and box.top<W-355
rows=[];placements=[]
def put(name,rot,x,y):
 t=k.Trans(rot,False,u(x),u(y));top.insert(k.CellInstArray(cells[name].cell_index(),t));placements.append(dict(macro=name,rotation_deg=rot*90,x_um=x,y_um=y));return t
for rot,x,y in [(0,0,0),(1,W,0),(2,W,W),(3,0,W)]:put('cor',rot,x,y)
side_nets=[('south',['GND','VDD','BIAS','SEL0','SEL1','SEL2']),('east',['GND','PREF','BUF','COL2','COL1','COL0']),('north',['GND','VDD','OUT','RST2','ROW2','VRESET']),('west',['GND','RST1','ROW1','RST0','ROW0','VDD'])]
for rot,(side,nets) in enumerate(side_nets):
 transform=[lambda x:(x,0),lambda x:(W,x),lambda x:(W-x,W),lambda x:(0,W-x)][rot]
 for index,net in enumerate(nets):
  origin=355+75*index;x,y=transform(origin)
  name='dvss' if net=='GND' else 'dvdd' if net=='VDD' else 'asig_5p0'
  t=put(name,rot,x,y)
  pads=[s.text for s in cells[name].shapes(L.layer(81,10)).each() if s.is_text() and s.text.string=={'dvss':'DVSS','dvdd':'DVDD','asig_5p0':'ASIG5V'}[name] and s.text.trans.disp.y*L.dbu<60]
  # PAD text is a documented geometry reference; it is not a certified bond landing center.
  assert len(pads)==1,(name,len(pads))
  local=pads[0].trans.disp
  ipoint=t.trans(k.Point(local.x,local.y))
  assert t.trans(cells[name].bbox()).contains(ipoint)
  point=ipoint.to_dtype(L.dbu)
  rows.append(dict(pad_id=f'P{len(rows)+1:02d}',core_net=net,side=side,macro=cells[name].name,rotation_deg=rot*90,origin_x_um=x,origin_y_um=y,pad_label_x_um=point.x,pad_label_y_um=point.y,bond_status='optional diagnostic / loading review' if net in ['OUT','COL0','COL1','COL2'] else 'proposed functional bond'))
 for index in range(5):x,y=transform(805+10*index);put('fill10',rot,x,y)
ports=next(l.split()[2:] for l in (R/'circuits/integrated.spice').read_text().splitlines() if l.startswith('.subckt sensor_3x3 '))
assert set(x['core_net'] for x in rows)==set(ports)
counts=Counter(x['core_net'] for x in rows);assert counts['VDD']==3 and counts['GND']==4 and all(counts[p]==1 for p in ports if p not in ['VDD','GND'])
assert len({(r['pad_label_x_um'],r['pad_label_y_um']) for r in rows})==24
assert len(rows)==24 and len([p for p in placements if p['macro']=='fill10'])==20
# Every side spans 500 µm: six 75 µm pads and five 10 µm fillers.
assert 6*75+5*10==W-2*355
L.write(str(B/'demonstrator_pad_proposal.gds'))
with (R/'docs/proposed-pad-map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
meta=dict(status='Placement only; unrouted, unapproved custom-carrier concept',nominal_ring_um=[W,W],actual_gds_bbox_um=str(top.dbbox()),core_bbox_um=[box.left,box.bottom,box.right,box.top],core_translation_um=[dx,dy],core_source_sha256=hashlib.sha256((R/'checkpoints/integrated/sensor_3x3.gds').read_bytes()).hexdigest(),pad_count=24,unique_nets=len(counts),supply_pad_count=7,corner_count=4,clamp_count_from_macro_inventory=15,instances=placements,pads=rows,checks=['All 19 schematic ports assigned','24 unique pad IDs','Side-length accounting exact','Core inside nominal ring opening','Translation on layout grid'],limitations=['No routing, local secondary protection, seal ring, optical mask changes or ESD qualification','No DRC/LVS/density/antenna/precheck run on proposal','PAD-label coordinates are not approved bond centers','Macro bounding boxes include process-layer overhang; bbox overlap is not used as a DRC test','Diagnostic pad leakage/capacitance and added clamps require requalification'])
(B/'placement.json').write_text(json.dumps(meta,indent=2)+'\n')
(R/'simulations/pad-proposal.json').write_text(json.dumps(meta,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(10,10),layout='constrained')
for p in placements:
 name=p['macro'];t=k.Trans(p['rotation_deg']//90,False,u(p['x_um']),u(p['y_um']));b=t.trans(cells[name].bbox()).to_dtype(L.dbu)
 ax.add_patch(Rectangle((b.left,b.bottom),b.width(),b.height(),facecolor='#cbd5e1' if name=='cor' else '#e2e8f0',edgecolor='#64748b',lw=.5))
ax.add_patch(Rectangle((box.left,box.bottom),box.width(),box.height(),facecolor='#80c9d7',edgecolor='#155e75',lw=2))
ax.text(W/2,W/2,'Existing 3×3 core\n334.2 × 241.2 µm\nOptical path must remain clear',ha='center',va='center',fontsize=10)
for row in rows:
 x,y=row['pad_label_x_um'],row['pad_label_y_um'];net=row['core_net'];color='#b45309' if net in ['VDD','GND'] else '#9333ea' if net in ['COL0','COL1','COL2','OUT'] else '#0369a1'
 ax.plot(x,y,'o',color=color,ms=5)
 # Names run along the inward radial direction; distinct pad IDs follow CCW perimeter order.
 if row['side']=='south':ax.text(x,y+45,row['pad_id']+' '+net,rotation=90,ha='center',va='bottom',fontsize=9,color=color)
 elif row['side']=='east':ax.text(x-45,y,row['pad_id']+' '+net,ha='right',va='center',fontsize=9,color=color)
 elif row['side']=='north':ax.text(x,y-45,row['pad_id']+' '+net,rotation=90,ha='center',va='top',fontsize=9,color=color)
 else:ax.text(x+45,y,row['pad_id']+' '+net,ha='left',va='center',fontsize=9,color=color)
ax.set(xlim=(-30,W+30),ylim=(-30,W+30),aspect='equal',xlabel='µm',ylabel='µm',title='Proposed 24-pad placement — top view, not routed or approved\nNominal 1.21 × 1.21 mm ring; die outline / seal ring not assigned')
ax.text(W/2,365,'Blue: functional signals   •   Purple: optional diagnostics\nBrown: supply / ground   •   Dots: macro PAD-label references',ha='center',fontsize=9)
fig.savefig(R/'docs/assets/proposed-pad-map.png',dpi=160);plt.close(fig)
print('Proposal generated; 19 nets / 24 pads; placement checks passed. No routing or sign-off claimed.')
