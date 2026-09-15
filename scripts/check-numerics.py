"""Run inside the tools container: python3 scripts/check-numerics.py."""
from pathlib import Path
import subprocess, tempfile, re
base = Path('simulations/pixel_3t.spice').read_text()
rows = ['gmin_S,start_V,end_V,drop_mV']
for gmin in ['1e-12', '1e-14', '1e-15', '1e-16', '1e-17', '1e-18']:
    deck = base.replace('gmin=1e-17', f'gmin={gmin}').replace('foreach light 0 1p 5p','foreach light 0')
    deck = '\n'.join(line for line in deck.splitlines() if not line.startswith('wrdata'))
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'check.spice'; path.write_text(deck)
        result=subprocess.run(['ngspice','-b',str(path)],capture_output=True,text=True,check=True)
        output=result.stdout+result.stderr
        if re.search(r'(?im)^error',output): raise RuntimeError(output)
        values=[float(re.search(name+r'\s*=\s*(\S+)',output)[1]) for name in ['sense_start','sense_end']]
        rows.append(f'{gmin},{values[0]},{values[1]},{1000*(values[0]-values[1]):.6f}')
Path('simulations/numerics.csv').write_text('\n'.join(rows)+'\n')
print('\n'.join(rows))
