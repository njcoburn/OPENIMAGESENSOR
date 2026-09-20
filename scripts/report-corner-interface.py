"""Publish the full-corner interface experiment, including incomplete runs."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json, hashlib, tarfile, html
R=Path(__file__).resolve().parents[1];B=R/'build/corner-interface-seeded'
s=json.loads((B/'summary.json').read_text());stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
checks=s.get('equivalence',[]);starts=s.get('startup',[])
practical=json.loads((B/'summary-practical-startup.json').read_text()) if (B/'summary-practical-startup.json').exists() else {}
passed=bool(checks) and all(c['passed'] for c in checks)
complete=passed and len(starts)==2 and all(c['completed'] for c in starts)
status=f'DC/AC interface comparison: {"PASS" if passed else "NOT VERIFIED"}. Full-corner ramp/load transients: {"COMPLETE" if complete else "NOT VERIFIED"}.'
text=f'''# Full-corner numerical interface check

Recorded **{stamp}**. Target: **3×3 demonstrator**.

**{status}**

## What changed

Each of the eight corner ports is connected through a testbench-only unity-gain voltage-controlled source, a zero-volt current-sensing source, and a unity-gain current-controlled source. For port p and external node e:

```spice
Ep drive 0 e 0 1
Vp drive p 0
Fp e 0 Vp 1
```

This enforces V(p)=V(e) and returns the measured current to e with the same sign. Port voltage, current, and power are preserved algebraically. It is a numerical reformulation, not an on-chip amplifier. All semiconductor, resistor and capacitor records are retained. The ground-connected ports use the same construction; their external current sources connect ground to ground.

## Checks performed

Direct and adapted circuits use the same 3.3 V supply, 2 Ω source and 100 kΩ standby loads at typical process and 27 °C. Both capacitor placements are checked. The DC and 1 kHz–1 GHz common-supply AC comparison includes both differential output rail voltages, source current and all eight port currents. This is a fixture-specific check, not a complete eight-port admittance matrix or a PDK bandwidth qualification.

The seeded comparison attempt uses `reltol=1e-7` and `abstol=1e-14`. The adapted DC solve is initialized with all voltage values from the direct operating point using `.nodeset`; these are nonbinding guesses, not fixed-voltage constraints. Earlier unseeded practical and strict attempts are archived separately and do not substitute for a passing comparison.

Mixed comparison limits: 10 nV + 10 ppm for voltage, 1 pA + 10 ppm for current, applied to saved real/imaginary components. A maximum ratio ≤1 passes.

| Placement | Analysis | Maximum error/limit | Pass |
|---|---|---:|---|
'''
for c in checks:text+=f"| {c['mode']} | {c['analysis']} | {c['max_mixed_error_ratio']:.6g} | {c['passed']} |\n"
text+='\nThe seeded AC rail-voltage component differences are at most 4.74 nV (nominal placement) and 0.387 nV (remote). The failed screens are port-current comparisons: maximum mixed error/limit ratios 4.10 and 1.13. These small discrepancies are not evidence of a physical circuit change, but they do not satisfy the stated numerical-equivalence screen.\n'
text+='\n## Startup and load pulse\n\nThe adapted startup attempt uses a 100 µs 0–3.3 V ramp, zero-charge startup, a 100 ns maximum step and a 1 mA-per-rail pulse at 151 µs with 1 ns edges; the requested end is 153 µs. It uses KLU, Gear, one thread, `gmin=1e-17`, `abstol=1e-14`, `reltol=1e-7`, and the existing GF180 clamp initialization. A simulator exit code alone is insufficient: aborted runs or traces that end early are rejected.\n\n'
for r in starts:text+=f"- **{r['mode']}**: {'completed' if r['completed'] else 'incomplete — '+r.get('error','unknown reason')}.\n"
if practical.get('startup'):
 text+='\nA separate diagnostic repeat uses the prior direct-ramp settings (`reltol=1e-6`, `abstol=1e-12`). It retains the failed AC screen and is not a qualified interface result:\n\n'
 for r in practical['startup']:text+=f"- **{r['mode']}**: {'completed' if r['completed'] else 'incomplete — '+r.get('error','unknown reason')}.\n"
if not starts:text+='Startup was not run because the prerequisite interface comparison did not pass.\n'
text+='\nBoth tolerance choices abort at about 1 ns, before the ramp or load test. The remote-placement log identifies `e.x354.ec_moscap#branch`; the nominal log reports an unrecorded cause. The prior direct model reached about 100 µs. The eight-port interface is therefore not adopted.\n'
text+='\n## Next step\n\n'+('Refine the completed transients and compare capacitor placements before integrated 3×3 qualification.' if complete else 'Reject the whole-corner eight-port interface for production use. Build a minimal reproducer around the reported `X354` MOS-capacitor branch and its extracted connections; compare direct and localized interface formulations, including a smooth supply ramp. Resolve the AC current-comparison discrepancy and startup failure before integrated 3×3 qualification. Do not alter physical parasitics or PDK device equations to obtain a pass.')+'\n\nNo layout, DRC/LVS, process/temperature, optical or fabrication qualification is claimed by this experiment.\n\n## Reproduce\n\n```sh\nbash scripts/run-tools.sh python3 scripts/check-corner-interface.py --strict --seed --diagnostic-startup\nbash scripts/run-tools.sh python3 scripts/check-corner-interface.py --strict --seed --reuse-equivalence --diagnostic-startup --startup-practical\npython3 scripts/report-corner-interface.py\nbash scripts/run-tools.sh python3 scripts/build-overview.py\n```\n\nRequires the preceding charge-reduction checkpoint and its parent charge-reference inputs. The checksummed checkpoint retains decks, logs, results and scripts.\n'
(R/'docs/corner-interface.md').write_text(text)
fragment=f'<section id="corner-interface"><h2>Full-corner numerical interface</h2><p>{stamp}. {html.escape(status)}</p><p>The eight-port interface preserves voltage and returns each port current without changing physical devices or parasitics. Both capacitor placements are checked against direct wiring.</p><p>Full results, failed runs and reproduction: <a href="corner-interface.md">interface report</a>.</p></section>\n'
(R/'docs/corner-interface.html').write_text(fragment)
(R/'simulations/corner-interface.json').write_text(json.dumps({'strict':s,'practical_startup':practical},indent=2)+'\n')
for name,heading in [('NEXT_STEPS.md','Corner-interface handoff'),('CHANGELOG.md','Corner-interface evaluation'),('COMPLETION_PLAN.md','Latest interface result')]:
 p=R/name;original=p.read_text();pos=original.index('\n')+1
 original=original[:pos]+f'\n## {heading} — {stamp}\n\n{status} [Evidence](docs/corner-interface.md). '+('Next: refine and qualify the full-corner transient.' if complete else 'Next: resolve full-corner startup before integrated 3×3 qualification.')+'\n'+original[pos:];p.write_text(original)
p=R/'README.md';a=p.read_text();pos=a.index('\n')+1;p.write_text(a[:pos]+f'\n**Latest simulation check ({stamp}):** {status} [Details](docs/corner-interface.md).\n'+a[pos:])
C=R/'checkpoints/corner-interface';C.mkdir(exist_ok=True)
source=R/'build/charge-reduced/corner-full/nominal.spice'
records=source.read_text().splitlines()
branch=next(line for line in records if line.startswith('X354 '))
nodes=set(branch.split()[1:3])
connected=[line for line in records if line and line[0] in 'RCX' and nodes.intersection(line.split()[1:])]
(B/'moscap-branch-context.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),branch=branch,nodes=sorted(nodes),connected_records=connected,scope='Connectivity context for the next diagnostic, not an independently simulatable subcircuit'),indent=2)+'\n')
files=[p for root in ['corner-interface','corner-interface-strict','corner-interface-seeded'] for p in (R/'build'/root).rglob('*')]+[R/f for f in ['scripts/check-corner-interface.py','scripts/report-corner-interface.py','docs/corner-interface.md','docs/corner-interface.html','simulations/corner-interface.json','checkpoints/pad-closure/ngspice-init/.spiceinit']]
files=sorted(p for p in files if p.is_file());hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(C/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(C/'evidence.tar.gz') as tar:
 for member in tar:
  assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==hashes[member.name]
(C/'manifest.json').write_text(json.dumps(dict(recorded=stamp,files=hashes,archive_sha256=hashlib.sha256((C/'evidence.tar.gz').read_bytes()).hexdigest()),indent=2)+'\n')
print(status,'Archive verified.')
