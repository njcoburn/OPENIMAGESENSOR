"""Publish ring candidate audit, keeping DC checks separate from capacitance acceptance."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile,base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'build/ring-candidate'
cap=json.loads((B/'capacitance-audit.json').read_text());dc={v:json.loads((B/v/'dc-audit.json').read_text()) for v in ['baseline','combined']}
rows=[]
for v in dc:
 for case in ['fill10','corner']:
  for mode in ['full','metal']:
   a=dc[v]['cases'][case][mode];c=cap[v][case][mode]
   rows.append({'variant':v,'case':case,'mode':mode,**a,'capacitance_gate':c['capacitance_gate'],'negative_diagonal_count':c['negative_diagonal_count']})
fig,axs=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
for ax,case in zip(axs,['fill10','corner']):
 for shift,v,col in [(-.18,'baseline','#677b8c'),(.18,'combined','#008b8b')]:
  ax.bar([i+shift for i in range(4)],[dc[v]['cases'][case]['full']['rails'][r]['R_ohm'] for r in ['VDD','VSS','DVDD','DVSS']],.36,label=v,color=col)
 ax.set(title=case+' — full geometry',xticks=range(4),xticklabels=['VDD','VSS','DVDD','DVSS'],ylabel='Point-to-point resistance (Ω)');ax.grid(axis='y',alpha=.2);ax.legend()
fig.suptitle('Ring diagnostic coupons: resistance includes external probe leads\nDC checks do not qualify the signed capacitance model')
asset=R/'docs/assets/ring-candidate.png';fig.savefig(asset,dpi=150);plt.close(fig)
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
summary={'recorded':stamp,'dc':dc,'capacitance':cap,'production_gds_sha256':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['build/power-ring/power_ring.gds','build/power-ring/ring_sensor_power.gds']}}
(R/'simulations/ring-candidate.json').write_text(json.dumps(summary,indent=2)+'\n')
table='| Build | Coupon | Geometry | Negative capacitors | Negative-energy nodes | Ground rails connected |\n|---|---|---|---:|---:|---|\n'
for row in rows:table+=f"| {row['variant']} | {row['case']} | {row['mode']} | {row['negative_capacitors']} | {row['negative_diagonal_count']} | {row['substrate_ground_connection']} |\n"
w=cap['combined']['corner']['full']['energy_witnesses']
assert w,'Update report conclusions if candidate no longer has negative-energy witnesses'
example=w[0]
text=f'''# Ring-section audit with the combined extraction candidate

Recorded **{stamp}**.

**The combined resistance corrections do not make the corner RC model ready for transient simulation.** Fresh filler and corner extraction completes with baseline and combined executables, using both full-device and conductor-only geometry. Four full-device LVS checks pass, and all 32 resistor-only rail solves pass connectivity and current-balance checks. The corner still fails the extracted-capacitance energy test.

![Matched ring resistance comparison](assets/ring-candidate.png)

{table}
## What the capacitance failure means

For each node we sum every incident capacitor to obtain its diagonal entry in the capacitance matrix. Set that node to 1 V and every other node to 0 V. The stored energy is one-half the diagonal capacitance. A negative diagonal therefore supplies a direct negative-energy witness: no eigenvalue fitting or deletion of small capacitors is needed.

Candidate full corner example: `{example['node']}`, diagonal **{example['C_diagonal_fF']:.6g} fF**, energy **{example['energy_J_at_1V']:.6g} J** at 1 V. These are internal extracted nodes with finite resistive connections, not nodes constrained together by ideal shorts. This rejects the raw parasitic capacitance network as a passive model; it does not by itself prove instability of a complete transistor circuit, whose device capacitances also contribute.

The negative values are already present in the raw `.res.ext` rnode capacitance fields, before SPICE export. This narrows the investigation to resistance extraction/capacitance redistribution rather than only the SPICE reader. Matching raw records are archived.

Negative entries and exact witness nodes are preserved in `simulations/ring-candidate.json`. Signed zero entries are not counted as negative. No capacitor was clamped, removed or redistributed. We did not attempt a corner transient or use this extraction to qualify the camera.

## Substrate connections and LVS scope

The full corner's `.ext` aliases VSS and DVSS; its resistor mesh joins the ground rails. The conductor-only corner retains separate rails. This localizes the distinction to semiconductor extraction rather than a metal-only short, but does not establish the physical accuracy of the substrate resistance model.

Corner device LVS uses tied analog supplies, matching the existing ring use: both VDD names map to AVDD and both ground names map to AVSS for that comparison. Filler LVS keeps four macro ports. DC audits separately reject supply-to-ground paths and supply-rail shorts before that LVS mapping. Passing LVS does not validate capacitance or independent corner-domain operation.

The same 0.4 µm external M5 leads and terminal fixtures are used for each matched comparison. Resistances include those leads and cannot simply be added into a full-ring model. Raw extraction diagnostics, including grid snapping and any `Missing rptr` messages, are retained in the audit. No new DRC is claimed for these diagnostic coupons.

## Decision and next work

Keep the candidate isolated. Its resistance fixes pass the earlier controls and block regressions, but neither fix addresses the corner's capacitance redistribution.

1. Trace each negative corner shunt back through `.res.ext` and Magic's capacitance redistribution code; check charge conservation against the pre-resistance `.ext` network.
2. Build a minimal reproducible capacitor-redistribution control, including the semiconductor reference node.
3. Require a passive, charge-conserving extracted model and justified substrate treatment before reduced-RC corner transients, stitched sections, or full-ring extraction.

Production ring GDS and installed tools remain unchanged. The source-code patches remain diagnostic, not a production tool adoption.

## Reproduce

Prerequisites are the previous ring-section coupon generation and combined executable checkpoint.

```sh
bash scripts/run-tools.sh python3 scripts/extract-ring-candidate.py
for variant in baseline combined; do
  bash scripts/run-tools.sh python3 scripts/audit-ring-sections.py --cases fill10 corner --work-dir build/ring-candidate/$variant --output build/ring-candidate/$variant/dc-audit.json
done
bash scripts/run-tools.sh python3 scripts/audit-ring-capacitance.py
bash scripts/run-tools.sh python3 scripts/report-ring-candidate.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The checksummed archive `checkpoints/ring-candidate/evidence.tar.gz` retains coupon GDS, command inputs, raw extraction, RC netlists, diagnostics, DC/LVS audits, capacitance witnesses, scripts and results. Executables and PDK remain dependencies from the pinned environment and previous checkpoint; binary and GDS hashes are recorded for each extraction.
'''
(R/'docs/ring-candidate.md').write_text(text)
html=f'''<section id="ring-candidate"><h2>Ring candidate: DC checks pass; corner capacitance fails</h2><p>{stamp}. Fresh matched filler/corner extraction passes four device LVS comparisons and 32 resistor-only rail solves. The combined candidate still produces negative-energy capacitance nodes in the corner, so it is not accepted for corner transient simulation.</p><img src="data:image/png;base64,{base64.b64encode(asset.read_bytes()).decode()}" alt="Baseline versus combined-candidate ring section resistances"><p>The full corner joins VSS/DVSS through semiconductor extraction; its metal-only control keeps them separate. Tied-domain LVS does not qualify independent supplies or the substrate model. No negative capacitors were removed or repaired.</p><p><b>Next:</b> trace capacitance redistribution and build a minimal passive-model regression before ring transients. <a href="ring-candidate.md">Detailed evidence and reproduction</a>.</p></section>'''
(R/'docs/ring-candidate.html').write_text(html)
entries=[('README.md','## Combined extraction regression',f'## Ring-section capacitance gate\n\nFour device LVS checks and 32 DC rail solves pass with matched ring coupons. The combined extraction candidate still produces negative-energy capacitance nodes in the corner; transient acceptance remains blocked. [Audit and next work](docs/ring-candidate.md).\n\n![Ring-section comparison](docs/assets/ring-candidate.png)\n\n'),('NEXT_STEPS.md','## Combined candidate handoff',f'## Ring-section handoff — {stamp}\n\nCompleted matched filler/corner extraction, 4 LVS checks and 32 DC solves. Corner capacitance still has explicit negative-energy witnesses; do not run camera qualification with this model. Next: trace signed capacitance redistribution from `.ext` through `.res.ext`, check total charge conservation, and make a minimal regression before any repair or transient use. [Evidence](docs/ring-candidate.md).\n\n'),('CHANGELOG.md','## ',f'## {stamp} — Ring-section candidate audit\n\nFresh baseline/combined full and metal coupons; 4 LVS and 32 DC checks pass. Negative-energy witnesses reject the corner parasitic capacitance network. Added plot, preserved diagnostics, dated next steps and checksummed evidence. [Report](docs/ring-candidate.md).\n\n')]
for name,marker,entry in entries:
 p=R/name;s=p.read_text()
 if 'ring-candidate.md' not in s:p.write_text(s.replace(marker,entry+marker,1))
checkpoint=R/'checkpoints/ring-candidate';checkpoint.mkdir(exist_ok=True)
files=[p for p in B.rglob('*') if p.is_file()]
files += [R/p for p in ['scripts/extract-ring-candidate.py','scripts/audit-ring-sections.py','scripts/audit-ring-capacitance.py','scripts/report-ring-candidate.py','simulations/ring-candidate.json','docs/ring-candidate.md','docs/assets/ring-candidate.png']]
files += [R/'build/ring-sections'/c/f'{m}.gds' for c in ['fill10','corner'] for m in ['full','metal']]
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};archive=checkpoint/'evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(archive) as tar:
 for name,digest in manifest.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
(checkpoint/'manifest.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':manifest},indent=2)+'\n')
print('Report and verified archive:',archive.stat().st_size,'bytes')
