"""Plot the controlled 16-column ground-bus comparison from audited reports."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'simulations/compact-bank-16-qualification.json').read_text())
old=json.loads((ROOT/r['refined_run']/'result.json').read_text())
new=json.loads((ROOT/r['ground_bus_revision']['run']/'result.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout='constrained')
for run,events,label,color in [(old,r['event_diagnosis'],'Original 2 µm bus','#c45438'),
                              (new,r['ground_bus_revision']['events'],'Revised 8 µm bus','#16798a')]:
    error=[max(abs(s['total_capture_readout_error_V'])*1e6 for s in run['samples'] if s['column']==c) for c in range(16)]
    shifts=[]
    for col in events['columns']:
        values={v['event']:v['values']['mim_average_ground_V'] for v in col['events']}
        shifts.append((values['after_row_off']-values['before_row_off'])*1e6)
    axes[0].plot(range(16),error,'o-',label=label,color=color,markersize=4)
    axes[1].plot(range(16),shifts,'o-',label=label,color=color,markersize=4)
axes[0].axhline(500,color='#6f3434',linestyle='--',label='500 µV accuracy limit')
axes[0].set(title='Worst total error across both scans',ylabel='Absolute ADC error (µV)',ylim=(0,None))
axes[1].set(title='Storage-plate ground movement at row off',ylabel='Mean MIM ground change (µV)')
for ax in axes:
    ax.set(xlabel='Column (even: dark; odd: 240 pA)',xticks=range(0,16,2))
    ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('16 columns · typical models · 27 °C · 100 ns maximum step',fontsize=12)
fig.savefig(ROOT/'docs/assets/compact-bank-16-ground.png',dpi=160)
