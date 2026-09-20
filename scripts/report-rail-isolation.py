"""DC topology, independent SPICE checks, and incremental real-rail comparison."""
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
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/rail-isolation'
read=lambda p:json.loads(p.read_text())
def solve(edges):
 names=sorted(set(n for a,b,r in edges for n in [a,b]));assert 'VDD_A' in names and 'VDD_B' in names
 assert all(r>0 for a,b,r in edges)
 pairs=[tuple(sorted([a,b])) for a,b,r in edges]
 assert len(pairs)==len(set(pairs)),'duplicate resistor node pairs require review'
 ix={n:i for i,n in enumerate(names)};a=np.array([ix[a] for a,b,r in edges]);b=np.array([ix[b] for a,b,r in edges]);g=np.array([1/r for a,b,r in edges]);G=coo_matrix((np.r_[g,g,-g,-g],(np.r_[a,b,a,b],np.r_[a,b,b,a])),shape=(len(ix),len(ix))).tocsc()
 assert connected_components(G,directed=False)[0]==1,'orphan/disconnected resistance graph'
 ground=ix['VDD_B'];keep=np.arange(len(ix))!=ground;rhs=np.zeros(len(ix));rhs[ix['VDD_A']]=1
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
 (d/'dc.cir').write_text(f'Isolated rail DC\n.include {d}/rc.spice\nXrail a 0 rail\nVtest a 0 1\n.control\nop\nprint i(Vtest)\nquit\n.endc\n.end\n')
 with (d/'ngspice.log').open('w') as log:subprocess.run(['ngspice','-b',str(d/'dc.cir')],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
 match=re.search(r'i\(vtest\)\s*=\s*([-+0-9.eE]+)',(d/'ngspice.log').read_text(),re.I);assert match
 ngR=-1/float(match[1]);assert abs(ngR/spiceR-1)<1e-5
 meshes={}
 for p in d.glob('mesh-*/result.json'):
  r=read(p);assert r['stitch_pass'] and max(r['relative_stitch_error'].values())<1e-8
  assert r['geometry_sha256']==hashlib.sha256((d/'geometry.json').read_bytes()).hexdigest()
  meshes[str(r['step_um'])]=r['monolithic']['VDD']['R_ohm']
 assert '0.1' in meshes and '0.25' in meshes
 results[d.name]={'Magic_raw_R_ohm':rawR,'Magic_SPICE_R_ohm':spiceR,'ngspice_R_ohm':ngR,'independent_ngspice_pass':True,'resistor_count':len(raw),'no_duplicate_pairs_and_all_nodes_connected':True,'FV_R_ohm':meshes}
assert all(results[n]['FV_R_ohm']['0.1']>=results[m]['FV_R_ohm']['0.1']-1e-8 for n,m in zip(list(results),list(results)[1:]))
series=.04*(4/.4+20/7)
assert abs(results['m5-to-m5']['Magic_raw_R_ohm']-series)<1e-6
previous=read(ROOT/'simulations/ring-sections.json')['cases']['fill20']['metal']['rails']['VDD']['R_ohm']
assert abs(results['m5-to-m1']['Magic_SPICE_R_ohm']/previous-1)<1e-6
for d in base.glob('m5-to-m*'):
 geometry=read(d/'geometry.json')
 for port in read(ROOT/'build/filler-stitch/geometry.json')['ports']:
  if not port['name'].startswith('VDD_'):
   assert not any(a<=port['x']*1000<=c and b<=port['y']*1000<=e for a,b,c,e in geometry['rects']['81']),port
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
summary={'recorded':stamp,'scope':'Isolated VDD conductor component of the actual two-filler coupon; no device/capacitance qualification.','cases':results,'M5_series_strip_R_ohm':series,'Magic_M4_addition_increases_R':results['m5-to-m4']['Magic_raw_R_ohm']>results['m5-to-m5']['Magic_raw_R_ohm'],'FV_0p1um_added_conductors_monotonic':True,'Magic_threshold_correction':'Earlier -1 command was rejected with Usage; current extraction uses accepted threshold 0, include VDD_B, and extresist all.','full_RC_qualified':False}
(ROOT/'simulations/rail-isolation.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axs=plt.subplots(1,3,figsize=(16,5),layout='constrained')
g=read(base/'m5-to-m5/geometry.json')
for a,b,c,d in g['rects']['81']:axs[0].add_patch(Rectangle((a/1000,b/1000-254),(c-a)/1000,(d-b)/1000,color='#66b9d0'))
axs[0].set(xlim=(-3,23),ylim=(-1,8),aspect='equal',xlabel='x (µm)',ylabel='y relative to rail bottom (µm)',title='Actual M5 rail and narrow probe leads')
axs[0].annotate('0.4 µm lead',xy=(-1,3.29),xytext=(-2,6),arrowprops={'arrowstyle':'->'})
for label,key in [('Magic raw','Magic_raw_R_ohm'),('Magic SPICE','Magic_SPICE_R_ohm')]:axs[1].plot(list(results),[r[key] for r in results.values()],'-o',label=label)
axs[1].plot(list(results),[r['FV_R_ohm']['0.1'] for r in results.values()],'-o',label='FV 0.1 µm');axs[1].tick_params(axis='x',rotation=25);axs[1].set(ylabel='Resistance including leads (Ω)',title='Add connected lower metal layers');axs[1].legend(fontsize=8);axs[1].grid(alpha=.2)
for name in ['m5-to-m5','m5-to-m1']:
 r=results[name];steps=sorted(map(float,r['FV_R_ohm']),reverse=True);axs[2].plot(steps,[r['FV_R_ohm'][str(s)] for s in steps],'-o',label=name)
axs[2].set(xlabel='Maximum cell size (µm)',ylabel='Spatial mesh resistance (Ω)',title='Refinement: top metal and full rail');axs[2].invert_xaxis();axs[2].legend();axs[2].grid(alpha=.2)
fig.savefig(ROOT/'docs/assets/rail-isolation.png',dpi=150);plt.close(fig)
rows=''.join(f'<tr><td>{n}</td><td>{r["Magic_raw_R_ohm"]:.6f}</td><td>{r["Magic_SPICE_R_ohm"]:.6f}</td><td>{r["FV_R_ohm"]["0.1"]:.6f}</td></tr>' for n,r in results.items())
text='''The discrepancy is present before any via is added. The finest M5-only mesh gives 0.577681 Ω at 0.0125 µm maximum cell size; the last refinement changes it by 0.057%. This is evidence of numerical stabilization, not an independent accuracy certification. The top-metal-only Magic result equals the one-dimensional series-strip estimate: 0.04 × (4 / 0.4 + 20 / 7) = 0.514286 Ω. The spatial mesh predicts additional resistance around the abrupt narrow-lead-to-wide-rail transitions. This strongly implicates probe-transition modeling; it does not independently prove either model's accuracy for the full rail.

Adding M4 increases Magic's effective resistance slightly, while the spatial model decreases as expected when a passive parallel path is added. This diagnostic monotonicity failure means these Magic exports should not be treated as an absolute DC reference without further investigation. The SPICE exports pass independent ngspice solves, which validates solving the exported networks, not their geometric accuracy.

Correction to earlier notes: the installed Magic rejects `extresist threshold -1` with a usage message. The earlier runs therefore did not prove a negative-threshold recipe. These rail results were rerun using accepted `extresist threshold 0`, explicit `extresist include VDD_B`, and `extresist all`; logs are checked for usage errors. Earlier checkpoint archives are preserved as historical evidence.

The full isolated Magic SPICE model reproduces the earlier four-rail VDD result (0.499084 Ω), confirming that isolation preserves this measurement. Raw versus exported resistance differs by about 0.00998 Ω for this multi-resistor network, so the single-resistor 0.0005 Ω observation must not be applied as a blanket terminal correction. Only the VDD-connected conductor component is retained at each stage; adding layers can connect more of the original rail geometry. These are diagnostic conductor coupons, not DRC/LVS-qualified layout revisions. The production sensor and power-ring GDS remain unchanged. Full RC, corner substrate coupling and negative capacitance remain unqualified.

Next: separate probe access resistance from the macro by moving measurements to full-width rail faces. Compare that de-embedded M5 control with an analytic strip and the layered rail with an independent field solver or a validated access-resistance model before returning to full-ring RC.'''
html=f'<section id="rail-isolation"><h2>Real VDD rail: the probe transition is a major source of disagreement</h2><p>{stamp}</p><img src="assets/rail-isolation.png" alt="Isolated M5 probe geometry, incremental layer comparison and mesh refinement"><table><tr><th>Layers</th><th>Magic raw Ω</th><th>Magic SPICE Ω</th><th>FV 0.1 µm Ω</th></tr>{rows}</table>'+''.join('<p>'+p.replace('`','')+'</p>' for p in text.split('\n\n'))+'<p><a href="rail-isolation.md">Commands and evidence</a>.</p></section>\n'
(ROOT/'docs/rail-isolation.html').write_text(html)
md=f'# Isolated real VDD rail\n\nRecorded **{stamp}**.\n\n![Rail isolation results](assets/rail-isolation.png)\n\n'+text+'\n\n## Results\n\n| Layers | Magic raw Ω | Magic SPICE Ω | FV 0.1 µm Ω |\n| --- | ---: | ---: | ---: |\n'
for n,r in results.items():md+=f'| {n} | {r["Magic_raw_R_ohm"]:.6f} | {r["Magic_SPICE_R_ohm"]:.6f} | {r["FV_R_ohm"]["0.1"]:.6f} |\n'
md+='\nAll completed mesh results and finer refinements are recorded in [the JSON summary](../simulations/rail-isolation.json). DC partition agreement is checked below 1e-8 relative; every Magic resistor network is checked for duplicate node pairs, disconnected nodes and agreement with ngspice. Mesh refinement is not an independent continuum error bound.\n\n## Reproduction\n\n```sh\nbash scripts/run-tools.sh python3 scripts/run-rail-isolation.py\nbash scripts/run-tools.sh python3 scripts/refine-rail-probes.py\nbash scripts/run-tools.sh python3 scripts/report-rail-isolation.py\nbash scripts/run-tools.sh python3 scripts/build-overview.py\n```\n\nUse the pinned Docker environment and the parent [matched-terminal checkpoint](geometry-controls.md). Each mesh has a 180-second watchdog. The checksummed `checkpoints/rail-isolation/evidence.tar.gz` retains geometry, extraction logs/netlists, results, scripts and figures. Large sparse matrices and generated FV SPICE decks are reproducible and omitted; this is a compact result/input checkpoint. Restore into a separate directory.\n'
(ROOT/'docs/rail-isolation.md').write_text(md)
cp=ROOT/'checkpoints/rail-isolation';cp.mkdir(exist_ok=True)
files=[p for p in base.rglob('*') if p.is_file() and p.suffix!='.npz' and p.name not in ['stitched.spice','testbench.spice']]
files += [ROOT/p for p in ['scripts/run-rail-isolation.py','scripts/refine-rail-probes.py','scripts/report-rail-isolation.py','scripts/compare-filler-stitch.py','docs/rail-isolation.md','docs/rail-isolation.html','docs/assets/rail-isolation.png','simulations/rail-isolation.json','build/geometry-controls/filler-matched.json']]
manifest={'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=cp/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for n in manifest['files']:t.add(ROOT/n,arcname=n)
with tarfile.open(a) as t:
 for n,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(cp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2))
