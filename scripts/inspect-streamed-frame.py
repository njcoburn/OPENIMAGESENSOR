from pathlib import Path
import runpy,json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; read=runpy.run_path(str(R/'scripts/diagnose-functional-camera.py'))['read_raw']
d=R/'build/functional-camera-diagnostic/nominal-frame-stream'
n,v=read(d/'stream.raw'); n0,v0=read(R/'build/functional-camera-diagnostic/trap-klu-baseline-1200s/stream.raw')
k=int(np.sum(v0[:,0]<=.003230025)); assert n==n0 and np.array_equal(v[:k],v0[:k])
out={'points_compared':k,'exact_prefix_match':True,'comparison_scope_end_s':.003230025}
(d/'diagnostic-prefix-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
keys=['v(ctl_rst2)','v(pad_rst2)','v(ctl_row1)','v(pad_row1)','v(vdd)','v(hold)']
out={'time_s':float(v[-1,0]),'last_values':{key:float(v[-1,n.index(key)]) for key in keys},'interpretation':'Failure coincides with row-2 reset falling-edge endpoint; named branch is not proof of causal device.'}
(d/'failure-edge.json').write_text(json.dumps(out,indent=2)+'\n')
mask=v[:,0]>=.003270005; x=(v[mask,0]-.00327002)*1e9
fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
for key in keys[:4]: axs[0].plot(x,v[mask,n.index(key)],label=key)
axs[0].legend();axs[0].set_ylabel('Control / pad (V)')
axs[1].plot(x,v[mask,n.index('v(vdd)')]);axs[1].set_ylabel('VDD (V)')
axs[2].semilogy(x,np.r_[np.nan,np.diff(v[:,0])][mask]);axs[2].set_ylabel('Accepted step (s)');axs[2].set_xlabel('Time relative to row-2 reset fall endpoint (ns)')
fig.suptitle('Incomplete frame: accepted points preceding solver abort');fig.tight_layout();fig.savefig(d/'failure-edge.png',dpi=140)
print(json.dumps(out))
