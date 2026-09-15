from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for key,label in [('0','Dark (0 pA)'),('1p','1 pA'),('5p','5 pA')]:
 data=np.loadtxt('simulations/pixel_'+key,skiprows=1)
 for ax,col in zip(axes,[1,2]): ax.plot(data[:,0]*1000,data[:,col],label=label)
for ax,title in zip(axes,['Photodiode sensing node','Column output']):
 ax.set(xlabel='Time (ms)',ylabel='Voltage (V)',title=title);ax.grid(alpha=.25);ax.legend()
fig.suptitle('GF180 3T pixel — assumed photodiode, continuous row selection')
fig.savefig('simulations/pixel-response.png',dpi=160)
