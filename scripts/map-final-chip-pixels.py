"""Recover nine photocurrent injection nodes from the final LVS device topology.
No geometry guessing: follow reset, source-follower and row-select connections.
"""
from pathlib import Path
import csv,hashlib,json,re
R=Path(__file__).resolve().parents[1];p=R/'build/filled-demonstrator/routed_extracted.spice';lines=[x.split() for x in p.read_text().splitlines() if x and not x.startswith(('*','+','.'))]
fets=[t for t in lines if t[0].startswith('X') and 'nfet_03v3' in t];diodes=[t for t in lines if t[0].startswith('D') and 'diode_nd2ps_03v3' in t and 'area=0.4n' in t and 'pj=80u' in t];assert len(diodes)==9
rows=[]
for d in diodes:
 sense=d[2];assert d[1]=='GND'
 resets=[t for t in fets if sense in [t[1],t[3]] and re.search(r'\.RST[012]$',t[2])];assert len(resets)==1
 sf=[t for t in fets if t[2]==sense and 'VDD' in [t[1],t[3]]];assert len(sf)==1
 sfnode=sf[0][3] if sf[0][1]=='VDD' else sf[0][1]
 selects=[t for t in fets if sfnode in [t[1],t[3]] and re.search(r'\.ROW[012]$',t[2])];assert len(selects)==1
 sel=selects[0];colnode=sel[3] if sel[1]==sfnode else sel[1];m=re.search(r'\.COL([012])$',colnode);assert m
 row=int(resets[0][2][-1]);assert int(sel[2][-1])==row
 rows.append(dict(row=row,column=int(m[1]),photodiode=d[0],sense=sense,ground=d[1],reset=resets[0][0],source_follower=sf[0][0],row_select=sel[0],reset_gate=resets[0][2],row_gate=sel[2],column_node=colnode,area_um2=400))
rows.sort(key=lambda z:(z['row'],z['column']));assert {(z['row'],z['column']) for z in rows}=={(i,j) for i in range(3) for j in range(3)}
r=dict(source=str(p.relative_to(R)),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pixels=rows,scope='Topology map for later final-chip stimuli; remap/audit if extraction node identities change. No optical simulation performed.')
(R/'simulations/final-chip-pixel-map.json').write_text(json.dumps(r,indent=2)+'\n')
with (R/'docs/final-chip-pixel-map.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Mapped all nine photodiodes through reset/SF/select topology, uniquely to row/column.')
