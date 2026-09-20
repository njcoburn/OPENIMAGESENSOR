"""Change only the integration method/order on the isolated direct clamp."""
import importlib.util,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('branch',R/'scripts/diagnose-moscap-branch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
deck=(m.B/'clamp-localFalse-smoothFalse/test.spice').read_text()
body=deck[deck.index('\nX1 ')+1:deck.index('.control')]
def run(case):
 name,options=case
 return m.simulate(name,body,'v(vb,gb) v(db,dg) v(a_56346_55631#,DVSS_B.t335) i(Vport0)',extra_options=options)
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,[('integration-backward-euler','.options maxord=1'),('integration-trapezoidal','.options method=trap')]))
(m.B/'integration.json').write_text(json.dumps(rows,indent=2)+'\n')
