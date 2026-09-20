"""Publish the combined candidate regression and its reproducible evidence."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,tarfile,base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; B=R/'build/combined-patch'
data=json.loads((B/'regression.json').read_text());data['controls']=json.loads((B/'controls.json').read_text())
assert all(x['pass'] for x in data['lvs']) and all(x['pass_run'] for x in data['runs'])
assert len(data['comparisons'])==40 and all(x['pass_screen'] for x in data['comparisons'])
maximum=max(x['max_sample_delta_V'] for x in data['comparisons'])
fig,axs=plt.subplots(1,2,figsize=(12,4),layout='constrained')
for ax,block in zip(axs,['buffer','readout']):
 for c in ['typical','ff','ss','fs','sf']:
  rows=[x for x in data['comparisons'] if x['block']==block and x['corner']==c]
  ax.plot([x['temp'] for x in rows],[x['max_sample_delta_V']*1e6 for x in rows],marker='o',label=c)
 ax.set(title=block+' — sampled output change',xlabel='Temperature (°C)',ylabel='|Combined − baseline| (µV)');ax.grid(alpha=.3);ax.legend(fontsize=8)
fig.suptitle('Fresh extraction, 3.3 V, reduced fill; short block fixtures')
asset=R/'docs/assets/combined-patch.png';fig.savefig(asset,dpi=150);plt.close(fig)
stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
data['recorded']=stamp;data['max_sample_delta_V']=maximum
data['production_gds_sha256']={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['build/power-ring/power_ring.gds','build/power-ring/ring_sensor_power.gds']}
data['candidate_binary_sha256']=hashlib.sha256((B/'magic-combined').read_bytes()).hexdigest()
(R/'simulations/combined-patch.json').write_text(json.dumps(data,indent=2)+'\n')
text=f'''# Combined extraction-patch regression

Recorded **{stamp}**.

Both Magic 8.3.664 corrections are now tested together in an isolated executable. Fresh buffer and column-readout extraction passes **4/4 LVS comparisons** and **80/80 short transients**, covering typical/ff/ss/fs/sf at −40, 27, 85 and 125 °C, at 3.3 V. All 40 baseline/candidate sample comparisons pass the 100 µV regression screen; largest difference: **{maximum*1e6:.4g} µV**.

![Process/temperature comparison](assets/combined-patch.png)

| Block | MOS devices | Extracted resistors | Raw capacitors | Eliminated floating fill nodes |
|---|---:|---:|---:|---:|
| Buffer | 3 | 19 | 150,473 | 21,085 |
| Column readout | 7 | 75 | 167,677 | 22,908 |

## What was checked

- Fresh GDS extraction with matched baseline and combined reader/triangle patch builds, including the PDK startup grid.
- LVS after resistor-net collapse against each schematic; actual RC networks retained for simulation.
- Buffer: 40 µA reference, 0.7→0.9 V input, 100 pF load, samples at 1.9 and 6 µs. Screen requires finite completed traces, in-rail samples and positive response.
- Readout: 0.5 µA reference, ideal 0.5/0.8/1.1 V columns, sequential 3.3 V selection, 30 pF load. Samples at 5/10/15 µs must be within 10 mV of the selected input.
- Both via controls match their independently solved unreduced graphs within 2 ppm: approximately 0.105148 Ω (20 vias) and 0.0938371 Ω (300 vias). Raw and exported values agree, demonstrating both fixes in the same executable.

## Scope and remaining gates

Fresh extraction is not byte-identical: internal readout terminals are renumbered and some printed capacitances differ slightly. Exact comparison flags are retained in the JSON; LVS is the connectivity gate. Capacitive-only floating fill is eliminated by the existing charge-neutral Schur reduction. The readout's existing BIAS-to-ground capacitance redistribution remains an approximation.

These are short block regressions with ideal references and column drivers, not an integrated camera/ADC qualification. No direct full-fill transient, supply-voltage sweep, mismatch, noise, new DRC or optical characterization is claimed. The 100 µV screen measures regression change, not ADC accuracy. Installed Magic and production GDS remain unchanged. The candidate is not adopted as a production tool.

**Next:** use the candidate on a representative ring section, audit substrate connections and signed capacitances, then compare DC resistance and reduced-RC transients before attempting a full-ring model.

## Reproduce

Use the pinned Docker environment described in the repository setup guide. The matching configured source checkout and baseline build are prepared by `scripts/build-export-diagnostic.sh`; coupon inputs come from the preceding extraction-diagnostics checkpoint.

```sh
bash scripts/run-tools.sh bash scripts/build-combined-diagnostic.sh
bash scripts/run-tools.sh python3 scripts/extract-combined-diagnostic.py
for block in buffer readout; do
  for mode in baseline combined; do
    bash scripts/run-tools.sh python3 scripts/reduce-$block.py --work-dir build/combined-patch/$block/$mode
  done
done
bash scripts/run-tools.sh python3 scripts/check-combined-controls.py
bash scripts/run-tools.sh python3 scripts/check-combined-diagnostic.py
bash scripts/run-tools.sh python3 scripts/report-combined-diagnostic.py
bash scripts/run-tools.sh python3 scripts/build-overview.py
```

Evidence: `checkpoints/combined-patch/evidence.tar.gz`, with SHA-256 manifest. Source commit, patches, exact inputs, binary hashes, netlists, LVS, reduction reports, simulator decks/logs/waves and results are retained. Executables and source checkout are regenerable and omitted.
'''
(R/'docs/combined-patch.md').write_text(text)
html=f'''<section id="combined-patch"><h2>Combined extraction corrections: fresh block regressions</h2><p>Recorded {stamp}. Four LVS comparisons and 80 short transients pass across five process corners and four temperatures at 3.3 V. Largest sampled output change: <b>{maximum*1e6:.4g} µV</b>; regression screen: 100 µV.</p><img src="data:image/png;base64,{base64.b64encode(asset.read_bytes()).decode()}" alt="Sampled output differences by process and temperature"><p>Both via controls also pass with the combined executable. Floating fill is reduced; the readout BIAS capacitance approximation remains. These short block checks do not qualify the integrated camera, ADC or full-ring parasitics. Installed tools and production GDS are unchanged.</p><p><b>Next:</b> candidate extraction of a representative ring section, with substrate and signed-capacitance audits before simulation. <a href="combined-patch.md">Detailed report and reproduction</a>.</p></section>'''
(R/'docs/combined-patch.html').write_text(html)
# Idempotent latest entries.
for filename,marker,entry in [
 ('README.md','## Two-layer cause confirmed; device-aware patch tests',f'## Combined extraction regression\n\nFour LVS comparisons and 80 block transients pass across five process corners and −40 to 125 °C. Largest sampled baseline/candidate difference: {maximum*1e6:.4g} µV. Diagnostic candidate only; full-ring extraction remains open. [Report](docs/combined-patch.md).\n\n![Combined patch process/temperature comparison](docs/assets/combined-patch.png)\n\n'),
 ('CHANGELOG.md','## 2026-09-18 — Triangle',f'## {stamp} — Combined extraction candidate\n\nFresh buffer/readout extraction, four LVS passes, 80 corner transients and two via controls pass. Added isolated build, reusable reducer paths, plots and archived evidence. [Report](docs/combined-patch.md).\n\n'),
 ('NEXT_STEPS.md','## Latest continuation update',f'## Combined candidate handoff — {stamp}\n\nCompleted fresh buffer/readout extraction with both patches; 4/4 LVS and 80/80 short corner transients pass. Next: extract a representative ring section with this candidate, audit substrate connections and negative capacitances, then validate DC and reduced RC behavior. Do not yet replace installed Magic or production netlists. [Evidence](docs/combined-patch.md).\n\n')]:
 p=R/filename;s=p.read_text()
 if 'Combined extraction regression' not in s and filename=='README.md':s=s.replace(marker,entry+marker,1)
 elif filename!='README.md' and 'Combined candidate handoff' not in s and '— Combined extraction candidate' not in s:s=s.replace(marker,entry+marker,1)
 p.write_text(s)
checkpoint=R/'checkpoints/combined-patch';checkpoint.mkdir(exist_ok=True)
files=[p for p in B.rglob('*') if p.is_file() and p.suffix not in ['.npy'] and p.name!='magic-combined']
files += [R/p for p in ['checkpoints/output-buffer/output_buffer.gds','checkpoints/readout/column_readout.gds','circuits/output-buffer.spice','layout/column_readout.spice','scripts/build-combined-diagnostic.sh','scripts/extract-combined-diagnostic.py','scripts/check-combined-diagnostic.py','scripts/check-combined-controls.py','scripts/report-combined-diagnostic.py','scripts/reduce-buffer.py','scripts/reduce-readout.py','patches/magic-8.3.664-resistor-reader.patch','patches/magic-8.3.664-triangle-offset.patch','simulations/combined-patch.json','docs/combined-patch.md','docs/assets/combined-patch.png']]
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
archive=checkpoint/'evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
with tarfile.open(archive) as tar:
 for name,digest in manifest.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
(checkpoint/'manifest.json').write_text(json.dumps({'source_commit':'381714e2d5debf2ded71c5a6b6604e6b936422cf','archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':manifest},indent=2)+'\n')
print(stamp,'max delta V',maximum,'archive bytes',archive.stat().st_size)
