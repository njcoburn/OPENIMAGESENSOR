"""Publish power-ring evidence, distinguishing completed checks from unfinished PEX."""
from pathlib import Path
import hashlib,json,re,tarfile,xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/power-ring'
def violations(p):return len(ET.parse(p).findall('.//items/item'))
ring_drc=violations(out/'ring-early.lyrdb');assembly_drc=violations(out/'assembly-final-main.lyrdb')
assert ring_drc==assembly_drc==0
assert 'RING_DRC_COUNT=0' in (out/'magic.log').read_text()
lvs=(out/'flat-lvs/lvs.log').read_text();assert 'Final result: Circuits match uniquely.' in lvs
connect=json.loads((out/'assembly-connectivity.json').read_text());assert connect['all_pass']
lead_text=(out/'leads/power_leads_rc.spice').read_text();res={}
for line in lead_text.splitlines():
 if line.startswith('R'):
  t=line.split();res['VDD' if 'VDD' in t[1] else 'VSS']=float(t[3])
assert set(res)=={'VDD','VSS'} and all(x>0 for x in res.values())
loadfile=ROOT/'simulations/power-ring-load-practical.json'
load=json.loads(loadfile.read_text()) if loadfile.exists() else None
finefile=ROOT/'simulations/power-ring-load-practical-fine.json'
comparison=None
if finefile.exists():
 coarse=np.loadtxt(out/'electrical-practical/hot/wave.txt',skiprows=1)
 fine=np.loadtxt(out/'electrical-practical-fine/hot/wave.txt',skiprows=1)
 # Compare settled load response on the common 100 ns output grid.
 times=np.arange(.0012,.0015+1e-12,1e-7)
 errors={name:float(np.max(np.abs(np.interp(times,coarse[:,0],coarse[:,col])-np.interp(times,fine[:,0],fine[:,col]))))*1e6 for name,col in [('core_vdd_uV',2),('core_ground_uV',3)]}
 comparison={'scope':'Hot settled response, 100 ns versus 50 ns requested time step, common 100 ns grid','max_difference':errors,'limit_uV':10,'pass':all(v<10 for v in errors.values())}
 assert comparison['pass'],comparison
status={}
for name in ['pex','pex-unsimplified','pex-metal','pex-hier']:
 p=out/name
 if (p/'status.json').exists():status[name]=json.loads((p/'status.json').read_text())
 else:status[name]={'status':'exported_unvalidated' if (p/'ring_rc.spice').exists() else 'unfinished_no_model'}
fig,axs=plt.subplots(1,3,figsize=(16,4.5),constrained_layout=True)
x=np.arange(2);axs[0].bar(x-.18,[10.8526,16.3276],.36,label='Initial 1.2 µm routes');axs[0].bar(x+.18,[res['VDD'],res['VSS']],.36,label='Final 4 µm trunks + bridges');axs[0].set(xticks=x,xticklabels=['VDD','Ground'],ylabel='Extracted resistance (Ω)',title='Actual connecting routes');axs[0].legend(fontsize=8)
rows=[]
if load:
 for name,r in load['cases'].items():
  a=np.loadtxt(out/'electrical-practical'/name/'wave.txt',skiprows=1);active=a[:,0]>=.0012
  axs[1].plot(a[:,0]*1e3,a[:,2]-a[:,3],label=name)
  axs[2].plot(a[active,0]*1e3,a[active,3]*1e3,label=name)
  rows.append(f"<tr><td>{name}</td><td>{r['max_active_core_supply_drop_mV']:.3f}</td><td>{r['max_active_ground_rise_mV']:.3f}</td><td>{'PASS' if r['rail_screen_pass'] else 'FAIL'}</td></tr>")
 for ax in axs[1:]:ax.legend()
else:
 for ax in axs[1:]:ax.text(.5,.5,'Load test unfinished',ha='center',transform=ax.transAxes)
axs[1].set(title='Ring models + extracted connecting wires',xlabel='Time (ms)',ylabel='Core supply relative to core ground (V)')
axs[2].set(title='Ground movement during load pulses',xlabel='Time (ms)',ylabel='Core ground relative to bond ground (mV)')
for ax in axs:ax.grid(alpha=.2)
fig.savefig(ROOT/'docs/assets/power-ring-performance.png',dpi=150);plt.close(fig)
summary={'ring_magic_DRC':0,'ring_configured_KLayout_DRC':ring_drc,'assembly_configured_KLayout_DRC':assembly_drc,
 'ring_flat_LVS':'Circuits match uniquely','physical_connectivity_probes':len(connect['checks']),
 'lead_R_ohm':res,'hot_time_step_check':comparison,'ring_extraction_attempts':status,'load_test':load,
 'ring_GDS_sha256':hashlib.sha256((out/'power_ring.gds').read_bytes()).hexdigest(),
 'assembly_GDS_sha256':hashlib.sha256((out/'ring_sensor_power.gds').read_bytes()).hexdigest(),
 'scope':'Power-only development assembly. Signal pads/routing, full die precheck, ESD, and validated full-ring distributed RC remain separate.'}
(ROOT/'simulations/power-ring-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
section=f'''<section id="power-ring"><h2>Physical supply ring and sensor power routing</h2>
<p><strong>Built:</strong> a 1.110 × 1.010 mm development ring with two supply bond pads, four foundry corners, and 125 filler cells. The unchanged 3×3 sensor is placed inside and its power and ground are routed. The bottom two pads are VDD and ground; the central block is the sensor. Signal pads and their routing are still absent.</p>
<figure><img src="assets/power-ring-sensor.png" alt="Actual GDS of the foundry power ring surrounding the 3 by 3 sensor, with supply and ground routes" style="width:100%;max-width:1000px"><figcaption>Actual power-only assembly. This is a development test vehicle, not a complete camera die or bonding-ready design.</figcaption></figure>
<table><tr><th>Check</th><th>Result</th></tr><tr><td>Ring Magic DRC</td><td>0 violations</td></tr><tr><td>Ring and final assembly, configured KLayout DRC</td><td>0 violations each</td></tr><tr><td>Flat ring device LVS</td><td>Unique match, including corners and fillers</td></tr><tr><td>Independent physical metal/via continuity</td><td>{len(connect['checks']):,} probes passed; no supply-to-ground short</td></tr><tr><td>Added VDD route resistance</td><td>{res['VDD']:.5f} Ω</td></tr><tr><td>Added ground route resistance</td><td>{res['VSS']:.5f} Ω</td></tr></table>
<p>The final routes use 4 µm trunks and bridges matching the existing sensor buses. Their total extracted resistance is {sum(res.values()):.5f} Ω, versus 27.1802 Ω for the initial narrow routes. A new via was moved outside the existing dummy-fill boundary to clear width/spacing violations. The sensor GDS and foundry macro devices are unchanged.</p>
<p><strong>More than two clamps:</strong> the corners add eight clamp circuits, giving ten total. Each filler includes 32 MOS-capacitor units, and all 125 instances are included in the schematic. This changes startup loading compared with the earlier two-pad experiment.</p>
<img src="assets/power-ring-performance.png" alt="Extracted wire resistance comparison and ring load-test response" style="width:100%;height:auto">
<h3>Supply-load test: explicit model scope</h3>
<p>This test uses the installed ring schematic models plus RC extracted from the actual isolated connecting wires. It includes a 0.5 Ω / 2 nH board feed, 100 nF decoupling with ESR/ESL, a 33 kΩ core load and 100 µA load pulses. It does not yet include ring-metal resistance, complete assembly coupling, or a new camera-image scan.</p>
<table><tr><th>Condition</th><th>Maximum core-supply drop after startup (mV)</th><th>Maximum ground rise (mV)</th><th>1% rail screen</th></tr>{''.join(rows) if rows else '<tr><td colspan="4">Unfinished; no electrical pass claimed.</td></tr>'}</table>
<p>The ring-only practical run uses 1 pA absolute current tolerance, relative tolerance 1e-4 and charge tolerance 1e-14 C. Its source ramps over 1 ms; evaluation begins after a 200 µs hold. This does not relax the earlier pixel simulation settings. Extracted wire resistors remain at their nominal values in the temperature tests; metal temperature coefficients are not yet included.</p>
<p>Hot time-step cross-check: {('maximum supply difference %.4f µV and ground difference %.4f µV on a common 100 ns grid; both below 10 µV.' % (comparison['max_difference']['core_vdd_uV'],comparison['max_difference']['core_ground_uV'])) if comparison else 'unfinished.'} Strict direct and exact-interface diagnostic runs both timed out at 900 seconds; no strict-tolerance pass is claimed.</p>
<h3>Full-ring extraction status</h3><ul>'''+''.join(f'<li>{name}: {r["status"]}</li>' for name,r in status.items())+'''</ul>
<p>An unfinished or merely exported model is not a verified full-ring RC result. Earlier camera sampling passes remain separate evidence. The independent load test above must not be described as full-ring extracted camera verification.</p>
<p>The configured DRC selection is <code>all,-antenna,-density,-cup</code>. Density, antenna, CUP, seal ring, slot dimensions, chip ID, optical openings, bonding and ESD qualification remain outside this checkpoint. The metal-continuity check does not replace device LVS of a future complete pad-and-sensor design.</p>
<p><a href="power-ring.md">Model details, sources and reproduction instructions</a>. Next: validate the full ring interconnect model, then use it in the camera simulation and replace reserved filler positions with the required signal pads.</p></section>'''
(ROOT/'docs/power-ring.html').write_text(section+'\n')
checkpoint=ROOT/'checkpoints/power-ring';checkpoint.mkdir(exist_ok=True)
files=[ROOT/'docs/power-ring.md',ROOT/'docs/power-ring.html',ROOT/'docs/assets/power-ring-layout.png',ROOT/'docs/assets/power-ring-sensor.png',ROOT/'docs/assets/power-ring-performance.png',ROOT/'simulations/power-ring-verification.json']
files += [ROOT/'scripts/run-tools.sh', ROOT/'scripts/build-overview.py']
files+=list((ROOT/'scripts').glob('*power-ring*'))+list((ROOT/'scripts').glob('*power-assembly*'))+list((ROOT/'scripts').glob('*power-leads*'))+list((ROOT/'layout').glob('*power-ring*'))+list((ROOT/'layout').glob('*power-leads*'))
for name in ['power_ring.gds','ring_sensor_power.gds','power_leads.gds','power_ring.spice','placement.json','connectivity.json','assembly-connectivity.json','ring-early.lyrdb','assembly-final-main.lyrdb','magic.log','device-extraction.log','klayout.log','assembly-final-klayout.log']:
 files.append(out/name)
for folder in ['flat-lvs','leads','electrical-practical','electrical-practical-fine','electrical','electrical-adapter','leads-1p2um']:
 files.extend(p for p in (out/folder).rglob('*') if p.is_file())
if load:files.append(loadfile)
if finefile.exists():files.append(finefile)
# Only closed extraction evidence goes into this snapshot; no moving files.
for name,r in status.items():
 if r['status']=='stopped_unfinished':files.extend(p for p in (out/name).glob('*') if p.is_file())
manifest={'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files)) if p.is_file()},'parent_checkpoint':'checkpoints/clamp-convergence/evidence.tar.gz'}
archive=checkpoint/'evidence.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=3) as tar:
 for name in manifest['files']:tar.add(ROOT/name,arcname=name)
with tarfile.open(archive) as tar:
 for name,digest in manifest['files'].items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
manifest['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest();(checkpoint/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Physical verification passed; checkpoint contains',len(manifest['files']),'verified files. Full-ring RC status is reported separately.')
