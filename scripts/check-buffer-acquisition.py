"""Extend baseline sweep with longer ADC acquisition and numerical refinement."""
from pathlib import Path
import runpy,json
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
m=runpy.run_path(str(root/'scripts/output-buffer.py'));run=m['run'];name,result,wave,dc=run((20,100,True,5))
assert result['max_tracking_error_mV']<1
assert max(abs(x['hold_error_mV']) for x in result['samples'])<1
g=run.__globals__;g['base']=g['base'].replace('tran 0.2u','tran 0.1u').replace('reltol=1e-4','reltol=5e-5');g['out']=root/'build/output-buffer/refined';g['out'].mkdir(exist_ok=True)
_,refined,_,_=run((20,100,True,5))
error=max(abs(a['output_V']-b['output_V'])*1000 for a,b in zip(result['samples'],refined['samples']));assert error<.1,error
p=root/'simulations/output-buffer.json';data=json.loads(p.read_text());data['cases'][name]=result;data['numerical_check']={'case':name,'half_step_max_sample_change_mV':error};p.write_text(json.dumps(data,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(11,4.5),layout='constrained');mask=(wave[:,0]>=.006973)&(wave[:,0]<=.007029)
for col,label in [(2,'Follower BUF'),(3,'ADC input'),(5,'Sampling capacitor')]:ax.plot((wave[mask,0]-.00697)*1e6,wave[mask,col],label=label)
ax.set(xlabel='Time after row selection (µs)',ylabel='Voltage (V)',title='20 µA buffer · 100 pF board + 20 pF sampler · 5 µs acquisition');ax.grid(alpha=.2);ax.legend();fig.savefig(root/'docs/assets/buffer-acquisition.png',dpi=160)
print('Longer acquisition',result['max_tracking_error_mV'],'refinement',error)
