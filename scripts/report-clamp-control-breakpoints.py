"""Publish the bounded control-resolution result, including charge bookkeeping."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/clamp-control-breakpoints';O=R/'checkpoints/clamp-control-reference';O.mkdir(exist_ok=True)
r=json.loads((B/'result.json').read_text());a=json.loads((O/'analysis.json').read_text());stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
Q=lambda v:25e-6*10e-6*(.001107*v+.00107/6.25*(np.logaddexp(6.25*v-4.1875,-6.25*v+4.1875)-np.logaddexp(-4.1875,4.1875)))
charge={};fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for kind in ['original','scaled']:
 old=np.loadtxt(R/'build/clamp-model-review'/('control-'+kind)/'tran.dat',skiprows=1);m=abs(old[:,0]-100e-6)<30e-9;axs[0].plot((old[m,0]-100e-6)*1e9,-old[m,2]*1e9,'o-',label=kind,markersize=3)
 for ps in [50,25]:
  name=f'{kind}-{ps}ps';p=B/name/'tran.dat'
  if not p.exists():continue
  z=np.loadtxt(p,skiprows=1);tt=np.r_[0.,z[:,0]];ii=np.r_[0.,-z[:,2]];integrated=float(np.trapezoid(ii,tt));exact=float(Q(z[-1,1]));charge[name]=dict(integrated_source_charge_C=integrated,terminal_equation_charge_C=exact,charge_residual_C=integrated-exact,relative_charge_residual=(integrated-exact)/exact,wave_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  m=(z[:,0]>=99.998e-6)&(z[:,0]<=100.006e-6);axs[1].plot((z[m,0]-100e-6)*1e9,-z[m,2]*1e9,label=f'{kind} {ps} ps',alpha=.75)
for ax in axs:ax.set(xlabel='Time after ramp stops (ns)',ylabel='Capacitor current (nA)');ax.grid(alpha=.2);ax.legend()
axs[0].set_title('Archived coarse controls: inaccurate settling');axs[1].set_title('Same source waveform, locally resolved settling')
fig.suptitle('Standalone control comparison — not full-chip qualification');fig.savefig(R/'docs/assets/clamp-control-breakpoints.png',dpi=160)
r['charge_bookkeeping']=charge;r['recorded']=stamp;r['charge_scope']='Numerical source-current quadrature versus analytic integral of C(V); report only, not all-corner charge qualification.'
(R/'simulations/clamp-control-breakpoints.json').write_text(json.dumps(r,indent=2)+'\n');(O/'breakpoints.json').write_text(json.dumps(r,indent=2)+'\n')
clamp=next((x for x in r['runs'] if x['case']=='clamp-scaled-50ns'),None)
clamptext='Not run because a control gate failed.' if clamp is None else ('Completed; still requires refinement, equivalence and full-chip regression.' if clamp['completed'] else 'Incomplete: '+clamp['error'])
rows='\n'.join(f"| {ps} ps local spacing | {r['comparisons'][str(ps)]['max_pair_A']*1e12:.3f} pA | {max(r['comparisons'][str(ps)]['max_native_reference_A'].values())*1e12:.3f} pA | {'Pass' if r['comparisons'][str(ps)]['passes'] else 'Fail'} |" for ps in [50,25] if str(ps) in r['comparisons'])
md=f'''# Complete-chip electrical qualification: capacitor-control resolution audit

Recorded **{stamp}**. **Full-chip qualification remains open.** No chip geometry or PDK file changed.

## What we learned

The previous 2.708 nA original/scaled control difference is concentrated just after the 100 µs supply-ramp stop. An independent stiff ODE integration of the exact standalone terminal equation shows native-point current errors of 2.033 nA (original) and 1.692 nA (scaled). This is not merely interpolation between different time grids. The capacitor's high-voltage RC time constant is only **0.544 ns**, compared with the archived maximum step of 100 ns.

The reference integrates `C(Vg) dVg/dt = (Vs − Vg)/1000`, using the actual typical-corner equation and unchanged source. Its state is the resistor voltage drop to avoid cancellation. Two reference accuracies agree to {a['reference_refinement_max_A']*1e12:.4f} pA on the comparison grid. This is an independent numerical reference, not a foundry validation.

![Original traces and independent reference](assets/clamp-control-reference.png)

## Bounded new test and results

Inserted collinear PWL source points at **50 ps and 25 ps**, from 99.995 to 100.030 µs. These points preserve the original piecewise-linear waveform but give ngspice breakpoints around the short transient. Model equations, source resistance, simulator method/tolerances, and the original 100 pA current / 10 µV voltage comparison limits were retained. Exactly four controls ran; no retries or parameter search.

| Matched pair | Maximum pairwise current difference | Maximum native-point error versus reference | Existing current gate |
|---|---:|---:|---|
{rows}

Original and scaled resolution comparisons are also checked against 100 pA. All edge samples remain included; the ramp-stop interval is not excluded from acceptance.

![Resolved capacitor control comparison](assets/clamp-control-breakpoints.png)

**Gated extracted-clamp result:** {clamptext}

The clamp diagnostic used the prior 50 ns deck and the previously proposed internally rescaled capacitor. It did not inherit the standalone's added PWL points, change physical parasitics or relax tolerances. Its watchdog was 120 seconds. No further runs are authorized by this script after that bounded trial.

## Charge bookkeeping and limits

Integrating the source current from zero and comparing against the analytic integral of C(V) gives a maximum relative charge residual of {max(abs(x['relative_charge_residual']) for x in charge.values()):.3g} across the four saved controls. This includes output-grid quadrature error and does not establish general terminal charge equivalence, other corners or full-clamp behavior. Exact values and waveform hashes are in [the JSON results](../simulations/clamp-control-breakpoints.json).

**No accepted full-chip fix.** Passing the standalone gate only removes a false lead from the earlier coarse comparison. Full-clamp completion/refinement, both parasitic placements, final post-fill extraction, startup, repeated frames, PVT and external-load qualification remain required. ESD robustness is not established by these transients.

## Next concrete gate

Review this new evidence with the existing extracted-clamp reproducer. If the gated clamp remains incomplete, do not treat the control success as a reason for additional blind solver sweeps. Obtain a specific supported diagnosis of the extracted fixture before promoting a model change. The independent reviewer has not been contacted; the public issue remains a local draft.

## Reproduction

```bash
bash scripts/run-tools.sh python3 scripts/audit-clamp-control-reference.py
bash scripts/run-tools.sh python3 scripts/check-clamp-control-breakpoints.py
bash scripts/run-tools.sh python3 scripts/report-clamp-control-breakpoints.py
```

The second command has the fixed five-run maximum described above. The first analyses saved traces only. [Archived evidence](../checkpoints/clamp-control-reference/evidence.tar.gz).

Background: [ngspice manual, transient options and PWL sources](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf). The measured errors and conclusions above come from the local traces and independent terminal equation, not from a claimed upstream bug report.
'''
(R/'docs/clamp-control-reference.md').write_text(md)
# Self-contained concise HTML summary; full technical detail remains in the Markdown report.
section=f'<section id="clamp-control-reference"><h2>Electrical qualification: resolved capacitor controls</h2><p>{stamp}. The archived control missed a 0.544 ns settling transient. Local 50/25 ps source breakpoints preserve the physical waveform and resolve the original/scaled comparison; the original acceptance limits remain unchanged.</p><img src="assets/clamp-control-breakpoints.png" alt="Coarse and locally resolved capacitor current traces" style="max-width:100%"><p><strong>Extracted clamp:</strong> {clamptext}</p><p><strong>Full-chip electrical qualification remains open.</strong> <a href="clamp-control-reference.md">Detailed analysis and next gate</a>.</p></section>'
(R/'docs/clamp-control-reference-section.html').write_text(section)
(R/'docs/clamp-control-reference.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Capacitor control audit</title><style>body{font:17px/1.5 system-ui;max-width:1100px;margin:40px auto;padding:20px}</style><body>'+section+'</body></html>')
with tarfile.open(O/'evidence.tar.gz','w:gz') as tf:
 for p in sorted(B.rglob('*')):
  if p.is_file():tf.add(p,arcname='breakpoints/'+str(p.relative_to(B)))
 for p in [*(R/'build/clamp-model-review/control-original').glob('*'),*(R/'build/clamp-model-review/control-scaled').glob('*'),R/'build/clamp-model-review/expanded.log',O/'analysis.json',O/'breakpoints.json',R/'scripts/audit-clamp-control-reference.py',R/'scripts/check-clamp-control-breakpoints.py',R/'scripts/report-clamp-control-breakpoints.py']:
  tf.add(p,arcname='audit/'+(p.parent.name+'/' if p.parent.name.startswith('control-') else '')+p.name)
print(clamptext);print('Charge residuals',charge);print('Wrote report, plots and evidence archive')
