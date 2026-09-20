"""Audit full-width rail-face DC controls; distinguish raw extraction from export."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,shlex,re,subprocess,hashlib,tarfile
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import connected_components
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/rail-faces'
read=lambda p:json.loads(p.read_text())
def solve(edges):
 names=sorted(set(n for a,b,r in edges for n in [a,b]));assert 'VDD_A' in names and 'VDD_B' in names
 assert all(r>0 for a,b,r in edges)
 pairs=[tuple(sorted([a,b])) for a,b,r in edges];assert len(pairs)==len(set(pairs))
 ix={n:i for i,n in enumerate(names)};a=np.array([ix[a] for a,b,r in edges]);b=np.array([ix[b] for a,b,r in edges]);g=np.array([1/r for a,b,r in edges]);G=coo_matrix((np.r_[g,g,-g,-g],(np.r_[a,b,a,b],np.r_[a,b,b,a])),shape=(len(ix),len(ix))).tocsc()
 assert connected_components(G,directed=False)[0]==1
 keep=np.arange(len(ix))!=ix['VDD_B'];rhs=np.zeros(len(ix));rhs[ix['VDD_A']]=1
 v=np.zeros(len(ix));v[keep]=spsolve(G[keep][:,keep],rhs[keep]);assert max(abs((G@v-rhs)[keep]))<1e-8
 return float(v[ix['VDD_A']])
results={}
for d in sorted(base.glob('m5-to-m*'),reverse=True):
 assert 'Usage:' not in (d/'magic.log').read_text()
 raw=[];exported=[]
 for line in (d/'rail.res.ext').read_text().splitlines():
  t=shlex.split(line)
  if t[0]=='resist':raw.append((t[1],t[2],float(t[3])))
 for line in (d/'rc.spice').read_text().splitlines():
  if line.startswith('R'):
   t=line.split();exported.append((t[1],t[2],float(t[3])))
 rawR=solve(raw);spiceR=solve(exported)
 rd={tuple(sorted([a,b])):v for a,b,v in raw};sd={tuple(sorted([a,b])):v for a,b,v in exported};assert rd.keys()==sd.keys()
 offsets=[sd[k]-v for k,v in rd.items()]
 (d/'dc.cir').write_text(f'Full-width rail DC\n.include {d}/rc.spice\nXrail a 0 rail\nVtest a 0 1\n.control\nset numdgt=12\nop\nprint i(Vtest)\nquit\n.endc\n.end\n')
 with (d/'ngspice.log').open('w') as log:subprocess.run(['ngspice','-b',str(d/'dc.cir')],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
 match=re.search(r'i\(vtest\)\s*=\s*([-+0-9.eE]+)',(d/'ngspice.log').read_text(),re.I);assert match
 ngR=-1/float(match[1]);assert abs(ngR/spiceR-1)<1e-7
 meshes={}
 for step in [.25,.1,.05]:
  r=read(d/f'mesh-{step}/result.json');assert r['stitch_pass'] and max(r['relative_stitch_error'].values())<1e-8
  assert r['geometry_sha256']==hashlib.sha256((d/'geometry.json').read_bytes()).hexdigest();meshes[str(step)]=r['monolithic']['VDD']['R_ohm']
 fine=meshes['0.05']
 results[d.name]={'Magic_raw_R_ohm':rawR,'Magic_SPICE_R_ohm':spiceR,'ngspice_R_ohm':ngR,'ngspice_pass':True,'resistor_count':len(raw),'export_resistor_offset_range_ohm':[min(offsets),max(offsets)],'FV_R_ohm':meshes,'raw_vs_FV_pct':100*(rawR/fine-1),'export_vs_FV_pct':100*(spiceR/fine-1),'last_mesh_change_pct':100*(fine/meshes['0.1']-1)}
for name,r in results.items():
 assert max(abs(v-.0005) for v in r['export_resistor_offset_range_ohm'])<1.1e-8
 if name in ['m5-to-m3','m5-to-m2','m5-to-m1']:assert abs(r['raw_vs_FV_pct'])<.02
exact=.04*20/7
assert all(abs(v/exact-1)<1e-8 for v in results['m5-to-m5']['FV_R_ohm'].values())
assert abs(results['m5-to-m5']['Magic_raw_R_ohm']-exact)<1e-6
assert all(results[a]['FV_R_ohm']['0.05']>=results[b]['FV_R_ohm']['0.05'] for a,b in zip(list(results),list(results)[1:]))
prior=read(ROOT/'simulations/rail-isolation.json')['cases']
delta=prior['m5-to-m5']['FV_R_ohm']['0.0125']-exact
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
summary={'recorded':stamp,'scope':'Full-width M5 electrodes on the clipped real VDD conductor stack. Diagnostic DC comparison, not full RC qualification.','analytic_M5_R_ohm':exact,'M5_probe_configuration_minus_ideal_body_R_ohm':delta,'cases':results,'full_RC_qualified':False}
(ROOT/'simulations/rail-faces.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axs=plt.subplots(1,3,figsize=(16,4.8),layout='constrained')
axs[0].add_patch(Rectangle((0,0),20,7,color='#65b8d0'));axs[0].plot([0,0],[0,7],lw=6,color='#dd842e',label='Ideal electrode face');axs[0].plot([20,20],[0,7],lw=6,color='#dd842e');axs[0].set(xlim=(-2,22),ylim=(-1,8),aspect='equal',xlabel='x (µm)',ylabel='y relative to rail bottom (µm)',title='Full-width M5 measurement: 20 × 7 µm');axs[0].legend(fontsize=8)
for label,key in [('Magic raw','Magic_raw_R_ohm'),('Magic SPICE','Magic_SPICE_R_ohm')]:axs[1].plot(list(results),[r[key] for r in results.values()],'-o',label=label)
axs[1].plot(list(results),[r['FV_R_ohm']['0.05'] for r in results.values()],'-o',label='Spatial mesh 0.05 µm');axs[1].set(ylabel='Rail-face resistance (Ω)',title='Layered stacks: raw vs exported resistance');axs[1].tick_params(axis='x',rotation=25);axs[1].legend(fontsize=8);axs[1].grid(alpha=.2)
axs[2].bar(['Full-width\nM5 body','Narrow-lead\nM5 coupon'],[exact,prior['m5-to-m5']['FV_R_ohm']['0.0125']],color=['#65b8d0','#dd842e']);axs[2].set(ylabel='Spatial-model resistance (Ω)',title='Measurement configuration matters');axs[2].grid(axis='y',alpha=.2)
fig.savefig(ROOT/'docs/assets/rail-faces.png',dpi=150);plt.close(fig)
rows=''.join(f'<tr><td>{n}</td><td>{r["FV_R_ohm"]["0.05"]:.6f}</td><td>{r["Magic_raw_R_ohm"]:.6f}</td><td>{r["Magic_SPICE_R_ohm"]:.6f}</td><td>{r["raw_vs_FV_pct"]:.3f}%</td></tr>' for n,r in results.items())
body=f'''The M5-only rail agrees with the analytic value 0.04 × 20 / 7 = {exact:.9f} Ω at all three mesh sizes. Magic raw extraction agrees to its printed precision. Moving to full-width electrodes removes the large narrow-probe transition discrepancy in this controlled M5 comparison.

The new diagnostic clips every layer to x = 0…20 µm, preserving all interior rectangles, then replaces the external narrow M5 leads with 0.2 µm-long, 7 µm-wide ideal electrode extensions. Their inner faces are x = 0 and 20 µm. Magic label lower-left x coordinates match those planes. Only M5 is directly contacted; lower layers connect through their original vias. These are different electrical boundary conditions, not a physical pad change or proof that arbitrary Magic point terminals equal finite electrodes.

The earlier M5 narrow-lead coupon gives 0.577681 Ω; subtracting the analytic body gives {delta:.6f} Ω for the configuration difference. Its simple lead-strip contribution is 0.400000 Ω, leaving about {delta-.4:.6f} Ω beyond that one-dimensional estimate. This is evidence for spreading/access resistance in that geometry; it is not a universal correction to subtract from full-device extraction.

Every exported resistor network is checked for positive resistances, duplicate node pairs, disconnected nodes and agreement with an independent ngspice solve. All spatial meshes pass the stitched/combined 1e-8 relative screen. These checks verify topology and solving; they do not certify geometric extraction accuracy.

For M5–M3, M5–M2 and M5–M1, raw Magic agrees with the 0.05 µm spatial mesh within 0.013%; the last mesh changes are below 0.003%. This is strong numerical agreement for these conductor-only controls, not an independent certification of full RC accuracy. The exports add approximately 0.0005 Ω per resistor (within printed precision), raising the effective rail-face resistance by about 11.2% relative to the spatial model. The full-stack values are 0.0891035 Ω raw, 0.0891144 Ω spatial and 0.0990837 Ω exported.

The M5–M4 Magic diagnostic still increases resistance when passive metal is added, contrary to the spatial-model trend. Raw extraction and exported SPICE must also be distinguished: export changes the individual resistor values, and the total effect depends on network topology. No blanket offset subtraction or production netlist modification is applied.

Next: isolate the two-layer Magic anomaly and inspect the raw-to-SPICE resistor conversion before accepting the layered extraction as an absolute reference. Keep full-ring capacitance, substrate coupling and camera transient qualification behind that check. Production sensor and ring GDS are unchanged.'''
html=f'<section id="rail-faces"><h2>Full-width rail faces: separating the probe from the rail</h2><p>{stamp}</p><img src="assets/rail-faces.png" alt="Full-width rail electrodes, layered resistance comparison and probe contribution"><table><tr><th>Stack</th><th>FV 0.05 µm Ω</th><th>Magic raw Ω</th><th>Magic SPICE Ω</th><th>Raw vs FV</th></tr>{rows}</table>'+''.join('<p>'+p+'</p>' for p in body.split('\n\n'))+'<p><a href="rail-faces.md">Reproduction and evidence</a>.</p></section>\n'
(ROOT/'docs/rail-faces.html').write_text(html)
md=f'# Full-width rail-face comparison\n\nRecorded **{stamp}**.\n\n![Rail-face measurements](assets/rail-faces.png)\n\n'+body+'\n\n## Comparison\n\n| Stack | FV 0.05 µm Ω | Magic raw Ω | Magic SPICE Ω | Raw vs FV | Last mesh change |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'
for n,r in results.items():md+=f'| {n} | {r["FV_R_ohm"]["0.05"]:.6f} | {r["Magic_raw_R_ohm"]:.6f} | {r["Magic_SPICE_R_ohm"]:.6f} | {r["raw_vs_FV_pct"]:.3f}% | {r["last_mesh_change_pct"]:.4f}% |\n'
md+='\n## Reproduction\n\n```sh\nbash scripts/run-tools.sh python3 scripts/run-rail-faces.py\nbash scripts/run-tools.sh python3 scripts/report-rail-faces.py\nbash scripts/run-tools.sh python3 scripts/build-overview.py\n```\n\nUse the pinned Docker environment and [isolated-rail checkpoint](rail-isolation.md). The three mesh maxima are 0.25, 0.1 and 0.05 µm, with via-edge alignment and a 180-second watchdog per run. Magic uses accepted threshold zero, canonical `include VDD_B`, and `extresist all`. The spatial solves are matrix-only; ngspice independently checks the Magic exports. No new DRC/LVS or full-RC pass is claimed.\n\nThe compact `checkpoints/rail-faces/evidence.tar.gz` stores inputs, scripts, raw/exported netlists, logs, results and figures with SHA-256 hashes in `manifest.json`. Large matrices and generated spatial SPICE decks are reproducible and omitted. Extract to a separate folder when restoring. Exact values are in [the JSON summary](../simulations/rail-faces.json).\n'
(ROOT/'docs/rail-faces.md').write_text(md)
cp=ROOT/'checkpoints/rail-faces';cp.mkdir(exist_ok=True)
files=[p for p in base.rglob('*') if p.is_file() and p.suffix!='.npz' and p.name not in ['stitched.spice','testbench.spice']]
files += [ROOT/p for p in ['scripts/run-rail-faces.py','scripts/report-rail-faces.py','scripts/compare-filler-stitch.py','docs/rail-faces.md','docs/rail-faces.html','docs/assets/rail-faces.png','simulations/rail-faces.json','simulations/rail-isolation.json']]
manifest={'parent':'checkpoints/rail-isolation/evidence.tar.gz','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=cp/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for n in manifest['files']:t.add(ROOT/n,arcname=n)
with tarfile.open(a) as t:
 for n,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(cp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2))
