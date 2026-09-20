"""Publish charge-conserving reference evidence and its placement limitation."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile,base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/charge-reference'
summary=json.loads((B/'summary.json').read_text());audit=json.loads((B/'serialized-audit.json').read_text());ac=json.loads((B/'ac-checks.json').read_text());old=json.loads((R/'build/capacitance-candidate/accounting.json').read_text())
assert len(summary)==len(audit)==8 and sum(len(v) for v in ac.values())==16
assert all(v['pass'] for d in ac.values() for v in d.values())
maxerr=max(v['max_error_fC'] for d in ac.values() for v in d.values());matrixerr=max(v['max_serialized_pair_error_fF'] for v in audit.values())
fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
a=old['tee']['area-fixed'];ref=sum(ac['tee']['common']['ngspice_charge_fC'])
axs[0].bar(['Original C','Native RC','Reference RC'],[a['original_shunt_sum_fF'],a['ngspice_common_mode_fF'],ref],color=['#426785','#b86632','#16887d']);axs[0].set(ylabel='Common-mode capacitance (fF)',title='Two-layer T control: charge accounting restored')
d=ac['tee']['differential'];x=[0,1];axs[1].bar([v-.18 for v in x],d['expected_charge_fC'],.36,label='Original C matrix',color='#426785');axs[1].bar([v+.18 for v in x],d['ngspice_charge_fC'],.36,label='Reference ngspice',color='#16887d');axs[1].set(xticks=x,xticklabels=['Signal electrode','Lower plate'],ylabel='Charge amplitude (fC)',title='Differential drive: +1 V / −1 V');axs[1].legend()
for ax in axs:ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
asset=R/'docs/assets/charge-reference.png';fig.savefig(asset,dpi=150);plt.close(fig)
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
result={'recorded':stamp,'release_scope':'3x3 demonstrator first, confirmed by user','models':summary,'serialized_audit':audit,'ngspice_checks':ac,'placement_scope':'lumped original capacitance at explicit R anchors; distributed-R retained; spatial placement not qualified','native_export_status':'not corrected or adopted','production_gds_sha256':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['build/power-ring/power_ring.gds','build/power-ring/ring_sensor_power.gds']}}
(R/'simulations/charge-reference.json').write_text(json.dumps(result,indent=2)+'\n')
rows='\n'.join(f"| {name} | {v['resistors']:,} | {v['devices']} | {v['capacitors']} |" for name,v in summary.items())
text=f'''# Charge-conserving RC reference

Recorded **{stamp}**. First release: **3×3 monochrome demonstrator**, confirmed by the user. The proposed 64×64 camera is a later expansion.

**Eight reference models preserve the original capacitance matrix, and all 16 independent ngspice charge checks pass.** This fixes charge accounting in a separately generated reference netlist. It does not correct or qualify Magic's native distributed-capacitance export.

![Charge reference versus original extraction and native export](assets/charge-reference.png)

## Construction and scope

The builder reads original node-to-substrate and mutual capacitors from `.ext`, retains their values and connections once, and copies every extracted resistor and device record unchanged from the area-corrected RC export. It replaces the native exported capacitor records as a complete set; it does not delete isolated negative entries or fit capacitor values to simulation.

Each original net maps to one connected resistor component. If its original named node remains, that node is the anchor. Otherwise the nearest recorded resistor-node coordinate to the original extraction-node coordinate is selected deterministically. Nets without an extracted resistor network retain their original node. Every anchor and selection reason is archived.

**Placement approximation:** capacitance remains lumped per original extracted net and attached to these anchors. The original node coordinate is an extractor naming location, not a demonstrated physical capacitance centroid. Exact charge accounting with zero metal resistance does not establish accurate finite-resistance settling or high-frequency behavior. We have not adopted this as a signoff model.

| Model | Resistors | Devices | Capacitor pairs |
|---|---:|---:|---:|
{rows}

## Validation

- Four small controls and four ring coupons have only nonnegative capacitors.
- Every original capacitance pair is recovered after collapsing the metal resistors. The independent audit re-reads the saved SPICE files and original `.ext`; maximum serialized pair error is {matrixerr:.4g} fF. Pair equality determines the complete capacitance matrix, including charge and energy for arbitrary original-net voltages.
- Resistor and device records compare exactly with the earlier area-corrected exports. Their prior DC and LVS topology evidence remains applicable; no new physical layout or LVS run is claimed here.
- Sixteen ngspice AC checks cover common-mode, differential and both electrode-basis excitations across four controls. Maximum charge error versus the original capacitance matrix is {maxerr:.4g} fC, at numerical precision.
- The T control now measures **{ref:.5f} fF** in common mode, matching the original **{a['original_shunt_sum_fF']:.5f} fF**. The native RC export measured **{a['ngspice_common_mode_fF']:.5f} fF**.

For the independent AC fixtures, signal endpoints A/B are driven together so metal resistance has no voltage drop; the separate lower plate is driven according to each excitation. The implicit substrate is explicitly exposed and grounded in the fixture only. Charge is inferred from AC source current at 1 MHz. These are numerical electrical checks, not physical capacitance measurements or camera transients.

## Why a separate reference

Source inspection shows two native behaviors that need care: coupling can be redistributed as substrate capacitance while still being retained as coupling, and `killnode` handling suppresses coupling attached to eliminated nodes. A local subtraction of the observed excess would not repair all cases. Reconstructing the complete original capacitor network provides an auditable reference without changing installed tools or inventing missing spatial information.

## Next steps toward the 3×3 release

1. Test capacitor-anchor placement sensitivity rather than treating the chosen coordinate as physically exact.
2. Eliminate resistor-only internal nodes with a validated reduction that preserves retained-port behavior. The corner reference still contains over half a million resistors.
3. Run corner and integrated 3×3 transients, then repeat process/supply/temperature and realistic ADC-load checks with the accepted model.
4. Complete the physical, manufacturing-interface and bench milestones in [COMPLETION_PLAN.md](../COMPLETION_PLAN.md).

Substrate ground-domain interpretation and previously recorded extraction diagnostics remain open. No tapeout, optical performance, new DRC, or complete camera qualification is claimed. Production GDS and installed tools are unchanged.

## Reproduce

Prerequisite: the area-corrected extraction and controls from the capacitance-candidate checkpoint.

```sh
python3 scripts/build-charge-reference.py
python3 scripts/audit-charge-reference.py
bash scripts/run-tools.sh python3 scripts/check-charge-reference.py
bash scripts/run-tools.sh python3 scripts/report-charge-reference.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

`checkpoints/charge-reference/evidence.tar.gz` preserves the generated models, mappings, audits, simulator decks/logs/results, input `.ext`/`.res.ext`/RC files, scripts and completion plan, with a verified SHA-256 manifest.
'''
(R/'docs/charge-reference.md').write_text(text)
html=f'''<section id="charge-reference"><h2>Charge-conserving reference for the 3×3 demonstrator</h2><p>{stamp}. The first release target is now confirmed as 3×3. Eight reference models preserve the original capacitance matrix, resistor and device records; 16 independent ngspice charge checks pass.</p><img src="data:image/png;base64,{base64.b64encode(asset.read_bytes()).decode()}" alt="Common-mode and differential charge now match the original extraction"><p>The reference fixes charge accounting by retaining the original lumped capacitor network at explicit resistor anchors. Spatial capacitance placement and finite-resistance settling remain unqualified; native Magic export is not adopted.</p><p><b>Next:</b> placement sensitivity, resistor-network reduction and integrated 3×3/ADC-load simulations. <a href="charge-reference.md">Detailed evidence</a> · <a href="../COMPLETION_PLAN.md">Completion plan</a>.</p></section>'''
(R/'docs/charge-reference.html').write_text(html)
for name,marker,entry in [
 ('README.md','## Capacitance correction and path to completion',f'## 3×3 release: charge-conserving RC reference\n\nThe first finished chip will be the **3×3 demonstrator**. Eight reference models preserve the original capacitance matrix; 16 independent charge checks pass. Capacitance placement and integrated transient qualification remain open. [Evidence](docs/charge-reference.md) · [Completion plan](COMPLETION_PLAN.md).\n\n![Charge-conserving reference results](docs/assets/charge-reference.png)\n\n'),
 ('NEXT_STEPS.md','## Capacitance handoff',f'## Charge-reference handoff — {stamp}\n\nUser confirmed **3×3 demonstrator first**. Generated 8 reference models: unchanged R/devices, original capacitance-pair matrix preserved, and 16 ngspice charge checks pass. Native export remains unaccepted. Next: quantify lumped-capacitor anchor sensitivity, validate reduction of resistor-only nodes, then run corner/integrated 3×3 and ADC-load transients. [Report](docs/charge-reference.md) · [Completion plan](COMPLETION_PLAN.md).\n\n'),
 ('CHANGELOG.md','## ',f'## {stamp} — Charge-conserving reference and confirmed 3×3 scope\n\nBuilt and independently audited 8 lumped-C/distributed-R reference models; all 16 ngspice charge checks pass. Preserved exact R/device records, recorded every capacitor anchor, and retained the spatial-placement limitation. User confirmed the 3×3 demonstrator as the first release. [Report](docs/charge-reference.md).\n\n')]:
 p=R/name;s=p.read_text()
 if 'charge-reference.md' not in s:p.write_text(s.replace(marker,entry+marker,1))
p=R/'COMPLETION_PLAN.md';s=p.read_text();s=__import__('re').sub(r'Updated \*\*.*?\*\*\.',f'Updated **{stamp}**.',s,count=1);p.write_text(s)
checkpoint=R/'checkpoints/charge-reference';checkpoint.mkdir(exist_ok=True)
files=[p for p in B.rglob('*') if p.is_file()]
for v in summary.values():
 src=R/v['source'];files += [src/n for n in ['coupon.ext','coupon.res.ext','rc.spice']]
files += [R/p for p in ['scripts/build-charge-reference.py','scripts/audit-charge-reference.py','scripts/check-charge-reference.py','scripts/report-charge-reference.py','docs/charge-reference.md','docs/assets/charge-reference.png','simulations/charge-reference.json','COMPLETION_PLAN.md']]
files=list(dict.fromkeys(files));manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};archive=checkpoint/'evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(archive) as tar:
 for name,digest in manifest.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
(checkpoint/'manifest.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':manifest},indent=2)+'\n');print('Verified archive',archive.stat().st_size,'bytes')
