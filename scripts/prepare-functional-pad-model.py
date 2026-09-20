"""Normal-operation candidate: freeze only rail/clamp MOS capacitance at settled bias.
Preserves every other final-GDS device and all condensed wiring capacitance.
No startup, ESD or full distributed-R claim; simulation range must be checked.
"""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];B=R/'build/functional-pad-model';B.mkdir(exist_ok=True);S=R/'build/filled-electrical-baseline/filled_condensed.spice'
red=json.loads((S.parent/'reduction.json').read_text());assert red['completed'] and red['devices_unchanged'];assert hashlib.sha256(S.read_bytes()).hexdigest()==red['output_sha256']
raw=S.read_text();raw='\n'.join(l for l in raw.splitlines() if not l.startswith(('.subckt','+','.ends')))+'\n';caps=[]
# Alias extracted node tokens containing simulator command metacharacters.
unsafe=sorted({t for l in raw.splitlines() if l and not l.startswith('*') for t in l.split()[1:] if '$' in t or '/' in t})
aliases={t:f'PEX_SAFE_{i}' for i,t in enumerate(unsafe)}
raw='\n'.join(' '.join(aliases.get(t,t) for t in l.split()) if l and not l.startswith('*') else l for l in raw.splitlines())+'\n'
(B/'node-aliases.json').write_text(json.dumps(aliases,indent=2)+'\n')
def val(t):
 m=re.fullmatch(r'([\d.eE+-]+)([unp]*)',t);return float(m[1])*{'':1,'u':1e-6,'n':1e-9,'p':1e-12}[m[2]]
for l in raw.splitlines():
 if ' cap_nmos_06v0 ' not in l:continue
 s=l.split();assert s[3]=='cap_nmos_06v0';ps=dict(x.split('=') for x in s[4:]);assert set(ps)=={'c_width','c_length'};caps.append(dict(name=s[0],p=s[1],n=s[2],area_m2=val(ps['c_width'])*val(ps['c_length']),line=l))
assert len(caps)==1680
pairs=list(dict.fromkeys((c['p'],c['n']) for c in caps));print('MOS caps',len(caps),'unique terminal pairs',len(pairs))
(B/'stock-model.spice').write_text(raw)
(B/'caps.json').write_text(json.dumps(dict(source_sha256=red['output_sha256'],capacitors=caps,pairs=pairs,scope='Normal-operation candidate only; capacitance freezes at measured OP and requires in-run C(V) validity checks'),indent=2)+'\n')
