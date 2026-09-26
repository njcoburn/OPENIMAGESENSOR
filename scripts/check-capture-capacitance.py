"""Measure the eight extracted MIM devices with the installed AC/leakage model."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
PDK=Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--extraction',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    text=(a.extraction/'direct.spice').read_text()
    devices=[line for line in text.splitlines() if 'cap_mim_2f0_m4m5_noshield' in line]
    assert len(devices)==8
    dimensions=[dict(re.findall(r'(c_width|c_length)=([\d.]+)u',line)) for line in devices]
    area=sum(float(d['c_width'])*float(d['c_length'])*1e-12 for d in dimensions)
    perimeter=sum(2*(float(d['c_width'])+float(d['c_length']))*1e-6 for d in dimensions)
    nominal=.00199*area+2.383e-10*perimeter
    leakage_conductance=(9.51e-10/5*10000)*area
    results=[]
    for temp in (27,125):
        d=out/str(temp);d.mkdir()
        deck=['Extracted MIM device capacitance and leakage control',
            f'.lib {PDK}/sm141064.ngspice mimcap_typical',f'.temp {temp}',
            '.options gmin=1e-17 abstol=1e-16 reltol=1e-6',
            'Vtest STORE 0 DC 1.6 AC 1',*devices,
            '.control','set num_threads=1','set numdgt=15','op',
            'wrdata leakage.txt i(vtest)','ac lin 1 1 1',
            'let measured_c = -imag(i(vtest))/(2*pi*frequency)',
            'wrdata capacitance.txt measured_c','quit','.endc','.end']
        (d/'test.spice').write_text('\n'.join(deck)+'\n')
        result=subprocess.run(['ngspice','-b','test.spice'],cwd=d,capture_output=True,text=True,timeout=60)
        (d/'ngspice.log').write_text(result.stdout+result.stderr);assert result.returncode==0
        ac=np.loadtxt(d/'capacitance.txt')
        assert ac.shape==(3,) and abs(ac[2])<1e-30
        capacitance=float(ac[1])
        leakage=float(np.loadtxt(d/'leakage.txt')[-1])
        delta=temp-25;factor=1+1.46e-5*delta-5.55e-8*delta**2
        expected=nominal*factor
        # The capacitor model explicitly sets TNOM=25; the leakage resistor
        # inherits ngspice's default TNOM=27 from this fixture.
        resistor_delta=temp-27
        resistor_factor=1+1.46e-5*resistor_delta-5.55e-8*resistor_delta**2
        expected_leakage=-1.6*leakage_conductance/resistor_factor
        assert math.isclose(capacitance,expected,rel_tol=1e-9),(capacitance,expected)
        assert math.isclose(leakage,expected_leakage,rel_tol=1e-6,abs_tol=1e-17),(leakage,expected_leakage)
        results.append(dict(temperature_C=temp,measured_pF=capacitance*1e12,
            expected_pF=expected*1e12,measured_leakage_A=leakage,expected_leakage_A=expected_leakage))
    models={}
    for name in ['sm141064.ngspice','sm141064_mim.spice','sm141064_mim.ngspice']:
        data=(PDK/name).read_bytes();models[name]=hashlib.sha256(data).hexdigest()
        (out/name).write_bytes(data)
    report=dict(scope='Small-signal capacitance and DC leakage of the eight extracted MIM devices; routing parasitics excluded, no transient retention qualification.',
        source_sha256=hashlib.sha256((a.extraction/'direct.spice').read_bytes()).hexdigest(),
        dimensions_um=dimensions,models_sha256=models,results=results,passed=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
