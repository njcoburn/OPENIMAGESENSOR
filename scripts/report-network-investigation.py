"""Publish source-level reduction controls and bounded device-aware patch regressions."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'build/network-investigation'
read=lambda p:json.loads(p.read_text())
construction=read(base/'construction-verification.json');device=read(base/'device-export/regression.json');reduced=read(base/'device-export/reduced-regression.json');prior=read(ROOT/'simulations/extraction-diagnostics.json')
for case in ['two_end_columns','all_cuts']:
 assert abs(construction[case+'-normal']['R_ohm']/prior['via_controls'][case]['raw_ohm']-1)<1e-6
 assert abs(construction[case+'-fixed']['R_ohm']/construction[case+'-unreduced']['R_ohm']-1)<2e-6
 assert abs(construction[case+'-fixed']['ngspice_R_ohm']/construction[case+'-fixed']['R_ohm']-1)<1e-7
for case in ['buffer','hierarchy']:
 assert device[case]['nonresistor_records_identical_ignoring_cap_names_and_order']
 assert all(reduced['cases'][case][m]['pass'] for m in ['baseline','patched'])
 assert reduced['cases'][case]['max_buffer_difference_V']<1e-4
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
commit='381714e2d5debf2ded71c5a6b6604e6b936422cf';source=f'https://github.com/RTimothyEdwards/magic/blob/{commit}/resis/ResMerge.c'
summary={'recorded':stamp,'source_commit':commit,'triangle_offset_cause_confirmed_on_two_controls':True,'construction':construction,'device_export_audit':device,'reduced_RC_transients':reduced,'reader_and_triangle_patches_tested_separately':True,'combined_patch_production_qualification':False,'production_tools_or_netlists_changed':False,'full_RC_qualified':False,'trace_binary_sha256':hashlib.sha256((base/'magic-trace').read_bytes()).hexdigest(),'triangle_candidate_binary_sha256':hashlib.sha256((base/'magic-reduction-fixed').read_bytes()).hexdigest()}
(ROOT/'simulations/network-investigation.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axs=plt.subplots(1,3,figsize=(16,5),layout='constrained')
labels=['20 vias','300 vias'];cases=['two_end_columns','all_cuts'];x=np.arange(2)
for dx,kind,label in [(-.24,'normal','Normal reduction'),(0,'unreduced','Construction retained'),(.24,'fixed','Triangle candidate')]:axs[0].bar(x+dx,[construction[c+'-'+kind]['R_ohm'] for c in cases],.24,label=label)
axs[0].set(xticks=x,xticklabels=labels,ylabel='Raw equivalent resistance (Ω)',title='Construction reduction changes the answer');axs[0].legend(fontsize=8);axs[0].grid(axis='y',alpha=.2)
d=base/'device-export/buffer-reduced';a=np.loadtxt(d/'baseline-wave.txt',skiprows=1);b=np.loadtxt(d/'patched-wave.txt',skiprows=1)
axs[1].plot(a[:,0]*1e6,a[:,1],label='Baseline');axs[1].plot(b[:,0]*1e6,b[:,1],'--',label='Reader patch');axs[1].set(xlabel='Time (µs)',ylabel='Buffer output (V)',title='Nominal extracted-buffer transient');axs[1].legend();axs[1].grid(alpha=.2)
for case in ['buffer','hierarchy']:
 d=base/'device-export'/(case+'-reduced');a=np.loadtxt(d/'baseline-wave.txt',skiprows=1);b=np.loadtxt(d/'patched-wave.txt',skiprows=1);axs[2].plot(a[:,0]*1e6,(np.interp(a[:,0],b[:,0],b[:,1])-a[:,1])*1e6,label=case)
axs[2].set(xlabel='Time (µs)',ylabel='Patched − baseline output (µV)',title='Reader-patch effect under stated conditions');axs[2].legend();axs[2].grid(alpha=.2)
fig.savefig(ROOT/'docs/assets/network-investigation.png',dpi=150);plt.close(fig)
rows=''.join(f'<tr><td>{c}</td><td>{construction[c+"-normal"]["R_ohm"]:.9f}</td><td>{construction[c+"-unreduced"]["R_ohm"]:.9f}</td><td>{construction[c+"-fixed"]["R_ohm"]:.9f}</td></tr>' for c in cases)
body='''The two-layer error is caused by construction-time reduction in these controls. Turning off final simplification does not disable ResDoneWithNode, which performs series, parallel and triangle reductions as the graph is built. Instrumentation retains 24 resistors for the 20-via control and 360 for the 300-via control. Independent matrix and ngspice solves agree on their unreduced resistance.

Both implementations of triangle-to-star conversion in ResTriangleCheck add 0.5 to each new floating-point branch resistance in milliohms. A separate six-line candidate removes those additions while retaining normal reduction. Its one-resistor outputs match the unreduced networks within 2e-6 relative, including printed precision, and recover the expected falling resistance when more vias are added. This confirms the cause on these two layouts; it is not broad qualification of all reduction cases.

The reader patch was tested separately on the actual output-buffer extraction and a synthetic parent containing two copies of that extracted cell. Each child has three PFETs, 19 extracted resistors and 150,473 capacitor records. Device parameters, capacitor connectivity/values and hierarchy are preserved. Capacitor names and order vary between runs, so comparisons use normalized multisets. The standalone diagnostic must apply the PDK's scalegrid 1 10 startup setting; omitting it changes device diffusion areas/perimeters. The corrected unmodified export matches the saved original buffer netlist after normalization.

Direct fill-heavy RC transient attempts use a 90-second watchdog, and their status is retained separately. Passing transient evidence uses the project's existing audited Schur capacitance reduction: eliminate 21,085 charge-neutral floating fill nodes and retain 276 capacitors. The capacitor network is unchanged by the reader patch; the raw baseline matches the previously audited source. No artificial shunt is added to these reduced-model tests.

All four reduced-model transients complete: baseline and reader-patched exports, each in the single-buffer and two-instance configurations. Conditions are nominal process, 27 °C default temperature, 3.3 V supply, 40 µA reference per buffer, a 0.7-to-0.9 V input step, 100 pF load and 6 µs duration. The maximum baseline/patched output difference is about 0.05 µV; the 100 µV comparison limit is a regression screen, not an ADC accuracy specification. The second hierarchical instance has a static 0.8 V input. These tests do not establish corner, noise, startup or whole-camera performance.

The reader and triangle candidates remain separate diagnostic builds. Installed tools, production netlists and layout files are unchanged. Next: combine the two corrections in one isolated build, re-extract representative device-aware blocks, and repeat topology/LVS and corner/transient checks before adopting any tool change. Then resume device-aware ring RC, including the outstanding substrate and negative-capacitance checks.'''
html=f'<section id="network-investigation"><h2>Triangle-reduction cause confirmed; device-aware reader tests</h2><p>{stamp}</p><img src="assets/network-investigation.png" alt="Normal, unreduced and corrected networks, buffer transient and reader-patch waveform differences"><table><tr><th>Control</th><th>Normal Ω</th><th>Unreduced Ω</th><th>Triangle candidate Ω</th></tr>{rows}</table>'+''.join('<p>'+p+'</p>' for p in body.split('\n\n'))+f'<p><a href="{source}#L612">Pinned reduction source</a> · <a href="network-investigation.md">Reproduction, timeout records and evidence</a>.</p></section>\n'
(ROOT/'docs/network-investigation.html').write_text(html)
md=f'# Construction reduction and device-aware patch tests\n\nRecorded **{stamp}**.\n\n![Network and buffer comparisons](assets/network-investigation.png)\n\n'+body+'\n\n## Construction results\n\n| Via control | Normal Ω | Unreduced Ω | Triangle candidate Ω |\n| --- | ---: | ---: | ---: |\n'
for c in cases:md+=f'| {c} | {construction[c+"-normal"]["R_ohm"]:.9f} | {construction[c+"-unreduced"]["R_ohm"]:.9f} | {construction[c+"-fixed"]["R_ohm"]:.9f} |\n'
md+='\n## Direct raw-network attempts\n\n'
for case in ['buffer','hierarchy']:
 for mode,r in device[case]['simulations'].items():md+=f'- {case}, {mode}: **{r["status"]}**. '+r.get('detail','')+'\n'
md+='\nThe direct attempts included a 1e12 Ω numerical shunt per node; the passing reduced tests did not. No direct raw-network pass is inferred from export-preservation checks.\n'
md+=f'\n## Source and patches\n\n- [Pinned triangle-reduction source]({source}#L612), with a second branch at line 747.\n- [Triangle candidate](../patches/magic-8.3.664-triangle-offset.patch).\n- [Instrumentation only](../patches/magic-8.3.664-construction-trace.patch).\n- [Previously tested reader patch](../patches/magic-8.3.664-resistor-reader.patch).\n'
md+='''
## Reproduce

Start from the [export-diagnostic checkpoint](extraction-diagnostics.md) and its configured source checkout. The build script requires the pinned commit and a clean source tree, uses the existing local build configuration, and restores the source after saving diagnostic binaries. No system installation is performed.

```sh
bash scripts/run-tools.sh bash scripts/build-network-diagnostic.sh
bash scripts/run-tools.sh python3 scripts/run-network-trace.py
bash scripts/run-tools.sh python3 scripts/run-network-trace.py --fixed
bash scripts/run-tools.sh python3 scripts/solve-construction-trace.py
bash scripts/run-tools.sh python3 scripts/verify-construction-networks.py
bash scripts/run-tools.sh python3 scripts/check-device-export.py
bash scripts/run-tools.sh python3 scripts/audit-device-export.py
bash scripts/run-tools.sh python3 scripts/check-reduced-device-export.py
bash scripts/run-tools.sh python3 scripts/report-network-investigation.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The direct raw-network audit may take four 90-second watchdog intervals. The reduced regression reuses the audited buffer capacitance matrix only after verifying the raw source hash and normalized baseline netlist; it preserves the resistor/device topology and substitutes the newly exported resistor values.

`checkpoints/network-investigation/evidence.tar.gz` contains inputs, trace outputs, netlists, waveforms, logs, scripts and candidate patches. The manifest verifies SHA-256 hashes. Diagnostic executables and the source checkout are omitted; binary hashes and the source commit are recorded. Extract into a separate directory. No upstream issue or PR has been submitted. These are local investigation results, not fabrication signoff.
'''
(ROOT/'docs/network-investigation.md').write_text(md)
cp=ROOT/'checkpoints/network-investigation';cp.mkdir(exist_ok=True)
files=[p for p in base.rglob('*') if p.is_file() and p.name not in ['magic-trace','magic-reduction-fixed']]
files += [ROOT/p for p in ['scripts/prepare-network-trace.py','scripts/build-network-diagnostic.sh','scripts/run-network-trace.py','scripts/solve-construction-trace.py','scripts/verify-construction-networks.py','scripts/check-device-export.py','scripts/audit-device-export.py','scripts/check-reduced-device-export.py','scripts/report-network-investigation.py','patches/magic-8.3.664-construction-trace.patch','patches/magic-8.3.664-triangle-offset.patch','docs/network-investigation.md','docs/network-investigation.html','docs/assets/network-investigation.png','simulations/network-investigation.json','build/buffer-pex/buffer_rc.spice','build/buffer-pex/buffer_reduced.spice','build/buffer-pex/reduction.json']]
manifest={'source_commit':commit,'parent':'checkpoints/extraction-diagnostics/evidence.tar.gz','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}}
a=cp/'evidence.tar.gz'
with tarfile.open(a,'w:gz',compresslevel=3) as t:
 for n in manifest['files']:t.add(ROOT/n,arcname=n)
with tarfile.open(a) as t:
 for n,h in manifest['files'].items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h
manifest['archive_sha256']=hashlib.sha256(a.read_bytes()).hexdigest();(cp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Construction cause confirmed on two controls; device records preserved; four reduced-RC transients pass. Combined-patch qualification remains open.')
