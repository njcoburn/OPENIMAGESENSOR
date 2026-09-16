"""Check nominal Xschem connectivity against the simulation's board subcircuit."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
drawn=(root/'build/bias-reference/board_bias.spice').read_text()
model=(root/'circuits/board-bias.spice').read_text()
ports=next(l.lstrip('*').split()[2:] for l in drawn.splitlines() if l.lstrip('*').startswith('.subckt'))
assert ports==['VDD','GND','BIAS','PREF'],ports
def devices(text):return {t[0]:t[1:] for t in map(str.split,text.splitlines()) if t and t[0][0] in 'RC' and not t[0].startswith('*')}
a=devices(drawn);b=devices(model)
for name,t in b.items():
 value={'{RCOL}':'5.1meg','{RBUF}':'49.9k','{CEXT}':'5p'}[t[2]]
 assert a[name]==[t[0],t[1],value],(name,a[name],t)
assert a.keys()==b.keys()
print('Xschem and board-bias SPICE match: four ports, two resistors, two assumed pin capacitances.')
