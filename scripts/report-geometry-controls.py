"""Audit and publish matched-plane diagnostics without claiming full RC qualification."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,shlex,hashlib,tarfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/geometry-controls'
read=lambda p:json.loads(p.read_text())
results={}
for name in ['straight','bend','via_bridge','wide_via_bridge']:
 d=base/name
 raw=[shlex.split(s) for s in (d/'control.res.ext').read_text().splitlines() if s.startswith('resist ')]
 exported=[s.split() for s in (d/'rc.spice').read_text().splitlines() if s.startswith('R')]
 assert len(raw)==len(exported)==1,(name,'missing or duplicate paths')
 assert set(raw[0][1:3])==set(exported[0][1:3])=={'test_A','test_B'}
 mr=float(raw[0][3]);sr=float(exported[0][3]);assert abs(sr-mr-.0005)<1e-9
 mesh=[]
 for step in [.2,.1,.05]:
  r=read(d/f'mesh-{step}/result.json');assert r['stitch_pass'] and max(r['relative_stitch_error'].values())<1e-8
  assert r['geometry_sha256']==hashlib.sha256((d/'geometry.json').read_bytes()).hexdigest()
  mesh.append(r['monolithic']['test']['R_ohm'])
 if name=='straight':assert all(abs(v/.192-1)<1e-9 for v in mesh) and abs(mr-.192)<1e-12
 results[name]={'Magic_raw_ohm':mr,'Magic_SPICE_ohm':sr,'mesh_steps_um':[.2,.1,.05],'FV_ohm':mesh,'fine_vs_raw_pct':100*(mesh[-1]/mr-1),'last_refinement_pct':100*(mesh[-1]/mesh[-2]-1),'single_path_audit_pass':True}
assert results['wide_via_bridge']['FV_ohm'][-1]<results['via_bridge']['FV_ohm'][-1]
f=read(base/'filler-matched-0.25/result.json');assert f['stitch_pass']
old=read(ROOT/'simulations/ring-sections.json')['cases']['fill20']['metal']['rails']
gap={n:100*(v['R_ohm']/old[n]['R_ohm']-1) for n,v in f['monolithic'].items()}
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
summary={'recorded':stamp,'scope':'Matched terminal planes, bends and M4/M5 via diagnostic coupons; matrix-only FV runs. Not DRC-qualified cells or full RC extraction.','controls':results,'matched_filler':f,'matched_filler_vs_earlier_Magic_pct':gap,'absolute_filler_convergence_established':False,'full_RC_qualified':False}
(ROOT/'simulations/geometry-controls.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axs=plt.subplots(1,3,figsize=(16,4.8),layout='constrained')
for name,r in results.items():axs[0].plot(r['mesh_steps_um'],[100*(v/r['Magic_raw_ohm']-1) for v in r['FV_ohm']],'-o',label=name)
axs[0].set(title='Matched-plane control differences',xlabel='Maximum mesh cell (µm)',ylabel='FV vs Magic raw resistance (%)');axs[0].invert_xaxis();axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
g=read(base/'via_bridge/geometry.json')
from matplotlib.patches import Rectangle
for z,color in [('46','#e6a147'),('81','#70bed4'),('41','#993e9c')]:
 for a,b,c,d in g['rects'][z]:axs[1].add_patch(Rectangle((a/1000,b/1000),(c-a)/1000,(d-b)/1000,color=color,alpha=.8))
axs[1].set(xlim=(-5.5,5.5),ylim=(-.5,2.5),aspect='equal',xlabel='µm',title='Via bridge: M5 ends, M4 bridge\nPurple = two via cuts')
names=list(gap);axs[2].bar(names,list(gap.values()));axs[2].set(title='Real filler: gap still present',ylabel='Matched-plane FV vs earlier Magic (%)');axs[2].grid(axis='y',alpha=.2)
fig.savefig(ROOT/'docs/assets/geometry-controls.png',dpi=150);plt.close(fig)
rows=''.join(f'<tr><td>{n}</td><td>{r["Magic_raw_ohm"]:.6f}</td><td>{r["FV_ohm"][-1]:.6f}</td><td>{r["fine_vs_raw_pct"]:.3f}%</td><td>{r["last_refinement_pct"]:.3f}%</td></tr>' for n,r in results.items())
html=f'''<section id="geometry-controls"><h2>Matched terminals, bends and vias</h2><p>Recorded {stamp}. Aligning the terminal measurement positions closes the straight-strip difference: the analytic, finite-volume and raw Magic results are all <strong>0.192 Ω</strong>. The exported Magic SPICE value is 0.1925 Ω.</p>
<img src="assets/geometry-controls.png" alt="Control resistance differences, via bridge geometry and remaining filler discrepancy">
<table><tr><th>Control</th><th>Magic raw Ω</th><th>FV 0.05 µm Ω</th><th>Difference</th><th>Last mesh change</th></tr>{rows}</table>
<p>The bend is a two-turn M5 path. The via controls connect two M5 ends through an M4 bridge, with one or three via cuts at each transition. All exports contain exactly one resistor between the two intended terminals; the forced canonical selection remains diagnostic only. The via controls include metal spreading resistance as well as contact resistance. They are not pure-via analytic standards or DRC-qualified macros.</p>
<p>Three mesh sizes pass the stitched/combined DC check. These runs are matrix-only; no new ngspice or optical-performance pass is claimed. The remaining bend/via differences do not establish which extraction is more accurate.</p>
<p><strong>The real filler discrepancy remains:</strong> moving full-width ideal electrode faces to the observed Magic x coordinates leaves a {min(gap.values()):.1f}–{max(gap.values()):.1f}% gap at the 0.25 µm mesh. This is a measurement-plane hypothesis; a finite electrode is not proven equivalent to a Magic point terminal in arbitrary geometry. The filler is still mesh-sensitive.</p>
<p>Next: isolate a single real filler rail and its probe transition, then compare M5-only, connected metal layers, and via networks on progressively finer meshes. Resolve absolute DC resistance before device-aware RC, corner substrate coupling and capacitance qualification.</p><p><a href="geometry-controls.md">Method, reproduction and evidence</a>.</p></section>'''
(ROOT/'docs/geometry-controls.html').write_text(html+'\n')
md='''# Matched terminal positions, bends and vias

'''+f'Recorded **{stamp}**.\n\n'+'''![Comparison and via geometry](assets/geometry-controls.png)

## Method and outcome

The straight 10 × 2 µm M5 strip retains 0.2 µm full-width ideal electrodes. Their inner faces are x = −4.8 and +4.8 µm. Magic label rectangles start at those x coordinates, unlike the previous test. Both raw Magic and the finite-volume model now agree with `0.04 × 9.6 / 2 = 0.192 Ω` at all three mesh sizes. A 0.0005 Ω export increment remains in each of these Magic SPICE controls; no general offset correction is applied.

The other controls are a two-turn M5 bend, a bridge through M4 with one via at each end, and the same bridge with three vias at each end. Every raw/exported Magic control must contain exactly one resistor between the intended terminals. The explicit canonical-net/negative-threshold recipe is retained only for these diagnostics. DRC, capacitance and devices are outside the scope.

'''
md+='| Control | Magic raw Ω | FV 0.05 µm Ω | Difference | Last mesh change |\n| --- | ---: | ---: | ---: | ---: |\n'
for n,r in results.items():md+=f'| {n} | {r["Magic_raw_ohm"]:.6f} | {r["FV_ohm"][-1]:.6f} | {r["fine_vs_raw_pct"]:.3f}% | {r["last_refinement_pct"]:.3f}% |\n'
md+='''
The FV matrices use exact via-edge alignment and maximum steps of 0.2, 0.1 and 0.05 µm. Stitched and combined networks agree below 1e-8 relative error on every run. These runs use matrix solves; no independent ngspice pass is claimed. The smaller last-step changes are evidence of refinement behavior, not a certified continuum error bound. Neither method is established as ground truth for the bend/via shapes.

## Real filler measurement-plane hypothesis

Keep all metal and via geometry fixed. Replace the original small terminal patches with full lead-width (0.4 µm) electrodes: left x = [−2.2, −2.1] µm, right x = [21.9, 22.2] µm. Their inward faces match the earlier Magic labels' lower-left x coordinates. This does not establish equivalence of finite-area and point terminals in arbitrary geometry. At maximum mesh step 0.25 µm:

| Rail | Matched-plane FV Ω | Earlier Magic Ω | Difference |
| --- | ---: | ---: | ---: |
'''
for n,v in f['monolithic'].items():md+=f'| {n} | {v["R_ohm"]:.6f} | {old[n]["R_ohm"]:.6f} | {gap[n]:.2f}% |\n'
md+='''
Terminal positioning alone does not resolve the real coupon gap. The next experiment should isolate a single real rail/probe transition, then add connected layers and vias incrementally. Absolute DC convergence, corner ground coupling and negative capacitance remain open before full-ring RC validation.

## Reproduce and restore

Use the pinned Docker environment and parent geometry from [terminal calibration](terminal-calibration.md).

```sh
bash scripts/run-tools.sh python3 scripts/run-geometry-controls.py
python3 scripts/prepare-matched-filler.py
bash scripts/run-tools.sh timeout 180 python3 scripts/compare-filler-stitch.py --geometry-file build/geometry-controls/filler-matched.json --output-dir build/geometry-controls/filler-matched-0.25 --step-um 0.25 --electrode-model equipotential --skip-spice
bash scripts/run-tools.sh python3 scripts/report-geometry-controls.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The checksummed `checkpoints/geometry-controls/evidence.tar.gz` contains the inputs, exports, logs, matrices, plots and summaries. Fine SPICE decks are reproducible and omitted to reduce archive size. SHA-256 hashes are in `manifest.json`. Extract into a separate directory to avoid overwriting active work. The parent checkpoints retain the original filler and Magic reference. No sensor or ring layout edits were required.
'''
(ROOT/'docs/geometry-controls.md').write_text(md)
cp=ROOT/'checkpoints/geometry-controls';cp.mkdir(exist_ok=True)
files=[p for p in base.rglob('*') if p.is_file() and (p.name!='stitched.spice' and p.name!='testbench.spice')]
files += [ROOT/p for p in ['scripts/run-geometry-controls.py','scripts/prepare-matched-filler.py','scripts/report-geometry-controls.py','scripts/compare-filler-stitch.py','docs/geometry-controls.md','docs/geometry-controls.html','docs/assets/geometry-controls.png','simulations/geometry-controls.json','simulations/ring-sections.json']]
manifest={'parent':'checkpoints/terminal-calibration/evidence.tar.gz','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=cp/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for n in manifest['files']:t.add(ROOT/n,arcname=n)
with tarfile.open(a) as t:
 for n,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(cp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2))
