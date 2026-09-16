from pathlib import Path
import runpy,json
root=Path(__file__).resolve().parents[1]
g=runpy.run_path(str(root/'scripts/simulate-pad-layout.py'))['engine']('res_ss')
name,r=g['scan']('typical',125,3.0,'diode_ff',cext=1,step=.05)
(root/'simulations/pad-layout-refinement.json').write_text(json.dumps({'case':name,'result':r},indent=2)+'\n')
