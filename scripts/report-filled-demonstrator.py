"""Publish the measured scope of the filled working-layout checkpoint."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import base64,hashlib,json,re,tarfile,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];B=R/'build/filled-demonstrator'
f=json.loads((B/'fill.json').read_text());c=json.loads((B/'connectivity.json').read_text())
def markers(name):
 items=ET.parse(B/name).findall('.//items/item')
 return dict(count=len(items),categories=dict(Counter(i.findtext('category','unknown') for i in items)))
a=markers('density-antenna.lyrdb');d=markers('main-drc.lyrdb');lvs=bool(re.search(r'Final result:\s*Circuits match uniquely\.',(B/'lvs.log').read_text()))
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
r=dict(recorded=stamp,fill=f,connectivity_pass=c['passed'],connectivity_checks=len(c['checks']),density_antenna=a,main_drc=d,lvs_unique_match=lvs,scope='Installed GF180MCU D density/antenna/main decks on working layout extent; CUP and run-specific manufacturing precheck excluded; no new RC simulation or Magic DRC on filled revision.')
(R/'simulations/filled-demonstrator.json').write_text(json.dumps(r,indent=2)+'\n')
summary=f"Central dummy fill regenerated. Density/antenna: {a['count']} violations; main KLayout DRC: {d['count']} violations; device LVS: {'unique match' if lvs else 'FAIL'}; physical connectivity: {len(c['checks'])} checks, {'PASS' if c['passed'] else 'FAIL'}."
names={30:'Poly2',34:'M1',36:'M2',42:'M3',46:'M4',81:'M5 (top)'}
rows='\n'.join(f"| {names[int(z)]} | {v['coverage_before_percent']:.2f}% | {v['coverage_after_percent']:.2f}% | {14 if z=='30' else 30}% |" for z,v in f['layers'].items())
md=f'''# Filled 3×3 demonstrator: density and antenna checkpoint

Recorded **{stamp}**.

**{summary}**

![Filled assembly](assets/filled-demonstrator.png)

## Changes and checks

The approved 24-pad routed layout is preserved as a separate input. This revision adds floating poly and M1–M5 dummy fill inside the central 498 × 498 µm region. No new vias or connections are added. The generator verifies that no existing geometry on the filled layers was removed, and that the added fill stays clear of functional shapes and all nine 26 × 26 µm optical keepouts. Poly fill also avoids active diffusion. The independent physical metal checker repeats the 4,566 supply, pad, core and isolation checks without joining nets by label.

Thirteen protected functional signals and seven supply/ground pads remain connected. P10–P12 and P15 remain disconnected from the internal diagnostic nodes. New fill can change capacitance even though it does not change device connectivity; no post-fill electrical performance is claimed.

![Filled core with nine clear optical regions](assets/filled-core-routing.png)

## Density before and after

These percentages use the current GDS bounding extent, approximately 1.210 mm square including the macro overhang. This is a working layout envelope, **not a selected shuttle die outline**.

| Layer | Before fill | After fill | Installed deck minimum |
|---|---:|---:|---:|
{rows}

The routed input already exceeded these whole-layout minima; the new fill restores central coverage around its routes. This does not establish that this amount of fill is electrically optimal.

The installed `density.rb` checks whole-layout minimum coverage (14% poly, 30% metal). It does not establish compliance with any additional local-window or maximum-density requirements a chosen run may impose. The antenna deck evaluates the installed process connectivity and ratio rules; its zero-marker result is distinct from electrical/ESD qualification.

## Verification

| Check | Result | Scope |
|---|---|---|
| Density + antenna | {a['count']} markers | `decks=density,antenna`; installed GF180MCU D rules |
| Main KLayout DRC | {d['count']} markers | `all,-antenna,-density,-cup`; rerun on the filled GDS |
| Device LVS | {'Unique match' if lvs else 'FAILED'} | Flat device extraction versus the same independent assembly reference |
| Physical connectivity | {'PASS' if c['passed'] else 'FAIL'} | {len(c['checks'])} checks on the filled GDS |
| Optical keepout exclusion | Pass | Added fill only; does not certify passivation or package optical access |
| Magic DRC | Not rerun on this revision | Earlier routed layout passed; filled revision uses the new KLayout result above |
| Full-chip post-fill RC/electrical tests | Not qualified | Prior simulator stop rule remains active |
| CUP / run-specific manufacturing checks | Open | No selected run, slot, bonding provider or approved final die/seal ring |

The main DRC completed and wrote its zero-item XML report. A subsequent shell-wrapper error, caused by editing the running script, overwrote that command’s console log; `runner-error.log` preserves the error. The XML report remains the main DRC evidence. Extraction/LVS was then run separately. The saved runner is corrected; no shell exit code is being used as a substitute for a DRC/LVS result.

Density/antenna categories: `{a['categories']}`. Main DRC categories: `{d['categories']}`.

GDS SHA-256: `{f['gds_sha256']}`.

## Next steps and input needed

1. Review the existing clamp-model reproducer with an appropriate ngspice/GF180 expert; resolve the documented model issue before resuming full-chip electrical qualification. The package is prepared but has not been sent. Further simulator parameter sweeps remain stopped.
2. Once the extracted model is accepted, include the final fill's coupling/parasitics and repeat startup, repeated frames, PVT and the selected off-chip ADC load.
3. Select a run and wire-bond/optical packaging route, then confirm die outline, seal ring, bond openings, optical access and all required sign-off decks. The current custom pad ring is not assumed compatible with wafer.space's default chip-on-board offering.
4. Complete carrier/controller/ADC design and independent release review before fabrication.

No additional user input was needed for this physical checkpoint. Final manufacturing closure requires the selected provider's requirements. No external contact, purchase, submission, or new simulator sweep was made.

## Reproduce and restore

```sh
bash scripts/run-tools.sh python3 layout/fill-routed-demonstrator.py
bash scripts/run-tools.sh bash scripts/check-filled-demonstrator.sh
bash scripts/run-tools.sh klayout -b -r scripts/render-filled-demonstrator.py
python3 scripts/report-filled-demonstrator.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

The [checkpoint manifest](../checkpoints/filled-demonstrator/manifest.json) records input/output hashes and a checked evidence archive. Unpack into a separate directory to inspect or restore; avoid overwriting an active workspace. The archive includes the routed input, placement/routing metadata, independent reference, scripts, reports and images. Use the pinned Docker image in `scripts/run-tools.sh` for its PDK and tools. This is a reproducible engineering checkpoint, not a fabrication release.
'''
(R/'docs/filled-demonstrator.md').write_text(md)
htrows=''.join(f"<tr><td>{names[int(z)]}</td><td>{v['coverage_before_percent']:.2f}%</td><td>{v['coverage_after_percent']:.2f}%</td></tr>" for z,v in f['layers'].items())
images=''.join(f'<img alt="{alt}" src="data:image/png;base64,{base64.b64encode((R/path).read_bytes()).decode()}">' for path,alt in [('docs/assets/filled-demonstrator.png','Filled working demonstrator'),('docs/assets/filled-core-routing.png','Core fill with nine optical keepouts')])
(R/'docs/filled-demonstrator.html').write_text(f'<section id="filled-demonstrator"><h2>Filled 3×3 layout: density and antenna</h2><p>{stamp}. {summary}</p>{images}<table><tr><th>Layer</th><th>Before</th><th>After</th></tr>{htrows}</table><p>Density uses the current layout extent, not a selected manufactured die. Nine optical keepouts remain clear of added fill. Full-chip post-fill electrical qualification, final packaging, die/seal geometry and run-specific precheck remain open.</p><p><a href="filled-demonstrator.md">Verification scope, evidence and reproduction</a>.</p></section>\n')
C=R/'checkpoints/filled-demonstrator';C.mkdir(exist_ok=True)
paths=list(p for p in B.rglob('*') if p.is_file())
paths += [R/n for n in ['build/routed-demonstrator/demonstrator_routed.gds','build/routed-demonstrator/routing.json','build/pad-proposal/placement.json','layout/fill-routed-demonstrator.py','scripts/check-filled-demonstrator.sh','scripts/check-routed-demonstrator.py','scripts/render-filled-demonstrator.py','scripts/report-filled-demonstrator.py','scripts/run-tools.sh','circuits/demonstrator-routed.spice','circuits/integrated.spice','circuits/analog-secondary.spice','docs/filled-demonstrator.md','docs/filled-demonstrator.html','docs/assets/filled-demonstrator.png','docs/assets/filled-core-routing.png','simulations/filled-demonstrator.json']]
paths=sorted(set(paths));hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with tarfile.open(C/'evidence.tar.gz','w:gz') as tar:
 for p in paths:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(C/'evidence.tar.gz') as tar:
 for member in tar:assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==hashes[member.name]
(C/'manifest.json').write_text(json.dumps(dict(recorded=stamp,files=hashes,archive_sha256=hashlib.sha256((C/'evidence.tar.gz').read_bytes()).hexdigest()),indent=2)+'\n')
print(summary+' Archive verified.')
