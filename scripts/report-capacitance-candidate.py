"""Report the area-sign correction and the independent charge-accounting blocker."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile,base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/capacitance-candidate'
cap=json.loads((B/'capacitance-audit.json').read_text())['area-fixed'];old=json.loads((R/'build/ring-candidate/capacitance-audit.json').read_text())['combined']
dc=json.loads((B/'dc-audit.json').read_text());prior=json.loads((R/'build/ring-candidate/combined/dc-audit.json').read_text());con=json.loads((B/'conservation.json').read_text());account=json.loads((B/'accounting.json').read_text())
assert all(cap[c][m]['capacitance_gate']=='nonnegative_capacitor_network' for c in cap for m in cap[c])
assert all(dc['cases'][c]['full']['device_LVS']=='unique_match' for c in dc['cases'])
delta=max(abs(dc['cases'][c][m]['rails'][r]['R_ohm']-prior['cases'][c][m]['rails'][r]['R_ohm']) for c in dc['cases'] for m in dc['cases'][c] for r in dc['cases'][c][m]['rails'])
maxerr=max(abs(row['relative_error']) for cases in con.values() for modes in cases.values() for rows in modes.values() for row in rows)
fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
labels=['Filler full','Filler metal','Corner full','Corner metal'];pairs=[('fill10','full'),('fill10','metal'),('corner','full'),('corner','metal')]
axs[0].bar(range(4),[len(old[c][m]['negative_capacitors']) for c,m in pairs],label='Previous candidate',color='#b46538')
axs[0].scatter(range(4),[0]*4,label='Area correction',color='#008b8b',zorder=4)
axs[0].set(xticks=range(4),xticklabels=labels,ylabel='Negative capacitor entries',title='Area-sign correction removes negative entries');axs[0].tick_params(axis='x',labelrotation=15);axs[0].legend()
a=account['tee']['area-fixed'];axs[1].bar(['Original extraction','Corrected RC export'],[a['original_shunt_sum_fF'],a['ngspice_common_mode_fF']],color=['#008b8b','#b46538'])
axs[1].set(ylabel='Common-mode capacitance to substrate (fF)',title='Separate charge-accounting test still fails')
for ax in axs:ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
asset=R/'docs/assets/capacitance-candidate.png';fig.savefig(asset,dpi=150);plt.close(fig)
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
summary={'recorded':stamp,'capacitance':cap,'dc':dc,'max_DC_change_ohm':delta,'partition_conservation':con,'max_partition_relative_error':maxerr,'common_mode_accounting':account,'status':'area_sign_corrected_in_isolated_candidate; exported_charge_accounting_still_fails','binary_sha256':hashlib.sha256((B/'magic-area-fixed').read_bytes()).hexdigest(),'production_gds_sha256':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['build/power-ring/power_ring.gds','build/power-ring/ring_sensor_power.gds']}}
(R/'simulations/capacitance-candidate.json').write_text(json.dumps(summary,indent=2)+'\n')
text=f'''# Capacitance area correction and charge-accounting audit

Recorded **{stamp}**.

**A one-line area-sign correction removes every negative capacitor in the four ring coupons. A separate exported-charge accounting error still blocks RC model acceptance.** The candidate remains isolated; no installed tool or production netlist is replaced.

![Area correction and remaining accounting discrepancy](assets/capacitance-candidate.png)

## Confirmed area-sign defect

In Magic 8.3.664, `resis/ResMakeRes.c`, the one-breakpoint branch of `ResCalcEastWest` adds `height * (LEFT(tile) - RIGHT(tile))` to the node's area. That is negative for a finite-width tile. The correction reverses the subtraction; the north–south counterpart already uses positive height. `ResDistributeCapacitance` in `ResSimple.c` normalizes those areas to allocate capacitance, carrying negative weights into `.res.ext` and SPICE.

Patch: `patches/magic-8.3.664-single-break-area.patch`, applied on top of the previously tested resistor-reader and triangle corrections, against source commit `381714e2d5debf2ded71c5a6b6604e6b936422cf`.

| Geometry | Previous negative entries | Corrected |
|---|---:|---:|
| Full filler | 0 | 0 |
| Metal-only filler | 4 | 0 |
| Full corner | 5 | 0 |
| Metal-only corner | 132 | 0 |

Both full-device LVS checks pass. All 16 DC rail solves pass; maximum change versus the prior candidate is {delta:.6g} Ω. Four corrected capacitor networks contain only nonnegative elements, so the explicit parasitic capacitor networks satisfy the passive-energy sign condition. This does **not** establish accurate capacitance magnitudes, substrate behavior, or complete transistor-model qualification. Existing grid-snapping and `Missing rptr` extraction diagnostics remain recorded.

## Two different conservation checks

**Internal redistribution:** the raw rnode capacitances sum to the original node's incident coupling-capacitance total, not its `.ext` node-shunt field. Comparing the proper quantities gives a maximum relative discrepancy of {maxerr*1e6:.3f} ppm across both candidates and all coupons. This reports numerical normalization accuracy; it is not full-network charge conservation. The source uses single-precision area accumulation and printed raw values.

**Exported electrical network:** the two-layer T control exposes a separate failure. Its original extraction has {a['original_shunt_sum_fF']:.5f} fF total shunt capacitance to substrate and {a['incident_coupling_sum_fF']:.5f} fF between the two metal electrodes. Driving both electrodes together should put zero voltage across that coupling capacitor. The corrected RC export instead measures **{a['ngspice_common_mode_fF']:.5f} fF** to substrate—an excess of **{a['excess_fF']:.5f} fF**, equal to the coupling capacitance within printed precision.

The exported netlist retains the original coupling capacitor and adds its redistributed value as substrate shunts. The nonnegative area correction does not fix this accounting. Eight ngspice AC checks (four control geometries × two candidates) independently reproduce the exported netlist's calculated common-mode capacitance. They confirm the discrepancy; they are not model-acceptance passes.

The control fixture explicitly exposes and grounds the implicit substrate, drives A/B/REF together, and measures current at 1 MHz with a 1 V AC source. Metal resistors have zero voltage in that excitation. The original expected value comes directly from `.ext` node shunts. No measured optical or semiconductor capacitance is implied.

The small T controls demonstrate the accounting error and changed area allocation, but do not reproduce negative entries themselves. The metal-only filler is the smallest tested negative-capacitance reproducer. Earlier control attempts with an outside terminal, a duplicate extraction call, and no coupling are retained as failed/non-exercising attempts, not passing regressions.

## Decision and next step

Keep the area correction as a diagnostic patch. Do not use this candidate to requalify camera settling yet. Next, correct the distinction between distributed shunt capacitance and retained mutual coupling, then require:

1. Original and R-collapsed RC capacitance matrices agree within an explicit numerical budget, including common-mode and differential excitations.
2. No negative-energy modes; preserved charge, device topology and DC resistance.
3. Repeated buffer/readout process-temperature and ADC-load tests using the accepted model.
4. Substrate-ground treatment resolved before corner stitching and full-ring simulation.

See [Completion plan](../COMPLETION_PLAN.md) for the remaining design, verification and fabrication milestones.

## Reproduce

Use the pinned tools container and matching configured Magic source from the earlier diagnostic checkpoints.

```sh
bash scripts/run-tools.sh bash scripts/build-capacitance-candidate.sh
bash scripts/run-tools.sh python3 scripts/extract-ring-candidate.py --area-fixed
bash scripts/run-tools.sh python3 scripts/audit-ring-sections.py --cases fill10 corner --work-dir build/ring-candidate/area-fixed --output build/capacitance-candidate/dc-audit.json
python3 scripts/audit-ring-capacitance.py --variants area-fixed --output build/capacitance-candidate/capacitance-audit.json
python3 scripts/audit-capacitance-conservation.py
bash scripts/run-tools.sh python3 scripts/check-capacitance-controls.py
bash scripts/run-tools.sh python3 scripts/check-capacitance-accounting.py
bash scripts/run-tools.sh python3 scripts/report-capacitance-candidate.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

`checkpoints/capacitance-candidate/evidence.tar.gz` retains fresh raw extraction, RC models, audits, small controls, ngspice measurements, source patch and scripts with SHA-256 verification. The prior combined ring models remain in the previous ring-candidate checkpoint. Production ring GDS hashes are unchanged.
'''
(R/'docs/capacitance-candidate.md').write_text(text)
html=f'''<section id="capacitance-candidate"><h2>Negative capacitance corrected; charge accounting remains</h2><p>{stamp}. A one-line tile-area sign correction removes all negative entries from four ring coupons. Two device LVS checks and 16 DC rail checks pass.</p><img src="data:image/png;base64,{base64.b64encode(asset.read_bytes()).decode()}" alt="Negative capacitor counts removed and common-mode capacitance discrepancy"><p>The corrected export still fails an independent common-mode charge check: {a['ngspice_common_mode_fF']:.5f} fF versus {a['original_shunt_sum_fF']:.5f} fF expected. Retained coupling is also added as substrate capacitance. The diagnostic tool is not adopted.</p><p><b>Next:</b> fix shunt/mutual-coupling accounting, then repeat electrical qualification. <a href="capacitance-candidate.md">Detailed report</a> · <a href="../COMPLETION_PLAN.md">Project completion plan</a>.</p></section>'''
(R/'docs/capacitance-candidate.html').write_text(html)
for name,marker,entry in [
 ('README.md','## Ring-section capacitance gate',f'## Capacitance correction and path to completion\n\nThe area-sign patch removes negative capacitances in all four ring coupons; LVS and DC checks pass. A separate charge-accounting error remains, confirmed with small ngspice controls. [Evidence](docs/capacitance-candidate.md) · [Completion plan](COMPLETION_PLAN.md).\n\n![Capacitance correction and remaining charge error](docs/assets/capacitance-candidate.png)\n\n'),
 ('NEXT_STEPS.md','## Ring-section handoff',f'## Capacitance handoff — {stamp}\n\nIsolated area-sign patch removes all negative C entries from four coupons; 2 LVS and 16 DC checks pass. Internal partition sums match incident coupling within {maxerr*1e6:.2f} ppm. Exported charge still fails: coupling is retained and also added as substrate shunts. Next: fix that accounting and compare original versus R-collapsed capacitance matrices before any camera requalification. [Report](docs/capacitance-candidate.md) · [Completion plan](COMPLETION_PLAN.md).\n\n'),
 ('CHANGELOG.md','## ',f'## {stamp} — Area-sign fix and charge-accounting regression\n\nAdded an isolated one-line Magic area correction: 4 coupons now have no negative C, with 2 LVS and 16 DC checks passing. Eight independent small-control AC checks confirm a separate exported common-mode capacitance excess. Recorded both outcomes, archived evidence, and added a completion plan. [Report](docs/capacitance-candidate.md).\n\n')]:
 p=R/name;s=p.read_text()
 if 'capacitance-candidate.md' not in s:p.write_text(s.replace(marker,entry+marker,1))
checkpoint=R/'checkpoints/capacitance-candidate';checkpoint.mkdir(exist_ok=True)
files=[p for p in B.rglob('*') if p.is_file() and p.name!='magic-area-fixed']+[p for p in (R/'build/ring-candidate/area-fixed').rglob('*') if p.is_file()]
files += [R/p for p in ['scripts/build-capacitance-candidate.sh','scripts/extract-ring-candidate.py','scripts/audit-ring-sections.py','scripts/audit-ring-capacitance.py','scripts/audit-capacitance-conservation.py','scripts/check-capacitance-controls.py','scripts/check-capacitance-accounting.py','scripts/report-capacitance-candidate.py','patches/magic-8.3.664-single-break-area.patch','simulations/capacitance-candidate.json','docs/capacitance-candidate.md','docs/assets/capacitance-candidate.png','COMPLETION_PLAN.md']]
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};archive=checkpoint/'evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(archive) as tar:
 for name,digest in manifest.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
(checkpoint/'manifest.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':manifest},indent=2)+'\n');print('Verified archive',archive.stat().st_size,'bytes')
