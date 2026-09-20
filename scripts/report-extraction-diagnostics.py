"""Publish controlled source-patch and via-density diagnostics with explicit limits."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,shlex,re,subprocess,hashlib,tarfile
from resistor_network import solve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/extraction-diagnostics'
read=lambda p:json.loads(p.read_text())
def parse(p,raw=False):
 edges=[]
 for line in p.read_text().splitlines():
  if (raw and line.startswith('resist ')) or (not raw and line.startswith('R')):
   t=shlex.split(line);edges.append((t[1],t[2],float(t[3])))
 return edges
def mapping(edges):return {tuple(sorted([a,b])):r for a,b,r in edges}
def spice_check(d,filename,expected):
 deck=f'Diagnostic DC\n.include {d}/{filename}\nXrail a 0 rail\nVtest a 0 1\n.control\nset numdgt=12\nop\nprint i(Vtest)\nquit\n.endc\n.end\n'
 p=d/(filename+'.cir');p.write_text(deck)
 with (d/(filename+'.ngspice.log')).open('w') as log:subprocess.run(['ngspice','-b',str(p)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
 m=re.search(r'i\(vtest\)\s*=\s*([-+0-9.eE]+)',(d/(filename+'.ngspice.log')).read_text(),re.I);assert m
 value=-1/float(m[1]);assert abs(value/expected-1)<1e-7
 return value
exports={}
for d in sorted((base/'export-check').glob('m5-to-m*'),reverse=True):
 raw=parse(d/'rail.res.ext',True);rd=mapping(raw);rawR=solve(raw)
 patched=parse(d/'patched.spice');baseline=parse(d/'baseline.spice');installed=parse(ROOT/'build/rail-faces'/d.name/'rc.spice')
 pm,bm,im=map(mapping,[patched,baseline,installed]);assert pm.keys()==bm.keys()==im.keys()==rd.keys()
 assert all(abs(pm[k]-rd[k])<max(1e-8,abs(rd[k])*1e-6) for k in rd)
 assert all(abs(bm[k]-im[k])<1e-10 for k in rd)
 assert all(abs(bm[k]-pm[k]-.0005)<1.1e-8 for k in rd)
 patchR,baseR=solve(patched),solve(baseline)
 assert abs(patchR/rawR-1)<1e-6
 ng=spice_check(d,'patched.spice',patchR);spice_check(d,'baseline.spice',baseR)
 for n in ['rail.ext','rail.res.ext']:assert (d/n).read_bytes()==(ROOT/'build/rail-faces'/d.name/n).read_bytes()
 exports[d.name]={'raw_ohm':rawR,'installed_and_unmodified_build_ohm':baseR,'patched_ohm':patchR,'patched_ngspice_ohm':ng,'same_raw_inputs':True,'edge_offset_removed':True}
via={};parent=read(ROOT/'build/rail-faces/m5-to-m4/geometry.json')
for name in ['two_end_cuts','two_end_columns','missing_one_cut','all_cuts']:
 d=base/name;g=read(d/'geometry.json')
 for z,b in parent['rects'].items():
  if z!='41':assert b==g['rects'][z]
 assert set(map(tuple,g['rects']['41']))<=set(map(tuple,parent['rects']['41']))
 rawR=solve(parse(d/'rail.res.ext',True));expR=solve(parse(d/'rc.spice'));spice_check(d,'rc.spice',expR)
 fv={}
 for step in [.1,.05]:
  r=read(d/f'mesh-{step}/result.json');assert r['stitch_pass'] and max(r['relative_stitch_error'].values())<1e-8
  assert r['geometry_sha256']==hashlib.sha256((d/'geometry.json').read_bytes()).hexdigest();fv[str(step)]=r['monolithic']['VDD']['R_ohm']
 via[name]={'cuts':len(g['rects']['41']),'raw_ohm':rawR,'exported_ohm':expR,'FV_ohm':fv,'raw_vs_fine_pct':100*(rawR/fv['0.05']-1)}
assert set(map(tuple,read(base/'two_end_columns/geometry.json')['rects']['41']))<set(map(tuple,parent['rects']['41']))
assert via['all_cuts']['raw_ohm']>via['two_end_columns']['raw_ohm']
assert via['all_cuts']['FV_ohm']['0.05']<via['two_end_columns']['FV_ohm']['0.05']
commit='381714e2d5debf2ded71c5a6b6604e6b936422cf'
source_url=f'https://github.com/RTimothyEdwards/magic/blob/{commit}/extflat/EFread.c#L598'
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
summary={'recorded':stamp,'Magic_version':'8.3.664','source_commit':commit,'source_url':source_url,'export_reader_offset_confirmed':True,'patched_export_diagnostic_only':True,'two_layer_raw_extraction_issue_resolved':False,'exports':exports,'via_controls':via,'patched_binary_sha256':hashlib.sha256((base/'magic-patched').read_bytes()).hexdigest(),'baseline_binary_sha256':hashlib.sha256((ROOT/'build/magic-export-diagnostic/bin/magic').read_bytes()).hexdigest(),'production_tools_or_netlists_changed':False,'full_RC_qualified':False}
(ROOT/'simulations/extraction-diagnostics.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axs=plt.subplots(1,2,figsize=(13,5),layout='constrained')
for key,label in [('raw_ohm','Raw extraction'),('installed_and_unmodified_build_ohm','Unmodified export'),('patched_ohm','Patched diagnostic export')]:axs[0].plot(list(exports),[v[key] for v in exports.values()],'-o',label=label)
axs[0].set(title='One-line reader patch removes the export offset',ylabel='Equivalent resistance (Ω)');axs[0].tick_params(axis='x',rotation=25);axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
for key,label in [('raw_ohm','Magic raw'),('FV_ohm','Spatial mesh 0.05 µm')]:axs[1].plot([v['cuts'] for v in via.values()],[v[key]['0.05'] if key=='FV_ohm' else v[key] for v in via.values()],'-o',label=label)
axs[1].set(title='Unchanged metal: adding vias exposes raw-extraction anomaly',xlabel='Number of via cuts',ylabel='Equivalent resistance (Ω)');axs[1].legend();axs[1].grid(alpha=.2)
fig.savefig(ROOT/'docs/assets/extraction-diagnostics.png',dpi=150);plt.close(fig)
rows=''.join(f'<tr><td>{n}</td><td>{v["raw_ohm"]:.6f}</td><td>{v["installed_and_unmodified_build_ohm"]:.6f}</td><td>{v["patched_ohm"]:.6f}</td></tr>' for n,v in exports.items())
vrows=''.join(f'<tr><td>{n}</td><td>{v["cuts"]}</td><td>{v["raw_ohm"]:.6f}</td><td>{v["FV_ohm"]["0.05"]:.6f}</td></tr>' for n,v in via.items())
body=f'''The export offset is traced to the resistor reader in Magic 8.3.664: it adds 0.5 to a floating-point resistance expressed internally in milliohms. Removing that addition in a local diagnostic build removes the measured 0.0005 Ω increment. An unmodified build with the same configuration reproduces the installed export resistor by resistor, isolating the one-line change from build differences. The patched build re-exports unchanged raw files and matches their effective resistance in all five stacks; both builds pass independent ngspice checks.

For the full stack, raw and patched resistance are about 0.0891035 Ω, versus 0.0990837 Ω from the unmodified export. This confirms the export cause for these resistor networks. It does not validate the patch for every device, hierarchy or capacitance use case, and does not fix raw geometry extraction.

The two-layer anomaly is independent of export. Keeping both metal shapes fixed and adding vias from the 20-cut end-column subset to all 300 cuts raises raw Magic resistance from 0.106148 Ω to 0.118443 Ω. The spatial model decreases from 0.105155 Ω to 0.093853 Ω. Adding passive connections should not raise DC resistance under the same terminal conditions. This localizes an inconsistency to Magic's raw two-layer via-array modeling. Removing a single cut also fails to eliminate it. The exact internal extraction cause remains open; no extraction patch or layout workaround is validated.

The source was checked out at the exact 8.3.664 release commit. The diagnostic uses a standalone, non-Tcl build because the container lacks Tcl development configuration; an equivalent unmodified build controls for that difference. A serial build avoids a generated-header race seen in the initial parallel attempt. The installed tools, production netlists and sensor/ring GDS were not replaced.

Next: inspect the raw two-layer contact/tile network before reduction and reproduce the failure in a minimal source-level regression. Separately broaden the reader-patch tests to device-aware hierarchical RC before considering adoption. Full-ring RC qualification remains open.'''
html=f'<section id="extraction-diagnostics"><h2>Export offset confirmed; two-layer via anomaly isolated</h2><p>{stamp}</p><img src="assets/extraction-diagnostics.png" alt="Patched versus original export and via-count resistance anomaly"><table><tr><th>Stack</th><th>Raw Ω</th><th>Original export Ω</th><th>Patched diagnostic Ω</th></tr>{rows}</table><table><tr><th>Via control</th><th>Cuts</th><th>Magic raw Ω</th><th>Spatial Ω</th></tr>{vrows}</table>'+''.join('<p>'+p+'</p>' for p in body.split('\n\n'))+f'<p><a href="{source_url}">Pinned upstream resistor-reader source</a> · <a href="extraction-diagnostics.md">Reproduction and evidence</a>.</p></section>\n'
(ROOT/'docs/extraction-diagnostics.html').write_text(html)
md=f'# Magic export and two-layer diagnostics\n\nRecorded **{stamp}**.\n\n![Diagnostic comparisons](assets/extraction-diagnostics.png)\n\n'+body+f'\n\nSource: [Magic 8.3.664 resistor reader]({source_url}). Diagnostic patch: [one-line change](../patches/magic-8.3.664-resistor-reader.patch).\n\n## Export comparison\n\n| Stack | Raw Ω | Unmodified export Ω | Patched diagnostic Ω |\n| --- | ---: | ---: | ---: |\n'
for n,v in exports.items():md+=f'| {n} | {v["raw_ohm"]:.6f} | {v["installed_and_unmodified_build_ohm"]:.6f} | {v["patched_ohm"]:.6f} |\n'
md+='\n## Via-array controls\n\n| Geometry | Cut count | Magic raw Ω | Spatial 0.05 µm Ω |\n| --- | ---: | ---: | ---: |\n'
for n,v in via.items():md+=f'| {n} | {v["cuts"]} | {v["raw_ohm"]:.6f} | {v["FV_ohm"]["0.05"]:.6f} |\n'
md+='''
The via subset checks establish unchanged metal geometry. Each spatial control runs at 0.1 and 0.05 µm with exact via-edge alignment and passes stitched/combined comparison below 1e-8 relative. Network audits reject nonpositive resistors, duplicate node pairs and disconnected nodes. All patched/baseline exports and the four installed-tool via controls pass independent ngspice checks. These are conductor-only diagnostic tests; no general PDK, LVS, DRC or full-RC signoff is implied.

## Reproduction

Use the pinned Docker image and the [rail-face checkpoint](rail-faces.md). Fetch the matching source on the host if it is absent:

```sh
git clone --depth 1 --branch 8.3.664 https://github.com/RTimothyEdwards/magic.git build/magic-8.3.664-source
bash scripts/run-tools.sh python3 scripts/run-extraction-diagnostics.py
bash scripts/run-tools.sh bash scripts/build-export-diagnostic.sh
bash scripts/run-tools.sh python3 scripts/report-extraction-diagnostics.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The build helper checks the source commit and requires an unmodified source checkout. It patches only the ignored diagnostic source, saves the patched executable, restores the source line and builds the matching baseline. No system install is performed. The helper uses a repository-local installation prefix. The patched executable and source checkout remain ignored build artifacts; reproduction requires fetching the source, not installing new host tools.

`checkpoints/extraction-diagnostics/evidence.tar.gz` contains the inputs, unchanged raw files, generated netlists, logs, scripts, patch and results. Its manifest records SHA-256 hashes. Large spatial matrices/decks and compiler binaries are reproducible and omitted; binary hashes and source commit are recorded in the summary. Extract checkpoints into a separate directory. No upstream issue, message or pull request has been sent.
'''
(ROOT/'docs/extraction-diagnostics.md').write_text(md)
cp=ROOT/'checkpoints/extraction-diagnostics';cp.mkdir(exist_ok=True)
files=[p for p in base.rglob('*') if p.is_file() and p.suffix!='.npz' and p.name not in ['magic-patched','stitched.spice','testbench.spice']]
files += [ROOT/p for p in ['scripts/run-extraction-diagnostics.py','scripts/check-export-patch.py','scripts/build-export-diagnostic.sh','scripts/report-extraction-diagnostics.py','scripts/resistor_network.py','scripts/compare-filler-stitch.py','patches/magic-8.3.664-resistor-reader.patch','docs/extraction-diagnostics.md','docs/extraction-diagnostics.html','docs/assets/extraction-diagnostics.png','simulations/extraction-diagnostics.json']]
manifest={'source_commit':commit,'parent':'checkpoints/rail-faces/evidence.tar.gz','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=cp/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for n in manifest['files']:t.add(ROOT/n,arcname=n)
with tarfile.open(a) as t:
 for n,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(cp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2))
