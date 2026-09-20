"""Publish the DC boundary benchmark without claiming a stitched Magic RC model."""
from pathlib import Path
import json,hashlib,tarfile
import numpy as np
from scipy.sparse import load_npz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/filler-stitch';steps=[2.,1.,.5,.25]
results=[json.loads((base/f'mesh-{h}'/'result.json').read_text()) for h in steps]
reference=json.loads((ROOT/'build/ring-sections/boundary-inspection.json').read_text())
expected={z:[[round(y0*1000),round(y1*1000)] for y0,y1 in intervals] for z,intervals in reference.items()}
for h,r in zip(steps,results):
 folder=base/f'mesh-{h}';ports=json.loads((folder/'ports.json').read_text());assert ports['boundary_intervals_dbu']==expected
 assert r['stitch_pass'] and max(r['relative_stitch_error'].values())<r['stitch_limit']
 G=load_npz(folder/'stitched-conductance.npz').tocsr()
 for name,n in ports['boundary_ports'].items():
  row=G.getrow(n);assert row.nnz==3 and row[0,n]>0 and np.sum(row.data<0)==2,(h,name)
 assert len(ports['boundary_ports'])==r['boundary_ports']
 assert len(dict(list(ports['boundary_ports'].items())[1:]))!=r['boundary_ports'] # Deliberate omission is detected.
 assert hashlib.sha256((base/'geometry.json').read_bytes()).hexdigest()==r['geometry_sha256']
finest=results[-1];previous=results[-2];rails=['VDD','VSS','DVDD','DVSS']
magic=json.loads((ROOT/'simulations/ring-sections.json').read_text())['cases']['fill20']['metal']['rails']
mesh_change={r:abs(finest['monolithic'][r]['R_ohm']/previous['monolithic'][r]['R_ohm']-1)*100 for r in rails}
magic_difference={r:(finest['monolithic'][r]['R_ohm']/magic[r]['R_ohm']-1)*100 for r in rails}
max_stitch=max(v for r in results for v in r['relative_stitch_error'].values())
summary={'scope':'Conductor-only finite-volume DC stitching benchmark. NOT stitched Magic RC/device extraction or a qualified full-ring camera model.','meshes':results,'all_81_intervals_match_independent_KLayout_geometry':True,'boundary_nodes_have_two_half_connections':True,'omitted_port_negative_control_detected':True,'max_relative_stitch_error':max_stitch,'independent_ngspice_pass_at_1um':results[1]['ngspice_check_pass'],'ngspice_0p5um_attempt':json.loads((base/'mesh-0.5/ngspice-attempt.json').read_text()),'last_mesh_change_pct':mesh_change,'Magic_diagnostic_difference_pct':magic_difference,'absolute_resistance_converged':False,'full_RC_stitch_qualified':False}
(ROOT/'simulations/filler-stitch.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axs=plt.subplots(1,3,figsize=(17,5),constrained_layout=True)
for j,(layer,intervals) in enumerate(expected.items()):
 for lo,hi in intervals:axs[0].plot([j,j],[lo/1000,hi/1000],lw=7,solid_capstyle='butt')
axs[0].set(xticks=range(5),xticklabels=['M1','M2','M3','M4','M5'],ylabel='Boundary position y (µm)',title='81 physical intervals at x = 10 µm');axs[0].grid(alpha=.15)
x=np.arange(4)
for off,values,label in [(-.25,[finest['monolithic'][r]['R_ohm'] for r in rails],'Combined DC mesh'),(0,[finest['stitched'][r]['R_ohm'] for r in rails],'Stitched DC mesh'),(.25,[magic[r]['R_ohm'] for r in rails],'Earlier Magic control')]:axs[1].bar(x+off,values,.25,label=label)
axs[1].set(xticks=x,xticklabels=rails,ylabel='Resistance including probe leads (Ω)',title='0.25 µm maximum mesh cell');axs[1].legend(fontsize=8);axs[1].grid(axis='y',alpha=.15)
for rail in rails:axs[2].plot(steps,[r['monolithic'][rail]['R_ohm'] for r in results],'-o',label=rail)
axs[2].set(xlabel='Maximum mesh cell size (µm)',ylabel='Combined-mesh resistance (Ω)',title='Absolute values still change with refinement');axs[2].invert_xaxis();axs[2].legend(fontsize=8);axs[2].grid(alpha=.15)
fig.suptitle('Boundary stitching passes; absolute resistance and full RC qualification remain open',fontsize=14)
fig.savefig(ROOT/'docs/assets/filler-stitch.png',dpi=150);plt.close(fig)
rows=''.join(f'<tr><td>{r}</td><td>{finest["monolithic"][r]["R_ohm"]:.6f}</td><td>{finest["stitched"][r]["R_ohm"]:.6f}</td><td>{magic[r]["R_ohm"]:.6f}</td><td>{mesh_change[r]:.2f}%</td></tr>' for r in rails)
section=f'''<section id="filler-stitch"><h2>Two-filler boundary stitching: DC benchmark</h2>
<p><strong>The partition test passes.</strong> Two independently constructed geometry partitions preserve all 81 conductor intervals at their shared boundary. The finest mesh uses 4,593 separate seam ports. Each port has one connection into each half, and every interval matches an independent KLayout boundary inspection.</p>
<img src="assets/filler-stitch.png" alt="Physical boundary intervals, stitched versus combined resistance, and mesh refinement results">
<p>This is a new conductor-only finite-volume DC reference using nominal metal/via resistance values read from the installed GF180 Magic technology file. It is <strong>not a stitched Magic RC model</strong>. It contains no transistor, capacitor, or substrate network. Both constructions use the same mesh and outer electrode conditions; their agreement validates partition assembly, not the absolute extraction method.</p>
<table><tr><th>Rail</th><th>Combined DC mesh (Ω)</th><th>Stitched DC mesh (Ω)</th><th>Earlier Magic control (Ω)</th><th>Last mesh refinement change</th></tr>{rows}</table>
<p>All values include the previous coupon's measurement leads. Across four meshes, maximum relative stitched/combined disagreement is {max_stitch:.2e}, below the 1e-8 comparison limit. The exported two-subcircuit SPICE model at 1 µm also passes an independent ngspice DC solve. The 0.5 µm ngspice attempt timed out after 120 seconds; its matrix comparison completed separately. No finer ngspice pass is claimed.</p>
<p><strong>Remaining uncertainty:</strong> the latest spatial refinement changes resistance by up to {max(mesh_change.values()):.2f}%, and the fine-grid values differ from the earlier Magic control by {min(magic_difference.values()):.1f}–{max(magic_difference.values()):.1f}%. Electrode treatment and numerical extraction differ. Neither agreement with Magic nor convergence of absolute resistance is established. The earlier negative capacitance and corner semiconductor-ground issues also remain open.</p>
<p>Next: refine and calibrate the terminal treatment against controlled geometry, reconcile the Magic/DC-reference discrepancy, then apply this boundary interface to device-aware RC sections. A full-ring camera simulation must wait for those checks.</p>
<p><a href="filler-stitch.md">Method, reproducible commands, evidence and limitations</a>.</p></section>'''
(ROOT/'docs/filler-stitch.html').write_text(section+'\n')
cp=ROOT/'checkpoints/filler-stitch';cp.mkdir(exist_ok=True)
files=[ROOT/'scripts/prepare-filler-stitch.py',ROOT/'scripts/compare-filler-stitch.py',ROOT/'scripts/report-filler-stitch.py',ROOT/'scripts/inspect-filler-boundary.py',ROOT/'docs/filler-stitch.md',ROOT/'docs/filler-stitch.html',ROOT/'docs/assets/filler-stitch.png',ROOT/'simulations/filler-stitch.json',ROOT/'build/ring-sections/boundary-inspection.json',ROOT/'build/ring-sections/fill20/metal.gds',ROOT/'build/ring-sections/fill20/geometry.json']+list(p for p in base.rglob('*') if p.is_file())
manifest={'scope':summary['scope'],'parent':'checkpoints/ring-sections/evidence.tar.gz','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=cp/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for name in manifest['files']:t.add(ROOT/name,arcname=name)
with tarfile.open(a) as t:
 for name,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==h,name
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(cp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Boundary benchmark PASS; absolute resistance/full RC remain unqualified. Archive files:',len(manifest['files']))
print('Mesh change %',mesh_change,'Magic difference %',magic_difference)
