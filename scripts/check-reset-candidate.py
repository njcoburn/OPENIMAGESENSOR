"""Check GUI-schematic samples against the independently varied reset deck."""
from pathlib import Path
import json
import numpy as np
root=Path(__file__).resolve().parents[1]
ref=next(r for r in json.loads((root/'simulations/repeatability.json').read_text()) if r['name']=='low_reset_fine')
errors=[]
for key,row in zip(['0','1p','5p'],ref['rows']):
 d=np.loadtxt(root/f'simulations/reset_candidate_{key}',skiprows=1)
 assert np.isfinite(d).all() and d[-1,0]>=.02
 samples=np.interp(np.arange(20)*.001+.00097,d[:,0],d[:,4])
 errors.append(float(np.max(np.abs(samples-row['samples_V'])))*1e6)
assert max(errors)<100,errors
print('Candidate schematic vs sweep maximum errors (uV):',errors)
