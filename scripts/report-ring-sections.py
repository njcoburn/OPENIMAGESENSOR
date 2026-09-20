"""Publish bounded coupon experiment, with DC evidence separated from RC model acceptance."""
from pathlib import Path
import json,hashlib,tarfile,datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import klayout.db as k
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/ring-sections';d=json.loads((ROOT/'simulations/ring-sections.json').read_text());names=['fill10','fill20','corner','corner_fill'];labels=['1 filler','2 fillers','Corner','Corner + filler'];rails=['VDD','VSS','DVDD','DVSS'];colors=['#c75219','#156082','#862faa','#208147']
fig,axs=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for ax,rail in zip(axs.flat,rails):
 x=np.arange(4)
 for offset,mode,label,col in [(-.18,'full','Full geometry','#156082'),(.18,'metal','Conductors only','#e49d37')]:ax.bar(x+offset,[d['cases'][n][mode]['rails'][rail]['R_ohm'] for n in names],.36,label=label,color=col)
 ax.set(xticks=x,xticklabels=labels,ylabel='Point-to-point resistance (Ω)',title=rail);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
axs[0,0].legend();fig.suptitle('Extracted coupon resistance — includes external M5 measurement leads\nOther terminals open; corner full extraction includes semiconductor ground coupling',fontsize=13)
fig.savefig(ROOT/'docs/assets/ring-sections-resistance.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,4,figsize=(16,6),constrained_layout=True)
for ax,name,label in zip(axs,names,labels):
 l=k.Layout();l.read(str(base/name/'full.gds'));c=l.cell(name);region=k.Region(c.begin_shapes_rec(l.layer(81,0))).merged()
 patches=[Polygon([(p.x*l.dbu,p.y*l.dbu) for p in poly.to_simple_polygon().each_point()],closed=True) for poly in region.each()]
 ax.add_collection(PatchCollection(patches,facecolor='#c8d3df',edgecolor='#576b80',linewidth=.3))
 meta=json.loads((base/name/'geometry.json').read_text())
 for p in meta['ports']:
  ax.scatter(p['x'],p['y'],s=18,color=colors[rails.index(p['rail'])],zorder=3)
 ax.autoscale();ax.set_aspect('equal');ax.set(title=label,xlabel='µm',ylabel='µm');ax.grid(alpha=.15)
fig.suptitle('Actual coupon metal-5 geometry and measurement terminals\nLower metals, vias and devices are present in the extraction but hidden in this view',fontsize=13)
fig.savefig(ROOT/'docs/assets/ring-sections-layout.png',dpi=150);plt.close(fig)
rows=[];maxdiff=0
for name,label in zip(names,labels):
 c=d['cases'][name];full=c['full'];metal=c['metal'];diff=max(abs(full['rails'][r]['R_ohm']/metal['rails'][r]['R_ohm']-1)*100 for r in rails);maxdiff=max(maxdiff,diff)
 rows.append('<tr><td>'+label+'</td>'+''.join(f'<td>{full["rails"][r]["R_ohm"]:.4f}</td>' for r in rails)+f'<td>{full["extraction_s"]:.2f}</td><td>{full["negative_capacitors"]}</td></tr>')
section='''<section id="ring-sections"><h2>Small ring sections: extraction and abutment experiment</h2>
<p>We can now extract a filler, two adjacent fillers, a corner, and a corner joined to a filler without waiting for the complete ring. Full-device exports take under one second for the fillers and about 28 seconds for the corners. The original sensor and physical ring are unchanged.</p>
<img src="assets/ring-sections-layout.png" alt="Actual metal-5 geometry of four extraction coupons with terminal markers">
<p>Four rail names are preserved: VDD, VSS, DVDD and DVSS. Independent metal/via checks confirm four separate physical conductor nets and all 830 original macro-label probes pass across the coupons. Every measured terminal pair has finite positive resistance and the resistor-network current-balance residual is below 1e-6 A for a 1 A test injection.</p>
<p><strong>Measurement fixture:</strong> 0.4 µm wide external M5 probe leads give the extractor distinct terminal locations. The values below include those leads. These are point-terminal measurements, not bare macro resistances, equipotential edge models, or numbers that can simply be added around a ring.</p>
<table><tr><th>Coupon</th><th>VDD (Ω)</th><th>VSS (Ω)</th><th>DVDD (Ω)</th><th>DVSS (Ω)</th><th>Full extraction (s)</th><th>Negative C entries</th></tr>'''+''.join(rows)+'''</table>
<img src="assets/ring-sections-resistance.png" alt="Full-geometry versus conductor-only resistance for four rails and four coupons">
<p>All four full-device exports pass device LVS after the extracted resistor networks are shorted. The filler checks keep all four macro ports separate. The corner checks tie supplies and grounds into the same analog domain used in our actual ring. The full corner extraction connects VSS and DVSS through semiconductor geometry; the conductor-only control does not. This is not evidence of an unwanted metal short.</p>
<p>Full-geometry and conductor-only corner results differ by up to '''+f'{maxdiff:.1f}%'+'''. They have different semiconductor networks and extraction partitions, so the control cannot replace the full model. The corner-plus-filler result also demonstrates why individual point-terminal resistances should not simply be added: an abutment can provide additional parallel paths.</p>
<h3>Failures that the audit caught</h3><ul><li>Device-only and RC export in one session introduced zero-ohm aliases and eliminated-node errors. RC is now exported independently.</li><li>Internal point labels lost a passive terminal in the exported network. External narrow probe leads resolved the terminal-connectivity check; the fixture contribution remains in the reported values.</li></ul>
<h3>What remains before camera simulation</h3><p>The corner RC files contain negative capacitor entries (five for the corner, seven for corner-plus-filler). No capacitance correction, passivity result, transient qualification, complete ring model, or new DRC signoff is claimed. Next: define a consistent multiport interface at every abutment stripe/layer; compare a stitched two-cell model with a monolithic coupon; then resolve capacitance/substrate treatment before assembling the full ring and rerunning the camera.</p>
<p><a href="ring-sections.md">Reproduction, validation scope, and saved evidence</a>.</p></section>'''
(ROOT/'docs/ring-sections.html').write_text(section+'\n')
checkpoint=ROOT/'checkpoints/ring-sections';checkpoint.mkdir(exist_ok=True)
files=[ROOT/'simulations/ring-sections.json',ROOT/'docs/ring-sections.md',ROOT/'docs/ring-sections.html',ROOT/'docs/assets/ring-sections-layout.png',ROOT/'docs/assets/ring-sections-resistance.png']
files+=list((ROOT/'scripts').glob('*ring-sections.py'))
for name in names:
 folder=base/name;files += list(folder.glob('*.gds'))+[folder/'geometry.json']
 for mode in ['full','metal']:
  f=folder/mode
  files += [p for p in f.iterdir() if p.is_file() and (p.suffix in ['.spice','.tcl','.json','.log'] or p.name=='coupon.ext')]
 for f in folder.glob('attempt-*'):
  # Failed diagnostic models remain in build; preserve settings/status/logs in the portable checkpoint.
  files += [f/n for n in ['extract.tcl','status.json','extraction.log'] if (f/n).exists()]
manifest={'scope':'Small-section DC/topology experiment. RC capacitance and stitched-ring qualification incomplete. Failed attempts preserve settings/status/logs, not all intermediate meshes.','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=checkpoint/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for n in manifest['files']:t.add(ROOT/n,arcname=n)
with tarfile.open(a) as t:
 for n,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h,n
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(checkpoint/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Published',len(manifest['files']),'checksummed files; maximum full/control resistance difference',maxdiff,'%')
