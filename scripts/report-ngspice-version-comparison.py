"""Publish bounded simulator-version evidence without claiming chip qualification."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile,html,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/ngspice-version-comparison';O=R/'checkpoints/ngspice-version-comparison';O.mkdir(exist_ok=True);stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
results=[json.loads(p.read_text()) for p in sorted((B/'runs').glob('*/result.json'))];audit=json.loads((B/'control-audit.json').read_text()) if (B/'control-audit.json').exists() else None
rows=[]
for x in results:
 rows.append(f"| {x['case']} | {x['version']} | {'Completed' if x['completed'] else 'Failed/incomplete'} | {x['last_time_s']*1e6 if x['last_time_s'] else 0:.3f} µs | {x['seconds']:.1f} s |")
fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
for version in ['46','47']:
 d=B/'runs'/f'capacitor-control-{version}';a=np.loadtxt(d/'tran.dat',skiprows=1)
 axs[0].plot(a[:,0]*1e6,-a[:,2]*1e9,label=f'ngspice {version}')
 m=(a[:,0]>=99.999e-6)&(a[:,0]<=100.005e-6)
 axs[1].plot((a[m,0]-100e-6)*1e9,-a[m,2]*1e9,label=f'ngspice {version}')
axs[0].set(title='Standalone control — both accuracy screens pass',xlabel='Time (µs)',ylabel='Capacitor current (nA)')
axs[1].set(title='Resolved ramp-stop transient',xlabel='Time after ramp stops (ns)',ylabel='Capacitor current (nA)')
for ax in axs:ax.grid(alpha=.2);ax.legend()
fig.suptitle('ngspice 46 / 47 controls agree; network failures are recorded in the table')
fig.savefig(R/'docs/assets/ngspice-version-comparison.png',dpi=160)
control_text='Pending' if not audit else ('PASS' if audit['control_screen_pass'] else 'FAIL')+': '+', '.join(f"v{x['version']} max current error {x['max_native_current_error_A']*1e12:.3f} pA; charge relative error {x['charge_relative_error']:.3g}" for x in audit['cases'])
md=f'''# Controlled ngspice version comparison

Updated {stamp}. **No complete-chip qualification is claimed.**

## Outcome

**The upgrade alone does not resolve the failure.** Both standalone capacitor controls pass. Stock ngspice 46 fails at the first startup point on the unextracted corner; stock ngspice 47 rejects its capacitor multiplier syntax before simulation. On the extracted coupon, both releases parse, then fail at startup in their respective capacitor helper branches. No candidate or new simulator is promoted.

The extracted stock model has no explicit capacitor multipliers, so the new v47 parser error cannot explain its startup failure. The prior custom helper candidate is not rerun in this batch because stock network tests already fail; its earlier failure remains separate evidence.

## Experiment

Both release sources were built in the same pinned OSIC container with GCC, `-O2`, KLU, no X GUI and no readline, using `scripts/build-ngspice-comparison.sh`. The installed simulator and PDK remain unchanged. Exact source/executable hashes and build logs are archived. This pair isolates release changes; it does not assert bitwise equivalence between our rebuilt v46 and the original OSIC binary.

The [official ngspice 47 release](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/) adds a new behavioral-capacitor implementation. In the downloaded source, `src/frontend/inpcom.c` replaces the older E/C/B helper expansion with a G/R/C/V/B network, including a 1e15 Ω terminal resistance and an internal 1e-15 s RC time constant. This is a numerical implementation change with small added effects, not a changed GF180 C(V) equation. The independent control checks remain necessary.

Controls use a stock 25×10 µm MOS capacitor, a 1 kΩ drive, the same 100 µs supply ramp and locally resolved ramp-end breakpoints. The independent reference solves the terminal differential equation and integrates charge. Limits: 100 pA pointwise current, 10 µV voltage, and 1e-5 relative charge error. {control_text}.

Network tests share typical process, 27°C, 100 µs supply ramp to 3.3 V, 2 Ω source resistance, two 1 mA load pulses at 151 µs with 1 ns edges, trapezoidal integration, KLU, 25 ns maximum timestep, reltol 1e-7 and abstol 1e-14. Each network run has a 1,200 s watchdog and no automatic retry. A transient must reach 153 µs with finite data and no analysis error to count as completed.

- **stock-corner:** unchanged foundry `gf180mcu_fd_io__cor` SPICE macro, ideal internal rail connections.
- **extracted-stock:** previously archived extracted corner coupon, stock capacitor model; resistor reduction and lumped capacitance placement are unchanged from the earlier fixture.
- **extracted-candidate:** the separate local helper-normalization experiment, only if run. It is not a stock PDK model.

Within each version pair, the deck and model hashes must match. The stock and extracted circuits have different physical detail, so their responses are not expected to be identical.

| Case | ngspice | Completion | Last saved time | Runtime |
|---|---|---|---|---|
{chr(10).join(rows)}

![Version comparison](assets/ngspice-version-comparison.png)

Completion is a diagnostic milestone. It does not qualify all process/temperature conditions, prove ESD robustness, or replace timestep refinement. Failed partial traces are shown only as diagnostics. Results, terminal comparisons, errors and hashes are in [machine-readable evidence](../simulations/ngspice-version-comparison.json).

## Separate PDK-free parser reproducer

A 15-line circuit with no GF180 dependency reproduces the v47 failure. Default multiplier passes in both releases; explicit `m=1`, `m=8`, and `m=70` pass in v46 but fail in v47 with `unknown parameter (e9)`. The new expansion appends `e9` to an already formatted multiplier. This is a locally reproduced release behavior, not an upstream-confirmed report. See [public issue draft](reviews/ngspice47-cap-multiplier-issue.md); nothing has been posted.

The version comparison rules out a simple switch to unmodified v47 as the solution for this fixture. It does not isolate the cause of the transient convergence failure. Stop this fixed batch; review the small parser example separately from the extracted startup circuit before selecting another bounded hypothesis.

## Remaining qualification

Select the implementation supported by the controls and network evidence. Refine any successful extracted run, compare both capacitance placements, then qualify final-chip startup, repeated frames, PVT and external loading. Final distributed-wire-R extraction and run-specific physical precheck remain separate requirements. No pad redesign follows merely from an older solver's failure.

[Evidence archive](../checkpoints/ngspice-version-comparison/evidence.tar.gz) · [Earlier wafer.space setup audit](wafer-space-version-audit.md).
'''
summary=dict(updated=stamp,runs=results,control_audit=audit,accepted_full_chip=False,upgrade_resolves_failure=False,multiplier_reproducer=json.loads((B/'multiplier-reproducer/results.json').read_text()))
for name in ['stock','extracted','candidate']:
 p=B/f'{name}-results.json'
 if p.exists():summary[name+'_comparison']=json.loads(p.read_text())['comparison']
(R/'simulations/ngspice-version-comparison.json').write_text(json.dumps(summary,indent=2)+'\n');(R/'docs/ngspice-version-comparison.md').write_text(md)
section=f'<section id="ngspice-version-comparison"><h2>Controlled simulator-version comparison</h2><p>{stamp}. The matched ngspice 46/47 controls pass, but both extracted stock-model runs fail at startup. Version 47 also has a separately reproduced capacitor-multiplier parser failure. Upgrade alone does not resolve qualification.</p><p>Independent capacitor control: {html.escape(control_text)}.</p><img src="assets/ngspice-version-comparison.png" alt="Standalone capacitor current controls for both releases, with ramp-stop detail" style="max-width:100%"><p><a href="ngspice-version-comparison.md">Results, methods and remaining gates</a></p></section>'
(R/'docs/ngspice-version-comparison-section.html').write_text(section);(R/'docs/ngspice-version-comparison.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>ngspice comparison</title><style>body{font:17px/1.5 system-ui;max-width:1100px;margin:40px auto;padding:20px}pre{white-space:pre-wrap}</style><body>'+section+'<pre>'+html.escape(md)+'</pre></body></html>')
with tarfile.open(O/'evidence.tar.gz','w:gz') as tf:
 for directory in ['decks','runs','multiplier-reproducer']:
  for p in sorted((B/directory).rglob('*')):
   if p.is_file():tf.add(p,arcname=str(p.relative_to(B)))
 for p in list(B.glob('*.json'))+list(B.glob('*.txt')):
  tf.add(p,arcname=p.name)
 for version in ['46','47']:
  for name in ['config.log','configure.log','make.log','install.log']:
   p=B/f'build-{version}'/name
   if p.exists():tf.add(p,arcname=f'build-{version}/'+name)
 for name in ['reproduce-ngspice47-cap-multiplier.py','build-ngspice-comparison.sh','compare-ngspice-versions.py','analyze-ngspice-control-comparison.py','report-ngspice-version-comparison.py']:
  tf.add(R/'scripts'/name,arcname='scripts/'+name)
(O/'evidence.sha256').write_text(hashlib.file_digest((O/'evidence.tar.gz').open('rb'),'sha256').hexdigest()+'  evidence.tar.gz\n')
print('Published',len(results),'runs',stamp)
