"""Publish reduction and placement sensitivity, preserving incomplete simulations."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile,base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reduced'
red=json.loads((B/'summary.json').read_text());audit=json.loads((B/'audit.json').read_text());placement=json.loads((B/'placement.json').read_text());fine=json.loads((B/'refinement.json').read_text());startup=json.loads((B/'corner-full/startup-placement.json').read_text())
assert len(red)==4 and len(audit)==4 and len(fine['runs'])==6
complete=all(v['completed'] for v in startup['runs'])
if complete:
 aa,bb=[np.loadtxt(B/'corner-full'/f'startup-{m}'/'tran.dat',skiprows=1,ndmin=2) for m in ['nominal','remote']]
 tt=np.unique(np.r_[aa[:,0],bb[:,0]])
 startup['max_entire_startup_placement_difference_V']=max(float(np.max(abs(np.interp(tt,aa[:,0],aa[:,i])-np.interp(tt,bb[:,0],bb[:,i])))) for i in [1,2])
 startup['preload_drift_149_to_150us_V']={m:[float(np.interp(150e-6,a[:,0],a[:,i])-np.interp(149e-6,a[:,0],a[:,i])) for i in [1,2]] for m,a in [('nominal',aa),('remote',bb)]}
maxcurrent=max(x['max_relative_current_error'] for r in red.values() for x in r['component_checks']);maxenergy=max(x['max_relative_energy_error'] for r in red.values() for x in r['component_checks']);maxdc=max(x['relative_error'] for r in audit.values() for x in r['dc'].values())
# AC corner comparison is independently available even if the subsequent transient aborted.
acrows=[]
for m in ['nominal','remote']:
 a=np.loadtxt(B/'corner-full'/f'practical-{m}'/'ac.dat',skiprows=1,ndmin=2);assert np.isfinite(a).all() and a[-1,0]>=.999e9;acrows.append(a)
a,b=acrows;delta=np.maximum(abs((a[:,1]+1j*a[:,2])-(b[:,1]+1j*b[:,2])),abs((a[:,3]+1j*a[:,4])-(b[:,3]+1j*b[:,4])))
corner_ac={'max_complex_transfer_change_through_1MHz':float(np.max(delta[a[:,0]<=1e6])),'max_complex_transfer_change_through_1GHz':float(np.max(delta))}
fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained');names=list(red);x=np.arange(4)
axs[0].bar(x-.18,[red[n]['original_resistors'] for n in names],.36,label='Original R network',color='#637b8d');axs[0].bar(x+.18,[red[n]['reduced_resistors'] for n in names],.36,label='Schur reduction',color='#16887d');axs[0].set(yscale='log',xticks=x,xticklabels=names,ylabel='Resistor count (log scale)',title='Devices and both capacitor placements retained');axs[0].tick_params(axis='x',labelrotation=20);axs[0].legend(fontsize=8)
for c in ['fill10-full','fill10-metal','corner-metal']:
 aa,bb=[np.loadtxt(B/c/f'refine-{m}'/'tran.dat',skiprows=1) for m in ['nominal','remote']];t=np.unique(np.r_[aa[:,0],bb[:,0]]);dv=np.maximum(*[abs(np.interp(t,aa[:,0],aa[:,i])-np.interp(t,bb[:,0],bb[:,i])) for i in [1,2]]);sel=(t>=.998e-6)&(t<=1.02e-6);axs[1].plot((t[sel]-1e-6)*1e9,dv[sel]*1e6,label=c)
axs[1].set(xlabel='Time from load-step start (ns)',ylabel='Placement difference (µV)',title='Refined edge response; full corner shown separately');axs[1].legend(fontsize=8)
for ax in axs:ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
asset=R/'docs/assets/charge-reduction.png';fig.savefig(asset,dpi=150);plt.close(fig)
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
result={'recorded':stamp,'reduction':red,'serialized_audit':audit,'initial_placement':placement,'refinement':fine,'corner_ac':corner_ac,'corner_startup':startup,'max_relative_current_error':maxcurrent,'max_relative_energy_error':maxenergy,'max_relative_DC_resistance_error':maxdc,'scope':'Exact resistor-only elimination within numerical tolerance. Two lumped capacitor anchors are sensitivity probes, not a worst-case bound. First release remains 3x3.'}
(R/'simulations/charge-reduction.json').write_text(json.dumps(result,indent=2)+'\n')
rows='\n'.join(f"| {c} | {v['original_resistors']:,} | {v['reduced_resistors']:,} | {v['eliminated_nodes']:,} |" for c,v in red.items())
sens='\n'.join(f"| {c} | {fine['comparisons'][c]['refined_max_placement_difference_V']*1e6:.3f} | {max(v['max_timestep_change_V'] for v in fine['runs'] if v['case']==c)*1e6:.3f} |" for c in fine['comparisons'])
status=(f"Both full-corner supply-ramp runs complete. Their maximum post-startup placement difference is **{startup['max_post_startup_difference_V']*1e6:.3f} µV**; sampled difference at 151.5 µs is {startup['load_sample_difference_V']} V. This longer fixture has not yet received its own timestep refinement; full-startup differences, pre-load voltages and settling drift are retained in the JSON." if complete else 'Both full-corner supply-ramp runs abort just after 100 µs in `e.x354.ec_moscap#branch`, before the 151 µs load pulse. They are not transient passes. The complete AC sweeps remain valid, but full-corner transient placement sensitivity is unverified.')
nextstep=('Refine the completed full-corner startup/load test numerically, then assemble the accepted reduced coupon model into a representative ring segment and repeat integrated 3×3 ADC-load simulations.' if complete else 'Test the voltage/current-preserving interface already used in the earlier clamp-convergence work around the corner macro, and verify its terminal equivalence. Resolve the MOS-capacitor startup abort before refining the full-corner load comparison and integrating the 3×3 model.')
text=f'''# Resistor reduction and capacitance-placement sensitivity

Recorded **{stamp}**. Release target: **3×3 demonstrator**.

**All four resistor networks are reduced and verified.** Six short placement transients and their six half-timestep refinements complete. The full corner needs a separate nonlinear startup treatment; its result is reported below.

![Network reduction and refined placement response](assets/charge-reduction.png)

## Reduction results

| Coupon | Original R | Reduced R | Eliminated nodes |
|---|---:|---:|---:|
{rows}

The Schur complement eliminates only nodes connected exclusively through resistors. Ports, all semiconductor terminals, and capacitor terminals for **both** placements remain. Thus this reduction introduces no frequency-dependent approximation for the stated reference circuit; it is subject to numerical precision. Device records and capacitor values are unchanged.

Three independent terminal-voltage excitations per resistor component compare original and reduced currents and power. Maximum relative current error: **{maxcurrent:.3g}**; energy error: **{maxenergy:.3g}**. The serialized models additionally pass 16 DC rail-resistance comparisons, maximum relative error **{maxdc:.3g}**, and preserve the original capacitance-pair matrix for both placements. No new layout/LVS/DRC run is claimed; device records retain the preceding topology evidence.

## Placement experiment

The nominal model uses the original named node, or nearest recorded resistor-node coordinate when that name was eliminated. The alternate moves each lumped capacitor anchor to the most distant recorded coordinate **within the same original resistor-connected net**. Both preserve the original R-collapsed capacitance matrix. This is a deliberately different geometric placement, not a proven physical worst-case bound or a distributed field-extracted capacitance model.

The short fixture uses 3.3 V at 27 °C, a shared 2 Ω source, two 100 kΩ standby loads, and simultaneous 1 mA-per-rail load pulses with 1 ns edges. Full coupons retain their PDK devices. In metal-only fixtures the implicit substrate is explicitly grounded. No package inductance is included.

| Completed short fixture | Refined maximum placement change (µV) | Largest 1 ns→0.5 ns timestep change (µV) |
|---|---:|---:|
{sens}

The full filler's placement difference is comparable to its numerical variation, so its few-microvolt peak is not accurately resolved. The metal-only corner's approximately 76 µV edge difference is much larger than its timestep variation. Late samples at 1.5 µs agree to saved precision in these short fixtures. This is rail behavior in a chosen fixture, not pixel/ADC error qualification.

## Full-corner solver and startup results

The full corner's AC sweeps complete using KLU. Maximum complex voltage-transfer difference is **{corner_ac['max_complex_transfer_change_through_1MHz']:.5g} V/V through 1 MHz**, and **{corner_ac['max_complex_transfer_change_through_1GHz']:.5g} V/V through 1 GHz**. The wide sweep is diagnostic, not a claim that the lumped PDK model is physically valid to 1 GHz.

The initial hierarchical and flat SPARSE runs timed out. KLU completed AC, but transients starting from the DC solution aborted at time zero in a MOS-capacitor controlled-source branch. Those attempts are retained as non-passes. Using rail `.nodeset` guesses and the earlier practical clamp settings did not establish a completed DC-start transient.

The separate supply-ramp fixture uses the repository's GF180 clamp initialization (`ngbehavior=hsa`, `wnflag=1`), KLU, one simulator thread, `gmin=1e-17`, `abstol=1e-12`, `reltol=1e-6`, and zero-charge startup (`uic`). It ramps the supply over 100 µs, holds until a 1 mA-per-rail pulse at 151 µs, and runs to 153 µs with a 100 ns maximum step and adaptive steps at the 1 ns pulse edges. This fixture is explicitly different from the short DC-start experiment.

{status}

Two bounded-degree star-mesh alternatives were also electrically verified, but retained 512,726 and 533,044 resistors and were not selected. An energy-bound sparsity inspection found that a tight bound removes too few dense edges to solve the performance issue; no resistor pruning was applied.

## Next acceptance gate

{nextstep}

The placement probe is not a manufacturing guarantee. Substrate-domain interpretation, accurate spatial capacitance, native Magic capacitance-export accounting, and full-chip qualification remain open. The first release remains the 3×3 demonstrator. Production GDS and installed tools are unchanged.

## Reproduce

Prerequisite: the charge-reference checkpoint and its original extraction dependencies.

```sh
bash scripts/run-tools.sh python3 scripts/reduce-charge-reference.py
bash scripts/run-tools.sh python3 scripts/audit-charge-reduction.py
bash scripts/run-tools.sh python3 scripts/check-charge-placement.py
# The command above retains the full-corner timeout as a non-pass.
bash scripts/run-tools.sh python3 scripts/refine-charge-placement.py
bash scripts/run-tools.sh python3 scripts/check-charge-placement.py --practical-corner
# This DC-start attempt retains the MOS-capacitor transient abort.
bash scripts/run-tools.sh python3 scripts/check-corner-placement-startup.py
bash scripts/run-tools.sh python3 scripts/report-charge-reduction.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The checksummed evidence archive includes the reductions, placement maps, simulator decks/logs/waveforms, failed attempts and scripts. Large parent reference inputs remain in the charge-reference checkpoint, linked by source hashes.
'''
(R/'docs/charge-reduction.md').write_text(text)
html=f'''<section id="charge-reduction"><h2>Verified resistor reduction and placement sensitivity</h2><p>{stamp}. The full corner is reduced from 571,551 to 87,748 resistors, with device and capacitor terminals preserved. Four reductions pass current/energy checks and 16 DC comparisons.</p><img src="data:image/png;base64,{base64.b64encode(asset.read_bytes()).decode()}" alt="Resistor count reduction and refined capacitor-placement sensitivity"><p>Six short transients and six refinements complete. The metal-only corner shows about 76 µV placement sensitivity at the load edge. The full filler's smaller effect is comparable to numerical variation.</p><p>{status}</p><p><b>Next:</b> {nextstep} <a href="charge-reduction.md">Evidence and limitations</a>.</p></section>'''
(R/'docs/charge-reduction.html').write_text(html)
for name,marker,entry in [
 ('README.md','## 3×3 release: charge-conserving RC reference',f'## 3×3 verification: reduced RC and placement sensitivity\n\nFour resistor reductions pass numerical and DC checks. Full corner: 571,551 → 87,748 resistors; metal-only corner: 451,892 → 12. Placement sensitivity is now measured in coupon fixtures, with numerical and startup limits retained. [Results](docs/charge-reduction.md).\n\n![RC reduction and placement response](docs/assets/charge-reduction.png)\n\n'),
 ('NEXT_STEPS.md','## Charge-reference handoff',f'## Reduced-RC handoff — {stamp}\n\nFour reductions pass current/energy and 16 DC checks; six short placement transients plus six refinements complete. Full-corner DC-start transient fails in a nonlinear MOS-capacitor model. Supply-ramp completion: {complete}. Next: {nextstep} [Detailed result](docs/charge-reduction.md).\n\n'),
 ('CHANGELOG.md','## ',f'## {stamp} — Verified resistor reduction and placement probes\n\nReduced four reference networks with preserved capacitance/device records and 16 DC comparisons. Added AC/load-step comparisons, half-step refinements, and retained failed full-corner startup attempts. Supply-ramp completion: {complete}. [Report](docs/charge-reduction.md).\n\n')]:
 p=R/name;s=p.read_text()
 if 'charge-reduction.md' not in s:p.write_text(s.replace(marker,entry+marker,1))
p=R/'COMPLETION_PLAN.md';s=p.read_text();s=__import__('re').sub(r'Updated \*\*.*?\*\*\.',f'Updated **{stamp}**.',s,count=1);start=s.index('## Immediate next task');end=s.index('\nNo additional host tools',start);s=s[:start]+f'## Immediate next task\n\n{nextstep} The [reduction report](docs/charge-reduction.md) preserves all successful and failed checks and the placement approximation.\n'+s[end:];p.write_text(s)
checkpoint=R/'checkpoints/charge-reduction';checkpoint.mkdir(exist_ok=True)
files=[p for p in B.rglob('*') if p.is_file()]
files += [R/p for p in ['scripts/reduce-charge-reference.py','scripts/audit-charge-reduction.py','scripts/check-charge-placement.py','scripts/refine-charge-placement.py','scripts/check-corner-placement-startup.py','scripts/reduce-corner-sparse.py','scripts/inspect-corner-sparsity.py','scripts/report-charge-reduction.py','simulations/charge-reduction.json','docs/charge-reduction.md','docs/assets/charge-reduction.png','COMPLETION_PLAN.md','checkpoints/pad-closure/ngspice-init/.spiceinit']]
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};archive=checkpoint/'evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(archive) as tar:
 for name,digest in manifest.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
(checkpoint/'manifest.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':manifest},indent=2)+'\n');print('Verified archive',archive.stat().st_size,'bytes')
