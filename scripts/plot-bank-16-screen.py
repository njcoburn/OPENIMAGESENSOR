"""Render the audited 100 ns temperature/pattern comparison for the overview."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'simulations/compact-bank-16-screen.json').read_text())
patterns=['alternating','inverse','dark','middle','bright']
labels=['Alternating\n0 / 240','Inverse\n240 / 0','Dark\n0','Middle\n80','Bright\n240']
fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for temperature,color,offset in [(27,'#187d91',-.19),(125,'#bc5535',.19)]:
    selected=[next(x for x in r['rows'] if x['temperature_C']==temperature and x['pattern']==p and x['step_ns']==100 and x['model']=='rc-port') for p in patterns]
    for ax,key,title in zip(axes,['max_capture_readout_error_uV','max_output_tracking_error_uV'],
                           ['Total capture/readout error','Output tracking error']):
        values=[x[key] for x in selected]
        bars=ax.bar(np.arange(5)+offset,values,width=.36,color=color,label=f'{temperature} °C')
        ax.bar_label(bars,fmt='%.1f',fontsize=8,padding=3)
        ax.set(title=title,ylabel='Worst absolute error (µV)',xticks=np.arange(5),xticklabels=labels,xlabel='Imposed photocurrent pattern (pA)')
for ax in axes:
    ax.axhline(500,color='#75433b',linestyle='--',label='500 µV limit')
    ax.set_ylim(0,max(550,ax.get_ylim()[1]*1.08));ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    ax.legend(fontsize=8,loc='upper left',ncols=3)
fig.suptitle('Revised 16-column bank · typical process · 100 ns · two readout scans',fontsize=12)
fig.savefig(ROOT/'docs/assets/compact-bank-16-screen.png',dpi=160)
