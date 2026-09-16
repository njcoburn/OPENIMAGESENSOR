from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import runpy,json
root=Path(__file__).resolve().parents[1];m=runpy.run_path(str(root/'scripts/buffer-hardening.py'));run=m['combined']
results=dict(ThreadPoolExecutor(max_workers=2).map(lambda v:run('ss',-40,20,variant=v),['_no_inductor','_schematic_readout']))
(root/'simulations/buffer-cold-diagnostics.json').write_text(json.dumps(results,indent=2)+'\n')
