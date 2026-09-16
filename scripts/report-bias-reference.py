"""Report physical board bias, power-up and supply checks; archive evidence."""
from pathlib import Path
import json,hashlib,tarfile,shutil
import numpy as np
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];p=root/'simulations/bias-reference.json';d=json.loads(p.read_text());dc=json.loads((root/'simulations/bias-reference-dc.json').read_text());rows=list(d['cases'].values())
assert len(rows)==d['planned_cases']
for name,h in d['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==h,name
fig,axs=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
for corner in ['typical','ff','ss','fs','sf']:
 r=[v for v in dc['cases'].values() if v['corner']==corner and v['diode']=='diode_typical' and v['rcol_scale']==v['rbuf_scale']==1 and v['status']=='complete']
 for ax,key in zip(axs,['column_reference_uA','buffer_reference_uA']):
  volts=[3.0,3.3,3.6];line,=ax.plot(volts,[next(v[key] for v in r if v['supply_V']==s and v['temp_C']==27) for s in volts],'o-',label=corner)
  ax.fill_between(volts,[min(v[key] for v in r if v['supply_V']==s) for s in volts],[max(v[key] for v in r if v['supply_V']==s) for s in volts],color=line.get_color(),alpha=.12)
for ax,title,target in zip(axs,['Column resistor current','Buffer resistor current'],[.5,40]):
 ax.axhline(target,color='black',ls='--',label='Previous ideal target');ax.set(xlabel='Supply voltage (V)',ylabel='Current (µA)',title=title+'\nLines: 27 °C; bands: −40 to 125 °C');ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.savefig(root/'docs/assets/bias-reference-dc.png',dpi=160)
fig,axs=plt.subplots(3,1,figsize=(11,8),layout='constrained',sharex=True)
for name,r in d['cases'].items():
 if (r['corner'],r['temp_C'],r['supply_V'],r['rcol_scale'],r['rbuf_scale'],r['external_bias_C_pF'])!=('typical',27,3.3,1,1,5) or r['status']!='complete':continue
 a=np.loadtxt(root/'build/bias-reference/scan'/name/'wave.txt',skiprows=1);m=a[:,0]<=r['scan_delay_s']+40e-6;x=a[m,0]*1e6
 for ax,y in zip(axs,[a[m,8],(a[m,8]-a[m,6])/5.1e6*1e6,a[m,7]/49900*1e6]):
  line,=ax.plot(x,y,label=f'{r["ramp_us"]} µs supply ramp');ax.axvline(r['scan_delay_s']*1e6,color=line.get_color(),ls=':',alpha=.5)
for ax,label in zip(axs,['VDD (V)','Column resistor current (µA)','Buffer resistor current (µA)']):ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(fontsize=8)
axs[0].set_title('Nominal power-up · dotted lines: ramp end + 200 µs controller wait');axs[-1].set_xlabel('Time from power-on (µs)')
fig.savefig(root/'docs/assets/bias-reference-startup.png',dpi=160)
dest=root/'checkpoints/bias-reference';dest.mkdir(exist_ok=True)
for f in ['circuits/board-bias.spice','xschem/board_bias.sch','build/bias-reference/board_bias.spice','build/bias-reference/xschem.log']:
 src=root/f;name='xschem-netlist.spice' if f.startswith('build/') and f.endswith('.spice') else src.name;shutil.copyfile(src,dest/name)
files=sorted(f for f in (root/'build/bias-reference').rglob('*') if f.is_file() and f.name in ['testbench.spice','run.log','result.json','calibrate.spice','calibrate.txt','calibrate.log'])
files += [p,root/'simulations/bias-reference-dc.json']+[root/f for f in ['circuits/bias-scan-template.spice','circuits/bias-dc-template.spice','scripts/bias-reference.py','scripts/check-bias-reference.py','scripts/refine-bias-reference.py']]
manifest={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
with tarfile.open(dest/'evidence.tar.gz','w:gz') as archive:
 for f in files:archive.add(f,arcname=str(f.relative_to(root)))
(dest/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Archived',len(files),'bias-reference evidence files')
