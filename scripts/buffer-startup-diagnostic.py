from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json
root=Path(__file__).resolve().parents[1];m=runpy.run_path(str(root/'scripts/buffer-hardening.py'));run=m['combined']
tasks=[lambda:run('ss',-40,20,variant='_probe_sense'),lambda:run('ss',-40,20,variant='_startup_reset'),lambda:run('ss',-40,40,variant='_startup_reset')]
results=dict(ThreadPoolExecutor(max_workers=3).map(lambda f:f(),tasks))
(root/'simulations/buffer-startup-diagnostic.json').write_text(json.dumps(results,indent=2)+'\n')
