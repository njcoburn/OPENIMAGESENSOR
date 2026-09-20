"""Publish the provisional 3×3 custom-carrier pad placement for review."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,csv,base64,hashlib,tarfile
R=Path(__file__).resolve().parents[1];B=R/'build/pad-proposal';m=json.loads((B/'placement.json').read_text());stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
text=f'''# Provisional 3×3 pad placement and bond-map review

Recorded **{stamp}**. **Placement proposal only: no signal/power routing or manufacturing sign-off.** The packaging route has not been selected. This assumes a bare-die/custom-carrier route for planning; it is not claimed compatible with wafer.space's default-ring chip-on-board service.

![Proposed pad map, top view](assets/proposed-pad-map.png)

## Geometry and assignment

- Nominal ring: **1.210 × 1.210 mm**, with a nominal 500 × 500 µm inner opening. This is not a selected die/slot size; seal ring, scribe margin, die ID and submission outline remain absent.
- Unchanged existing core: **334.2 × 241.2 µm**, centered with translation ({m['core_translation_um'][0]:g}, {m['core_translation_um'][1]:g}) µm.
- **24 pad locations**: all 19 existing core nets plus two extra VDD and three extra GND pads. One ground on each side; three supply pads total.
- Installed GF180 macros: 17 `asig_5p0`, three `dvdd`, four `dvss`, four corners, and twenty `fill10` instances. Each side uses six 75 µm pad pitches and 50 µm total filler.
- Added supply macros imply **15 supply/corner clamps** by macro inventory, versus ten in the previous power-ring vehicle. Fillers also change. This assembly needs fresh electrical qualification after review; previous ring results do not transfer unchanged.

Pad IDs run counterclockwise from the first southern pad, viewed from the top of the die. They are proposal IDs, not connector pins or an approved package numbering convention. Coordinates below refer to actual macro bond-region text labels, **not certified bond landing centers**. Final openings, edge distances, metallurgy and bond-loop geometry need the provider's review.

[Coordinate CSV](proposed-pad-map.csv) · [Logical interface and board timing](demonstrator-interface.md).

| Pad | Core net | Edge | X reference (µm) | Y reference (µm) | Bond intent |
|---|---|---|---:|---:|---|
'''
for p in m['pads']:text+=f"| {p['pad_id']} | {p['core_net']} | {p['side']} | {p['pad_label_x_um']:.3f} | {p['pad_label_y_um']:.3f} | {p['bond_status']} |\n"
text+='''
## Routing and protection review before implementation

1. Confirm the manufacturing slot and carrier route. The nominal ring can be moved into a larger approved die; its 1.21 mm size must not be treated as a submission entitlement or final die outline.
2. Review the three supply/four return bonds and whether their extra clamp/loading cost is justified. The supply-domain straps have not been added.
3. Review the analog-pad/protection choice for every functional pin, especially 3.3 V controls, 2 V VRESET and low-current BIAS. `asig_5p0` is an existing candidate macro; its name is not proof of thin-oxide protection compatibility.
4. Decide on COL0–COL2 and OUT access. Their four purple pads are optional placeholders. Even an unbonded but connected pad adds leakage/capacitance. Default to leaving those routes absent until a load budget is approved; replacing unused pads with fillers would change the ring again.
5. Reserve secondary protection and supply connections near the functional pads. The prior local protection cell has not been placed or copied blindly onto all pins.
6. Route controls away from the optical junctions and sensitive BIAS/OUT paths; keep bond wires and packaging out of the optical path. No passivation opening or optical keepout mask is introduced by this proposal.
7. After these choices: generate the matching full-chip schematic, route, then run connectivity, device LVS, applicable DRC/density/antenna and extracted electrical checks.

## Checks completed here

All 19 schematic port names are assigned, pad IDs and reference points are unique, each point lies in its placed macro bounding box, nominal side lengths match, the core fits the nominal opening, and its translation lies on the layout grid. These are placement checks, not DRC/LVS. Macro process layers have small bounding-box overhangs; simple bbox overlaps are not treated as design-rule violations.

The original core and power-ring GDS files are not modified. The separate proposal GDS and source hashes are in the checkpoint. No simulator experiments were resumed.

## Information needed to finalize this

- Selected wafer.space run/slot, or confirmation that none has been selected.
- Intended wire-bonding/package provider, or confirmation that none has been selected.
- Their required pad ring, die geometry, bond map and optical-access constraints.

The [manufacturing review questions](manufacturing-review.md) are ready to send to a provider once the destination and authorization are supplied. No external contact has been made. We cannot certify an optical path from a pad-placement drawing.

## Reproduce

```sh
bash scripts/run-tools.sh python3 layout/demonstrator-pad-proposal.py
python3 scripts/report-pad-proposal.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```
'''
(R/'docs/pad-proposal.md').write_text(text)
fragment=f'<section id="pad-proposal"><h2>Proposed 24-pad interface for the 3×3 demonstrator</h2><p>{stamp}. Separate placement-only GDS: 19 unique core nets plus extra supply/return pads, using installed GF180 macros. Nominal ring 1.21 × 1.21 mm; this is not a selected die outline or a routed/verified chip.</p><img alt="Proposed top-view pad assignment" src="data:image/png;base64,{base64.b64encode((R/"docs/assets/proposed-pad-map.png").read_bytes()).decode()}"><p>Packaging and optical access remain unconfirmed. Purple diagnostic pads require a loading decision; extra supply macros change clamp count and require requalification. No simulation debugging has resumed.</p><p><a href="pad-proposal.md">Pad table, placement checks and review gates</a> · <a href="proposed-pad-map.csv">Coordinate CSV</a> · <a href="manufacturing-review.md">Questions for the provider</a>.</p></section>\n'
(R/'docs/pad-proposal.html').write_text(fragment)
p=R/'docs/demonstrator-ports.csv';rows=list(csv.DictReader(p.open()))
for row in rows:row['physical_pad']=' / '.join(x['pad_id'] for x in m['pads'] if x['core_net']==row['core_net']);row['status']='proposed only; unapproved and unrouted'
with p.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
p=R/'docs/demonstrator-interface.md';s=p.read_text().replace('physical pad and connector numbers are intentionally unassigned.','pad IDs now reference the unapproved [placement proposal](pad-proposal.md); connector numbers remain unassigned.');s=s.replace('Final physical pad numbers, corner orientations, pad macros and connector pins remain unassigned.', 'Provisional physical IDs and macro orientations are now in the [placement proposal](pad-proposal.md); final approval, macro/protection choices and connector pins remain open.');p.write_text(s)
for filename in ['NEXT_STEPS.md','CHANGELOG.md']:
 p=R/filename;s=p.read_text();pos=s.index('\n')+1;p.write_text(s[:pos]+f'\n## Pad-placement proposal — {stamp}\n\nCreated a 24-pad custom-carrier proposal, coordinate CSV, labeled diagram and separate unrouted GDS. All 19 core ports are represented. Packaging, diagnostic loading and protection choices remain open; no routing or sign-off claimed. [Review](docs/pad-proposal.md). Next: obtain the selected run/package requirements and close the pad-map review before routing.\n'+s[pos:])
p=R/'COMPLETION_PLAN.md';s=p.read_text().replace('| Written run/package requirements | Open; [questions and draft](docs/manufacturing-review.md) |','| Written run/package requirements | Provisional [24-pad map](docs/pad-proposal.md) prepared; provider/run and optical requirements remain open |');p.write_text(s)
p=R/'README.md';s=p.read_text();at=s.index('### Later expansion:');s=s[:at]+'''### Provisional pad-placement review

![Proposed 24-pad map for the 3×3 demonstrator](docs/assets/proposed-pad-map.png)

Separate **unrouted, unapproved** custom-carrier concept: 19 core nets, 24 pads. Die outline and optical packaging remain open. [Pad table and review gates](docs/pad-proposal.md) · [Coordinate CSV](docs/proposed-pad-map.csv).

'''+s[at:];p.write_text(s)
C=R/'checkpoints/pad-proposal';C.mkdir(exist_ok=True)
files=[B/'demonstrator_pad_proposal.gds',B/'placement.json']+[R/n for n in ['layout/demonstrator-pad-proposal.py','scripts/report-pad-proposal.py','docs/pad-proposal.md','docs/pad-proposal.html','docs/assets/proposed-pad-map.png','docs/proposed-pad-map.csv','simulations/pad-proposal.json']]
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(C/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(C/'evidence.tar.gz') as tar:
 for member in tar:assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==hashes[member.name]
(C/'manifest.json').write_text(json.dumps(dict(recorded=stamp,files=hashes,archive_sha256=hashlib.sha256((C/'evidence.tar.gz').read_bytes()).hexdigest()),indent=2)+'\n')
print('Pad proposal documented; checkpoint archive verified.')
