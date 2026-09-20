"""Publish current evidence without promoting a coupon to full-chip qualification."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,tarfile,html
R=Path(__file__).resolve().parents[1];stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
ref=json.loads((R/'simulations/clamp-scaled-refinement.json').read_text());cp=R/'simulations/corner-scaled-candidate.json';corner=json.loads(cp.read_text()) if cp.exists() else None
b=R/'build/filled-electrical-baseline';audit=b/'audit.json';baseline=json.loads(audit.read_text()) if audit.exists() else None
rows=[]
for x in ref['runs']:
 c=x['comparison'];rows.append(f"| Isolated clamp {x['case']} | {'Complete' if x['completed'] else 'Incomplete'} | {max(c['post_startup_max_by_column'][:2])*1e6:.3f} µV rail difference |" if c else f"| Isolated clamp {x['case']} | Incomplete | {x['error']} |")
if corner:
 for x in corner['runs']:rows.append(f"| Complete corner: {x['mode']} placement | {'Complete' if x['completed'] else 'Incomplete'} | {x['seconds']:.1f} s runtime; not timestep-qualified |")
else:rows.append('| Complete corner placements | Pending | No final result yet |')
base_text='Final-GDS extraction retains all 4,037 semiconductor records and the same ports as device LVS. The precise constant-capacitance reference reduces 358,494 floating nodes to 2,179 capacitor pairs on 279 retained nodes, passing recorded port-charge and quadratic-energy checks. It assumes zero initial floating charge and omits distributed wire resistance. Tiny negative extraction roundoff is bounded in the capacitance audit; this is not a manufacturing or full-chip electrical pass.'
rows.append('| Complete corner: 25 ns / strict tolerances, both placements | FAIL | Both abort at 151 µs load onset in e.x354.ehelper#branch; candidate not promoted |')

md=f'''# Electrical qualification progress — {stamp}

**The 3×3 chip is not electrically qualified yet.** This checkpoint advances the numerical diagnosis while retaining the final-chip acceptance gates.

## Completed control investigation

The old standalone original/scaled comparison missed a 0.544 ns RC transient. Collinear source breakpoints resolve it without changing the physical supply waveform. At 50 ps and 25 ps local spacing, the maximum original/scaled current difference is 1.493 pA versus the unchanged 100 pA screen. Native-point errors versus an independently integrated terminal equation are below 2.875 pA. Integrated charge bookkeeping agrees to about 4.25e-8 relative in this fixture.

[Detailed control audit](clamp-control-reference.md) · [Machine-readable results](../simulations/clamp-control-breakpoints.json)

![Resolved control comparison](assets/clamp-control-breakpoints.png)

## Extracted-network results

The isolated 144-device clamp candidate completes at 50 ns. Its 25 ns normal and stricter-tolerance checks both complete and pass the recorded post-startup rail/capacitor voltage screens. Full-trace rail differences remain below 8.20 µV. Source-current differences are retained in the JSON; the voltage screens do not constitute a complete multiport current/charge-equivalence test.

| Test | Result | Evidence / scope |
|---|---|---|
{chr(10).join(rows)}

[Isolated refinement data](../simulations/clamp-scaled-refinement.json). These runs retain the extracted resistors, capacitors and semiconductor terminals. Only the named nonlinear MOS-capacitor's internal helper normalization changes; installed PDK files and chip GDS remain unchanged. The model candidate is limited to the tested equation/options and conditions.

## Final filled-chip extraction

{base_text}

The saved LVS extraction is device-only. The fresh baseline explicitly adds lumped capacitance but omits distributed wire resistance. It must not be called the accepted post-fill RC model. [Exact target and remaining stages](../simulations/full-chip-qualification.json).

## What remains before complete-chip qualification

1. Resolve the reproducible clamp-helper failure at the 151 µs, 1 ns-rise load transition. Both strict corner runs fail; do not bypass this gate or run blind solver sweeps. Separate timestep and tolerance effects in a reviewer-agreed minimal reproducer before promoting the candidate.
2. Validate the complete pad-ring/device model and final-GDS capacitance/resistance extraction, including the known capacitance-export limitations and substrate interpretation.
3. Qualify complete-chip startup and three nine-pixel frames with refinement, then PVT and realistic external loading.
4. Validate ADS1115 slow acquisition separately from the earlier fast sample/hold fixture; photodiodes continue integrating during conversion.
5. Independently review the accepted model and archive the matching layout, netlists, stimuli and evidence.

[Full electrical plan](full-chip-electrical-plan.md). No ESD survival, fabricated-camera, QE or manufacturing-readiness claim follows from this numerical checkpoint.

## Evidence archive

[Final filled-chip capacitance evidence](../checkpoints/filled-electrical-baseline/evidence.tar.gz). [Refinement and corner evidence](../checkpoints/scaled-electrical-progress/evidence.tar.gz), with deck/model/waveform hashes in the result JSON files. Model dependencies remain the pinned PDK and the earlier reproducer. Nothing was posted or sent externally.
'''
(R/'docs/scaled-electrical-progress.md').write_text(md)
section=f'<section id="scaled-electrical-progress"><h2>Electrical qualification progress</h2><p>{stamp}. The locally resolved capacitor controls pass. The isolated extracted clamp now completes and passes its 25 ns/tolerance voltage refinement screens. Both stricter complete-corner runs abort at the load transition, so the candidate is not promoted. Full-chip qualification is still open.</p><img src="assets/clamp-control-breakpoints.png" alt="Resolved capacitor model control traces" style="max-width:100%"><p>{html.escape(base_text)}</p><p><a href="scaled-electrical-progress.md">Network results and remaining electrical gates</a> · <a href="full-chip-electrical-plan.md">Full-chip plan</a></p></section>'
(R/'docs/scaled-electrical-progress-section.html').write_text(section)
(R/'docs/scaled-electrical-progress.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Electrical qualification progress</title><style>body{font:17px/1.5 system-ui;max-width:1100px;margin:40px auto;padding:20px}</style><body>'+section+'</body></html>')
out=R/'checkpoints/scaled-electrical-progress';out.mkdir(exist_ok=True)
with tarfile.open(out/'evidence.tar.gz','w:gz') as tf:
 for folder in ['clamp-scaled-refinement','corner-scaled-candidate','corner-scaled-refinement']:
  for p in sorted((R/'build'/folder).rglob('*')):
   if p.is_file():tf.add(p,arcname=folder+'/'+str(p.relative_to(R/'build'/folder)))
 for p in [R/'scripts/refine-corner-scaled-candidate.py',R/'scripts/refine-clamp-scaled-candidate.py',R/'scripts/check-corner-scaled-candidate.py',R/'scripts/extract-filled-electrical-baseline.py',R/'scripts/audit-filled-electrical-baseline.py',R/'scripts/report-scaled-electrical-progress.py']:
  tf.add(p,arcname='scripts/'+p.name)
(out/'evidence.sha256').write_text(hashlib.sha256((out/'evidence.tar.gz').read_bytes()).hexdigest()+'  evidence.tar.gz\n')
print('Updated electrical progress report and evidence',stamp)
