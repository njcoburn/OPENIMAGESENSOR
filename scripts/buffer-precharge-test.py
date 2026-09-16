from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json
root=Path(__file__).resolve().parents[1];m=runpy.run_path(str(root/'scripts/buffer-hardening.py'));run=m['combined']
tasks=[lambda:run('ss',-40,20,variant='_schematic_array'),lambda:run('ss',-40,20,True),lambda:run('ss',-40,40,True),lambda:run('fs',125,40,True)]
results=dict(ThreadPoolExecutor(max_workers=4).map(lambda f:f(),tasks))
(root/'simulations/buffer-precharge.json').write_text(json.dumps(results,indent=2)+'\n')
