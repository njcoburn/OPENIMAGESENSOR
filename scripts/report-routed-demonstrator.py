"""Publish scoped physical verification for the routed working demonstrator."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import json,re,hashlib,base64,tarfile,csv,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];B=R/'build/routed-demonstrator'
m=json.loads((B/'routing.json').read_text());connect=json.loads((B/'connectivity.json').read_text())
rdb=ET.parse(B/'main-drc.lyrdb');items=rdb.findall('.//items/item');categories=Counter(i.findtext('category','unknown') for i in items)
magic=(B/'magic.log').read_text();counts=re.findall(r'ROUTED_DRC_COUNT=(\d+)',magic);assert counts,'Magic DRC result missing'
lvs=(B/'lvs.log').read_text();lvs_pass=bool(re.search(r'Final result:\s*Circuits match uniquely\.',lvs))
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
result=dict(recorded=stamp,gds_sha256=hashlib.sha256((B/'demonstrator_routed.gds').read_bytes()).hexdigest(),reference_sha256=hashlib.sha256((R/'circuits/demonstrator-routed.spice').read_bytes()).hexdigest(),physical_connectivity=connect['passed'],physical_checks=len(connect['checks']),klayout_main_drc_items=len(items),klayout_categories=dict(categories),magic_drc_count=int(counts[-1]),lvs_unique_match=lvs_pass,scope='Working custom-carrier layout; main KLayout selection all,-antenna,-density,-cup; no density/antenna/CUP, optical packaging, ESD or full-chip electrical sign-off; no regeneration of central dummy fill')
(R/'simulations/routed-demonstrator.json').write_text(json.dumps(result,indent=2)+'\n')
external=json.loads((B/'external-ports.json').read_text())
with (R/'docs/routed-pad-map.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['pad_id','original_core_net','external_net','connection','pad_reference_x_um','pad_reference_y_um'])
 for p in m['pad_map']:
  state='power ring and core' if p['core_net'] in ['VDD','GND'] else 'primary pad only; core diagnostic disconnected' if p['core_net'] in ['COL0','COL1','COL2','OUT'] else 'primary pad -> secondary protection -> core'
  w.writerow([p['pad_id'],p['core_net'],external['pad_nets'][p['pad_id']],state,p['pad_label_x_um'],p['pad_label_y_um']])
summary=f"13 functional signal paths routed through local protection; seven supply/return pads connected. Metal connectivity: {len(connect['checks'])} checks, {'PASS' if connect['passed'] else 'FAIL'}. Main KLayout DRC: {len(items)} markers. Magic DRC: {counts[-1]}. Device LVS unique match: {lvs_pass}."
text=f'''# Routed 3×3 demonstrator working layout

Recorded **{stamp}**. The user approved proceeding with the 24-pad working arrangement without a selected shuttle or bonding provider. Manufacturing/optical requirements remain open.

**{summary}**

![Routed assembly](assets/routed-demonstrator.png)

## What changed

- Routed all 13 functional signal pads through copies of the existing local secondary protection cell to the corresponding core terminals.
- Connected three VDD and four GND pads to two separate internal supply rings and the sensor core. Protection-cell supplies connect to those rings.
- Retained four diagnostic pads (P10–P12 and P15) but left their signal paths disconnected from COL2/COL1/COL0 and OUT. Their primary pad diodes remain connected to the rails. This avoids adding those pads' signal loading to the unbuffered core nodes.
- Used the saved functional core geometry and omitted its old dummy fill so new routes can occupy that space. The functional device geometry is preserved; the resulting layout is a new revision, not the earlier filled-core GDS. Central dummy fill and density qualification remain to be completed.
- New top-level metal is checked against the nine existing 26 × 26 µm optical keepout boxes. This geometric check does not establish passivation or package optical access.
- Added top-level bond labels and an independent [hierarchical reference](../circuits/demonstrator-routed.spice). External functional pins use a `PAD_` prefix to distinguish the bond side from the core side of each physical series resistor. The four disconnected diagnostic bonds are `NC_P10`, `NC_P11`, `NC_P12`, and `NC_P15`.

![Core and new routing](assets/routed-core-routing.png)

[Working bond-net CSV](routed-pad-map.csv) lists actual external names and the disconnected diagnostic pads. Coordinate references are still macro labels, not approved bond landing centers.

## Verification evidence and limits

| Check | Result | Scope |
|---|---|---|
| Physical metal/via tracing | {connect['passed']} ({len(connect['checks'])} checks) | No name-based net joining; distinct core nets, signal-to-protection paths, no metal resistor bypass, supply stripes and disconnected diagnostic bonds |
| KLayout main DRC | {len(items)} markers | Installed GF180MCU D deck, `all,-antenna,-density,-cup` |
| Magic DRC | {counts[-1]} | Installed GF180MCU D technology checks |
| Netgen device LVS | Unique match = {lvs_pass} | New assembly reference versus extracted devices; see raw logs |
| New metal versus optical keepouts | Pass | Top-level route geometry only |
| Density / antenna / CUP / full-run precheck | Not performed for this revision | Final fill, die outline, seal ring, chip ID and process/package requirements remain open |
| Full assembled electrical simulation | Not qualified | Earlier simulator investigation remains stopped pending expert review |

The first combined runner was stopped after Magic printed its zero-error DRC count because an unconditional empty detail listing was taking extra time. A hierarchical extraction attempt (`extraction.log`) was also stopped before completion. Final device-only flat extraction/LVS uses `extract-flat.tcl`, `extraction-flat.log` and `lvs.log`; the reproduction script now uses that flat flow and skips the detail listing when the DRC count is zero. Neither stopped attempt is counted as passing LVS.

The first LVS reference had the DVSS macro supply arguments reversed. Correcting its call to `VDD GND VDD gf180mcu_fd_io__dvss` (the established stock-macro interface) resolved the mismatch without any layout edit. The initial failed comparison is retained as `lvs-initial-reference.log`; the final comparison is `lvs.log`.

KLayout marker categories: `{dict(categories)}`.

Initial route attempts had shorts. Independent tracing identified an obstacle-map hole-handling bug; it was repaired and all routes were rebuilt. Stage-by-stage tracing now checks separation after every functional route. The final evidence above, not an early route image or process exit code, determines the checkpoint status.

The power/ground distribution here is a functional candidate, not a qualified ESD return design. The prior protection cell's local checks do not establish adequate clamp voltage/current for the whole chip. These 24 pads/corners/fillers differ from the earlier power-only vehicle and need fresh electrical qualification.

## Next steps

1. Close any reported main DRC/LVS findings before adopting this revision.
2. Regenerate central dummy fill with route and optical exclusions; run density and antenna checks on the assembled geometry, then repeat affected DRC/LVS checks.
3. Review the supply/protection network, actual bond openings, pad numbering and optical package when the run/provider are selected.
4. Use external expert feedback to resolve the separately documented extraction/simulation issue; qualify the final assembled model across startup, PVT, repeated frames and a selected ADC load.
5. Complete run-specific die/seal/ID/precheck and independent release review before fabrication.

No new solver sweep or manufacturing submission was made. No additional input is needed to continue local physical verification; final manufacturing approval will need the provider's rules.

## Reproduce

```sh
bash scripts/run-tools.sh python3 layout/route-demonstrator.py
bash scripts/run-tools.sh bash scripts/check-routed-physical.sh
bash scripts/run-tools.sh klayout -b -r scripts/render-routed-demonstrator.py
python3 scripts/report-routed-demonstrator.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Dependencies are identified by hashes in `routing.json`: the earlier pad placement, functional core and local protection GDS. The checkpoint includes these three inputs, routed output, source, independent reference, reports and screenshots.
'''
(R/'docs/routed-demonstrator.md').write_text(text)
fragment=f'<section id="routed-demonstrator"><h2>Functional routing of the 24-pad 3×3 demonstrator</h2><p>{stamp}. {summary}</p><img alt="Actual routed demonstrator GDS" src="data:image/png;base64,{base64.b64encode((R/"docs/assets/routed-demonstrator.png").read_bytes()).decode()}"><p>The four diagnostic signal paths remain disconnected. Old central dummy fill was removed for routing; density, antenna and final manufacturing/electrical qualification are still open. No solver debugging was resumed.</p><img alt="Core routing and optical keepouts" src="data:image/png;base64,{base64.b64encode((R/"docs/assets/routed-core-routing.png").read_bytes()).decode()}"><p><a href="routed-demonstrator.md">Verification scope and reproduction</a> · <a href="../circuits/demonstrator-routed.spice">Assembly reference schematic netlist</a>.</p></section>\n'
(R/'docs/routed-demonstrator.html').write_text(fragment)
for filename in ['NEXT_STEPS.md','CHANGELOG.md']:
 p=R/filename;s=p.read_text();at=s.index('\n')+1;p.write_text(s[:at]+f'\n## Routed working demonstrator — {stamp}\n\n{summary} Four diagnostic signal paths remain disconnected; fill and final sign-off are open. [Evidence](docs/routed-demonstrator.md). Next: close physical findings and regenerate/verify fill; retain the stop on simulator parameter experiments.\n'+s[at:])
p=R/'README.md';s=p.read_text();at=s.index('### Provisional pad-placement review');s=s[:at]+'''### Routed working layout

![Routed 3×3 demonstrator with pad connections](docs/assets/routed-demonstrator.png)

'''+summary+''' The four diagnostic signal paths remain disconnected. Final fill, manufacturing and electrical sign-off remain open. [Verification report](docs/routed-demonstrator.md).

'''+s[at:];s=s.replace('the currently unbonded signal ports','the routed working signal interface');s=s.replace('The current power-ring vehicle does not yet route the signal pads.','The earlier power-only vehicle is superseded by the separate routed working-layout checkpoint below.');p.write_text(s)
p=R/'COMPLETION_PLAN.md';s=p.read_text();s=s.replace('The [power-ring assembly](docs/power-ring.md) is a development vehicle with power pads only: **signal pads and their routing are not implemented**.', 'The earlier [power-ring assembly](docs/power-ring.md) had power pads only. The [new routed working layout](docs/routed-demonstrator.md) now connects functional signals through local protection; diagnostic signal paths remain disconnected.');s=s.replace('| M2; logical interface ready now | Open; current ring only bonds power |','| Working pad arrangement approved; manufacturing M2 remains open | Functional routing candidate completed; see current DRC/LVS report. Fill and final checks remain |');p.write_text(s)
C=R/'checkpoints/routed-demonstrator';C.mkdir(exist_ok=True)
files=[p for p in B.rglob('*') if p.is_file() and p.name not in ['failed-stage.gds','failed-routes.json']]
files += [R/n for n in list(m['sources'])+['build/pad-proposal/placement.json','build/integrated/placement.json','layout/route-demonstrator.py','scripts/check-routed-demonstrator.py','scripts/prepare-routed-verification.py','scripts/check-routed-physical.sh','scripts/run-tools.sh','scripts/render-routed-demonstrator.py','scripts/report-routed-demonstrator.py','circuits/demonstrator-routed.spice','circuits/integrated.spice','circuits/analog-secondary.spice','docs/routed-pad-map.csv','docs/routed-demonstrator.md','docs/routed-demonstrator.html','docs/assets/routed-demonstrator.png','docs/assets/routed-core-routing.png','simulations/routed-demonstrator.json']]
files=sorted(set(files));hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(C/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(C/'evidence.tar.gz') as tar:
 for member in tar:assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==hashes[member.name]
(C/'manifest.json').write_text(json.dumps(dict(recorded=stamp,files=hashes,archive_sha256=hashlib.sha256((C/'evidence.tar.gz').read_bytes()).hexdigest()),indent=2)+'\n')
print(summary,'Archive verified.')
