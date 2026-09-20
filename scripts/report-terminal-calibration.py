"""Audit controlled terminal tests and publish their limits with recoverable evidence."""
from pathlib import Path
import json, hashlib, tarfile, shlex
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/terminal-calibration'
read=lambda p:json.loads(p.read_text())
g=read(base/'geometry.json'); cases=g['cases']; rails=['VDD','VSS','DVDD','DVSS']
strip={}
for model in ['legacy','equipotential']:
 for step in ['1','0.1']:
  r=read(base/f'{model}-{step}/result.json')
  assert r['stitch_pass'] and max(r['relative_stitch_error'].values())<1e-8
  assert r['geometry_sha256']==hashlib.sha256((base/'geometry.json').read_bytes()).hexdigest()
  strip[f'{model}-{step}']={n:r['monolithic'][n]['R_ohm'] for n in cases}
  if model=='equipotential':
   for n,c in cases.items():assert abs(strip[f'{model}-{step}'][n]/c['analytic_equipotential_R_ohm']-1)<1e-9
selection={}
for mode in ['area','point','all','negative-threshold','include','canonical-negative']:
 folder=base/('magic-'+mode); counts={n:[] for n in cases}
 for line in (folder/'rc.spice').read_text().splitlines():
  if line.startswith('R'):
   _,a,b,r=line.split();n=a.rsplit('_',1)[0]
   assert n in cases and {a,b}=={n+'_A',n+'_B'}
   counts[n].append(float(r))
 status='complete_single_paths' if all(len(v)==1 for v in counts.values()) else ('invalid_duplicate_paths' if any(len(v)>1 for v in counts.values()) else 'incomplete_missing_paths')
 selection[mode]={'classification':status,'resistors_ohm':counts}
assert selection['canonical-negative']['classification']=='complete_single_paths'
assert all(selection[m]['classification']=='invalid_duplicate_paths' for m in ['all','negative-threshold'])
assert all(selection[m]['classification']=='incomplete_missing_paths' for m in ['area','point','include'])
raw={}
for line in (base/'magic-canonical-negative/calibration.res.ext').read_text().splitlines():
 t=shlex.split(line)
 if t[0]=='resist':
  n=t[1].rsplit('_',1)[0];assert n not in raw;raw[n]=float(t[3])
for n,c in cases.items():
 assert abs(raw[n]-c['lower_left_point_distance_R_ohm'])<1e-12
 assert abs(selection['canonical-negative']['resistors_ohm'][n][0]-raw[n]-.0005)<1e-12
fbase=ROOT/'build/filler-stitch'
filler={n:read(fbase/n/'result.json') for n in ['electrode-1.0','electrode-0.5','electrode-0.25','electrode-0.5-via-grid']}
for r in filler.values():
 assert r['stitch_pass'] and max(r['relative_stitch_error'].values())<1e-8
 assert r['geometry_sha256']==hashlib.sha256((fbase/'geometry.json').read_bytes()).hexdigest()
assert filler['electrode-1.0']['ngspice_check_pass']
magic=read(ROOT/'simulations/ring-sections.json')['cases']['fill20']['metal']['rails']
fine=filler['electrode-0.25']['monolithic']
gap={n:100*(fine[n]['R_ohm']/magic[n]['R_ohm']-1) for n in rails}
change={n:100*(fine[n]['R_ohm']/filler['electrode-0.5']['monolithic'][n]['R_ohm']-1) for n in rails}
summary={'scope':'Controlled conductor-only terminal calibration; absolute filler resistance and full RC remain unqualified.','strip_cases':cases,'strip_results':strip,'analytic_electrode_pass':True,'Magic_selection':selection,'Magic_raw_R_ohm':raw,'observed_SPICE_offset_ohm':.0005,'filler_results':filler,'fine_vs_Magic_pct':gap,'last_mesh_change_pct':change,'production_Magic_recipe_changed':False,'absolute_resistance_converged':False,'full_RC_qualified':False}
(ROOT/'simulations/terminal-calibration.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axs=plt.subplots(1,2,figsize=(13,5),layout='constrained')
for key,values in strip.items():axs[0].plot(list(cases),[100*(values[n]/cases[n]['analytic_equipotential_R_ohm']-1) for n in cases],'-o',label=key)
axs[0].set(title='Straight M5 strips: ideal-electrode error',ylabel='Difference from analytic resistance (%)');axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
for n in rails:
 axs[1].plot([1,.5,.25],[filler[f'electrode-{h}']['monolithic'][n]['R_ohm'] for h in ['1.0','0.5','0.25']],'-o',label=n)
 axs[1].scatter([.5],[filler['electrode-0.5-via-grid']['monolithic'][n]['R_ohm']],marker='x',color=axs[1].lines[-1].get_color())
axs[1].set(title='Two fillers: corrected electrodes; × = via-aligned',xlabel='Maximum mesh cell (µm)',ylabel='Resistance including leads (Ω)');axs[1].invert_xaxis();axs[1].legend();axs[1].grid(alpha=.2)
fig.suptitle('Terminal calibration passes; absolute filler convergence remains open')
fig.savefig(ROOT/'docs/assets/terminal-calibration.png',dpi=150);plt.close(fig)
rows=''.join(f'<tr><td>{n}</td><td>{fine[n]["R_ohm"]:.6f}</td><td>{magic[n]["R_ohm"]:.6f}</td><td>{gap[n]:.2f}%</td><td>{change[n]:.2f}%</td></tr>' for n in rails)
section=f'''<section id="terminal-calibration"><h2>Terminal calibration: corrected electrodes and Magic controls</h2>
<p>The reference mesh previously retained half-cell resistance inside each nominal ideal electrode. The corrected mode removes that contribution. Four straight M5 strips now match R = sheet resistance × (length − 0.4 µm) / width at both tested mesh sizes, within 1e-9 relative error. Historical results remain available under the legacy mode.</p>
<img src="assets/terminal-calibration.png" alt="Analytic strip calibration and corrected filler mesh refinement">
<p>Magic's raw strip values instead match the distance between the labels' lower-left x coordinates. This is evidence for a different terminal convention in these controls, not a general characterization of every Magic geometry. SPICE export is 0.0005 Ω higher per resistor in these tests.</p>
<p>Default threshold-zero extraction omits the two wide strips. Forcing every net creates duplicate parallel resistors. A negative threshold with only canonical net names selected recovers one path per strip; this remains a diagnostic recipe, not a production extraction change.</p>
<table><tr><th>Rail</th><th>Corrected 0.25 µm mesh (Ω)</th><th>Earlier Magic control (Ω)</th><th>Difference</th><th>Last mesh change</th></tr>{rows}</table>
<p>The corrected 1 µm hierarchical netlist passes an independent ngspice DC check. Finer runs use matrix solves only. Resolving all via edges at 0.5 µm also passes stitching, with 6,715 seam ports and about 1.1 million nodes per model, but does not establish absolute convergence.</p>
<p><strong>Remaining work:</strong> the corrected fine mesh still differs from Magic by {min(gap.values()):.1f}–{max(gap.values()):.1f}%. Match terminal measurement planes, then isolate bends, parallel layers and vias with analytic controls before qualifying capacitance and device-aware sections. No full-ring RC or optical-performance pass is claimed.</p>
<p><a href="terminal-calibration.md">Reproduction, evidence and next experiment</a>.</p></section>'''
(ROOT/'docs/terminal-calibration.html').write_text(section+'\n')
cp=ROOT/'checkpoints/terminal-calibration';cp.mkdir(exist_ok=True)
files=list(p for p in base.rglob('*') if p.is_file())+[fbase/'geometry.json']
for name in filler:
 files += [p for p in (fbase/name).iterdir() if p.is_file() and (p.suffix in ['.json','.npz','.log'] or name=='electrode-1.0')]
files += [ROOT/p for p in ['scripts/prepare-terminal-calibration.py','scripts/run-terminal-calibration.py','scripts/check-magic-terminal-selection.py','scripts/compare-filler-stitch.py','scripts/report-terminal-calibration.py','docs/terminal-calibration.md','docs/terminal-calibration.html','docs/assets/terminal-calibration.png','simulations/terminal-calibration.json','simulations/ring-sections.json']]
manifest={'scope':summary['scope'],'parent':'checkpoints/filler-stitch/evidence.tar.gz','omissions':'Large fine-mesh SPICE decks are regenerated from geometry and scripts. Fine matrices are retained.','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=cp/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for name in manifest['files']:t.add(ROOT/name,arcname=name)
with tarfile.open(a) as t:
 for name,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==h,name
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(cp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Analytic electrodes, expected negative controls, DC stitching and checkpoint hashes PASS.')
print('Unresolved fine-mesh/Magic gap (%)',gap)
