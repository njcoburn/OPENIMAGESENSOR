"""Publish the isolated MOS-capacitor diagnosis and archived evidence."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile,base64,html
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/moscap-branch'
small=json.loads((B/'small.json').read_text());clamp=json.loads((B/'clamp.json').read_text());meta=json.loads((B/'isolation.json').read_text())
integration=json.loads((B/'integration.json').read_text())
refinement=json.loads((B/'refinement.json').read_text())
comparisons=[]
for n in [1,8]:
 for resistance in [1,1000,1000000]:
  for smooth in [False,True]:
   names=[f'small-n{n}-r{resistance}-{a}-{smooth}' for a in [False,True]]
   if not all(next(x for x in small if x['case']==name)['completed'] for name in names):continue
   a,b=[np.loadtxt(B/name/'tran.dat',skiprows=1,ndmin=2) for name in names]
   t=np.unique(np.r_[a[:,0],b[:,0]])
   dv=float(np.max(abs(np.interp(t,a[:,0],a[:,1])-np.interp(t,b[:,0],b[:,1]))))
   di=float(np.max(abs(np.interp(t,a[:,0],a[:,2])-np.interp(t,b[:,0],b[:,2]))))
   comparisons.append(dict(cap_count=n,source_R_ohm=resistance,smooth=smooth,max_voltage_difference_V=dv,max_current_difference_A=di))
fig,axs=plt.subplots(1,2,figsize=(12,4),layout='constrained')
for smooth,label in [(False,'Linear ramp'),(True,'Smooth ramp')]:
 a=np.loadtxt(B/f'small-n8-r1000000-False-{smooth}/tran.dat',skiprows=1)
 axs[0].plot(a[:,0]*1e6,a[:,1],label=label)
axs[0].set(title='Eight MOS capacitors, 1 MΩ drive',xlabel='Time (µs)',ylabel='Capacitor voltage (V)');axs[0].legend()
for row in clamp+integration+refinement['runs']:
 p=B/row['case']/'tran.dat'
 if p.exists():
  a=np.loadtxt(p,skiprows=1,ndmin=2)
  if len(a)>1:axs[1].plot(a[:,0]*1e6,a[:,3],label=row['case'].replace('clamp-','')+(' (complete)' if row['completed'] else ' (incomplete)'))
axs[1].set(title='Isolated extracted clamp: X354 voltage',xlabel='Time (µs)',ylabel='Voltage across X354 (V)');axs[1].legend(fontsize=8)
for ax in axs:ax.grid(alpha=.25)
asset=R/'docs/assets/moscap-branch.png';fig.savefig(asset,dpi=150);plt.close(fig)
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
result=dict(recorded=stamp,small=small,clamp=clamp,integration=integration,refinement=refinement,comparisons=comparisons,isolation=meta)
(R/'simulations/moscap-branch.json').write_text(json.dumps(result,indent=2)+'\n')
summary=f"{sum(x['completed'] for x in small)}/{len(small)} simple capacitor transients complete; {sum(x['completed'] for x in clamp)}/{len(clamp)} initial isolated-clamp transients complete. Integration follow-up: {sum(x['completed'] for x in integration)}/{len(integration)} complete; refinement: {sum(x['completed'] and x.get('rail_refinement_pass',False) for x in refinement['runs'])}/{len(refinement['runs'])} pass."
text=f'''# Isolated MOS-capacitor branch diagnosis

Recorded **{stamp}**. First-chip target: **3×3 demonstrator**.

**{summary}** This is a diagnostic reduction, not full-corner or camera qualification.

![Isolated capacitor and clamp responses](assets/moscap-branch.png)

## What was isolated

The reported device is `X354 a_56346_55631# DVSS_B.t335 cap_nmos_06v0 c_width=25u c_length=10u`. Its foundry model is a voltage-dependent capacitor. The model equations and installed PDK are unchanged.

First, 24 small fixtures exercise one or eight parallel copies, 1 Ω / 1 kΩ / 1 MΩ source resistance, direct or local E/V/F connections, and linear or half-cosine supply ramps. Both ramps reach 3.3 V at 100 µs; runs continue to 153 µs. These are diagnostic excitation choices, not extracted source impedances. The smooth source uses a zero-volt series current sensor; its current sign differs from the linear voltage source, so current comparisons use matching ramp types only.

Second, graph traversal starts from X354 and follows device connections through non-rail resistor-connected nets. This selects **{len(meta['selected_devices'])} device records** and omits {meta['removed_device_count']} other devices. The original rail wiring and all {meta['wiring_caps']} explicit wiring capacitors are retained; resistor-only elimination leaves **{meta['resistors']:,} resistors**. This is a smaller extracted clamp group, not a one-device approximation or a full-corner equivalent. Omitted semiconductor groups and their loading limit interpretation.

Three seeded terminal-voltage checks per retained resistor component verify the second reduction. Maximum relative current error: **{max(c['current_error'] for c in meta['checks']):.3g}**. One-terminal resistor-only dangling components have identically zero port admittance. These checks do not validate omitted semiconductor loading.

The local interface is applied only to MOS-capacitor devices, referenced to each capacitor's own bottom terminal. It enforces the same differential voltage and returns current to the original terminals. It is a simulation formulation, not a physical buffer or a change to the PDK.

## Simple-fixture comparisons

All comparisons below interpolate both adaptive traces onto their union of time points. They are measured differences, not a timestep-refinement or PVT qualification.

| Capacitors | Source R (Ω) | Smooth ramp | Maximum ΔV (V) | Maximum ΔI (A) |
|---:|---:|---|---:|---:|
'''
for c in comparisons:text+=f"| {c['cap_count']} | {c['source_R_ohm']} | {c['smooth']} | {c['max_voltage_difference_V']:.4g} | {c['max_current_difference_A']:.4g} |\n"
text+='\n## Extracted-clamp outcomes\n\n| Fixture | Completed | Last saved time (µs) |\n|---|---|---:|\n'
for c in clamp:
 last=f"{c['last_time_s']*1e6:.6g}" if 'last_time_s' in c else 'No saved trace'
 text+=f"| {c['case']} | {c['completed']} | {last} |\n"
text+='\n'
for c in clamp:
 if not c['completed']:text+=f"- **{c['case']}**: `{c.get('error','Incomplete')}`.\n"
text+='\n## Integration-only follow-up\n\nThese runs retain the direct linear-ramp fixture and change only Gear to first order (backward Euler), or Gear to trapezoidal integration. Devices, parasitics and tolerances are unchanged.\n\n'
for c in integration:
 last=f"{c['last_time_s']*1e6:.6g} µs" if 'last_time_s' in c else 'No saved trace'
 text+=f"- **{c['case']}**: completed={c['completed']}; last saved time={last}. {c.get('error','')}\n"
text+='\n## Trapezoidal refinement\n\nThe completed 100 ns trapezoidal run is compared with 50 ns runs at the original tolerances and at `reltol=1e-7`, `abstol=1e-14`. A 10 µV rail-difference screen is applied over 150–153 µs, including load edges, using the union of adaptive time points. This is a local numerical screen, not ADC accuracy qualification.\n\n'
for c in refinement['runs']:
 text+=f"- **{c['case']}**: completed={c['completed']}; rail comparison pass={c.get('rail_refinement_pass',False)}. "
 if c['completed']:text+=f"Maximum post-startup rail change {c['post_startup_max_difference']['rail_V']*1e6:.6g} µV; MOS-capacitor voltage change {c['post_startup_max_difference']['moscap_V']*1e6:.6g} µV.\n"
 else:text+=c.get('error','Incomplete')+'\n'
text+='''
## Interpretation and next acceptance gate

The standalone MOS capacitor does not reproduce the full-corner startup failure under these tested conditions. The extracted clamp's smooth-ramp case does reproduce the reported X354 branch abort. A smoother supply waveform alone is therefore not an established fix. A simulator's named trouble node identifies where its numerical test failed; it does not prove that device's physical model is defective.

Trapezoidal integration is a candidate because it completes the isolated-clamp load test without circuit changes. Its refinement outcomes above determine whether this local result is numerically repeatable. The 50 ns run at the original tolerances aborts, so the candidate is not accepted even though the 100 ns run completes. Next, use this smaller reproducer to investigate linear-solver conditioning and the internal behavioral-capacitor equations, preserving the foundry model and netlist as the reference. Require repeatable timestep/tolerance checks before returning to the full corner; the isolated group omits other semiconductor loading and cannot qualify the full corner by itself. Preserve failed and timed-out attempts as non-passes. Then repeat the full-corner comparison and integrated 3×3 ADC-load verification. No new layout, DRC/LVS, PVT, optical or fabrication qualification is claimed here.

## Reproduce

```sh
bash scripts/run-tools.sh python3 scripts/diagnose-moscap-branch.py
bash scripts/run-tools.sh python3 scripts/check-moscap-integration.py
bash scripts/run-tools.sh python3 scripts/refine-moscap-trapezoidal.py
bash scripts/run-tools.sh python3 scripts/report-moscap-branch.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Requires the charge-reduction checkpoint and its PDK/container prerequisites. The checkpoint archive includes decks, logs, traces, selection/reduction evidence, scripts and this report.
'''
(R/'docs/moscap-branch.md').write_text(text)
rows=''.join(f"<tr><td>{html.escape(c['case'])}</td><td>{c['completed']}</td><td>{format(c['last_time_s']*1e6,'.6g') if 'last_time_s' in c else 'No saved trace'}</td></tr>" for c in clamp+integration+refinement['runs'])
fragment=f'<section id="moscap-branch"><h2>Isolating the MOS-capacitor startup failure</h2><p>{stamp}. {summary}</p><p>The simple MOS-capacitor fixtures complete. The smaller extracted clamp reproduces the failure. Trapezoidal integration completes at 100 ns but fails the 50 ns refinement. It is not an accepted fix. Outcomes are recorded below and in the detailed report. This diagnostic omits other device groups and does not qualify the full corner.</p><img alt="Isolated capacitor and clamp responses; incomplete traces are marked" src="data:image/png;base64,{base64.b64encode(asset.read_bytes()).decode()}"><table><tr><th>Fixture</th><th>Completed</th><th>Last saved time (µs)</th></tr>{rows}</table><p><a href="moscap-branch.md">Detailed comparisons, limitations and reproduction</a>.</p></section>\n'
(R/'docs/moscap-branch.html').write_text(fragment)
for filename,heading in [('NEXT_STEPS.md','MOS-capacitor isolation handoff'),('CHANGELOG.md','MOS-capacitor isolation'),('COMPLETION_PLAN.md','Latest isolation result')]:
 p=R/filename;s=p.read_text();pos=s.index('\n')+1;p.write_text(s[:pos]+f'\n## {heading} — {stamp}\n\n{summary} [Evidence](docs/moscap-branch.md). Next: investigate solver conditioning and the behavioral-capacitor equations in this reproducer; the trapezoidal candidate failed refinement and is not accepted.\n'+s[pos:])
p=R/'README.md';s=p.read_text();pos=s.index('\n')+1;p.write_text(s[:pos]+f'\n**MOS-capacitor diagnosis ({stamp}):** {summary} [Report and plots](docs/moscap-branch.md).\n'+s[pos:])
pdk=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice')
(B/'pdk-provenance.json').write_text(json.dumps(dict(path=str(pdk),sha256=hashlib.sha256(pdk.read_bytes()).hexdigest()),indent=2)+'\n')
C=R/'checkpoints/moscap-branch';C.mkdir(exist_ok=True)
files=sorted(p for p in list(B.rglob('*'))+[R/n for n in ['scripts/diagnose-moscap-branch.py','scripts/report-moscap-branch.py','scripts/check-moscap-integration.py','scripts/refine-moscap-trapezoidal.py','docs/moscap-branch.md','docs/moscap-branch.html','docs/assets/moscap-branch.png','simulations/moscap-branch.json','checkpoints/pad-closure/ngspice-init/.spiceinit']] if p.is_file())
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(C/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(C/'evidence.tar.gz') as tar:
 for item in tar:assert hashlib.sha256(tar.extractfile(item).read()).hexdigest()==hashes[item.name]
(C/'manifest.json').write_text(json.dumps(dict(recorded=stamp,files=hashes,archive_sha256=hashlib.sha256((C/'evidence.tar.gz').read_bytes()).hexdigest()),indent=2)+'\n')
print(summary,'Archive verified.')
