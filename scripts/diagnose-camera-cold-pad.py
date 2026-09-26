"""Bounded isolated unused-pad DC controls; never a camera corner pass.

Retain the eight protection diodes connected to NC_P10, with ideal rails.
The shunted cold control deliberately adds a 1 Tohm external path solely to
probe sensitivity to a floating-pad DC equation; it is not promoted as a fix.
"""
from pathlib import Path
import json,runpy,shutil,hashlib
R=Path(__file__).resolve().parents[1]
h=runpy.run_path(str(R/'scripts/screen-camera-operating-corners.py'))
root=R/'build/camera-operating-corners/cold-pad-diagnostic-20260924';root.mkdir(parents=True,exist_ok=False)
(root/'runner.py').write_bytes(Path(__file__).read_bytes())
init=root/'init';init.mkdir();shutil.copyfile(h['SOURCE']/'init/.spiceinit',init/'.spiceinit')
stock=(h['F']/'stock-model.spice').read_text()
lines=[l for l in stock.splitlines() if l.startswith('D') and 'NC_P10' in l.split()[1:3]]
assert len(lines)==8
cases=[('warm',27,'typical',3.3,False),('cold',-40,'typical',3.3,False),('cold-shunted',-40,'typical',3.3,True),('fast-cold',-40,'ff',3.6,False)]
summary=dict(scope=__doc__,source_stock_sha256=hashlib.sha256(stock.encode()).hexdigest(),diode_records=lines,simulator_sha256=h['digest'](Path(shutil.which('ngspice'))),pdk_sha256=h['digest'](h['LIB']),cases={})
for name,temp,corner,vdd,shunt in cases:
 base=f'Isolated unused-pad DC diagnostic\n.include {h["LIB"].parent}/design.ngspice\n.lib {h["LIB"]} diode_{corner}\n.temp {temp}\n.options gmin=1e-17 reltol=1e-6 abstol=1e-12 chgtol=1e-16 trtol=3 method=trap\nVrail VDD GND {vdd}\n.nodeset v(NC_P10)=1.65\n'+'\n'.join(lines)+'\n'
 if shunt:base+='Rdiagnostic NC_P10 GND 1e12\n'
 dest=root/name;vectors=['v(NC_P10)','i(Vrail)']
 result=h['invoke'](dest,h['dc_deck'](base,vectors),shutil.which('ngspice'),15,init)
 result['used_transient_op_fallback']='Transient op started' in (dest/'ngspice.log').read_text()
 result['singular_matrix_warning']='singular matrix' in (dest/'ngspice.log').read_text()
 if result['completed']:result['op']=h['read_dc'](dest,vectors)
 result.update(temp_C=temp,diode=corner,supply_V=vdd,added_shunt_ohm=1e12 if shunt else None)
 summary['cases'][name]=result;h['write'](root/'summary.json',summary);print(name,result,flush=True)
