"""Physically join one compact pixel and capture column, then extract and audit.

Unfilled development tile. Shared references, real drivers and ADC are external.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import hashlib
import heapq
import importlib.util
import json
import re
import sys
import klayout.db as k

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checks',ROOT/'scripts/check-compact-capture.py')
checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
PORTS=['VDD','VRESET','GND','RST0','ROW0','COL0','STORE0','CBUF0','BUF','SC','SCB','SEL0','SELB0','BIAS','PREF']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pixel',type=Path,default=ROOT/'build/compact-pixel-v1-20260926')
    p.add_argument('--column',type=Path,default=ROOT/'build/compact-capture-v4-20260926')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'physical-check-helper.py').write_bytes((ROOT/'scripts/check-compact-capture.py').read_bytes())
    assert json.loads((a.column/'verification.json').read_text())['direct_and_resistor_collapsed_lvs']
    ly=k.Layout()
    sources=[a.column/'column.gds',a.pixel/'pixel.gds']
    for path in sources:ly.read(str(path))
    top=ly.create_cell('compact_tile');dbu=ly.dbu
    top.insert(k.CellInstArray(ly.cell('capture_column').cell_index(),k.Trans()))
    top.insert(k.CellInstArray(ly.cell('pixel_physical').cell_index(),k.Trans(0,round(-80/dbu))))
    def box(metal,x0,y0,x1,y1):
        top.shapes(ly.layer(metal,0)).insert(k.Box(*[round(v/dbu) for v in [x0,y0,x1,y1]]))
    def wire(metal,x0,y0,x1,y1,width):
        assert x0==x1 or y0==y1
        box(metal,min(x0,x1)-width/2,min(y0,y1)-width/2,max(x0,x1)+width/2,max(y0,y1)+width/2)
    def via(level,x,y):
        low,cut,high={2:(36,38,42),3:(42,40,46)}[level]
        for metal in [low,high]:box(metal,x-.3,y-.3,x+.3,y+.3)
        box(cut,x-.13,y-.13,x+.13,y+.13)
    # Physical COL join: M3 endpoints and M4 crossing below the column ports.
    wire(42,38.5,-41.6,38.5,-30,.4);via(3,38.5,-30)
    wire(46,20,-30,38.5,-30,.4);via(3,20,-30)
    wire(42,20,-30,20,0,.4)
    # Shared supply/return feeds connect both blocks through actual metal.
    for x,pixel_y,column_x,join_y in [(-10,-50,14,-20),(-4,-42.8,36,-10)]:
        wire(36,x,pixel_y,0,pixel_y,.4);via(2,x,pixel_y)
        wire(42,x,pixel_y,x,join_y,2);via(3,x,join_y)
        wire(46,x,join_y,column_x,join_y,2);via(3,column_x,join_y)
        wire(42,column_x,join_y,column_x,0,2)
    top.flatten(True)
    for layer in ly.layer_indices():
        for shape in list(top.shapes(layer).each()):
            if shape.is_text():shape.delete()
    def label(name,x,y,metal):
        top.shapes(ly.layer(metal,10)).insert(k.Text(name,k.Trans(round(x/dbu),round(y/dbu))))
    for name,x in [('STORE0',16),('CBUF0',18),('COL0',20),('BUF',22),('SC',24),('SCB',26),('SEL0',28),('SELB0',30),('BIAS',32),('PREF',34)]:label(name,x,0,42)
    for name,y in [('RST0',-46.4),('ROW0',-45.2),('VRESET',-44)]:label(name,0,y,36)
    label('GND',-10,-20,46);label('VDD',-4,-10,46)
    aperture=k.Region(k.Box(*[round(v/dbu) for v in [5,-76,23,-58]]))
    for metal in [34,36,42,46,81]:
        assert (k.Region(top.begin_shapes_rec(ly.layer(metal,0))) & aperture).is_empty()
    top.write(str(out/'tile.gds'))
    reference=['.subckt reference '+' '.join(PORTS),
        'Xpixel_reset VRESET RST0 SENSE GND nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
        'Xpixel_follow VDD SENSE SF GND nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
        'Xpixel_select SF ROW0 COL0 GND nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
        'Dpixel GND SENSE diode_nd2ps_03v3 area=0.4n pj=80u']
    contract=(ROOT/'checkpoints/capture-column-preparation/capture-column.spice').read_text()
    body=contract.split('.subckt capture_column ',1)[1].split('\n',1)[1].split('.ends',1)[0]
    local={'COL':'COL0','STORE':'STORE0','CBUF':'CBUF0','SEL':'SEL0','SELB':'SELB0'}
    for line in body.splitlines():
        if not line.startswith('X'):continue
        fields=line.split();fields[0]='Xcolumn_'+fields[0][1:]
        fields[1:5]=[local.get(n,n) for n in fields[1:5]]
        reference.append(' '.join(fields))
    reference += [f'Xplate{i} STORE0 GND cap_mim_2f0_m4m5_noshield c_width=32u c_length=77.76u' for i in range(8)]
    reference.append('.ends reference')
    (out/'reference.spice').write_text('\n'.join(reference)+'\n')
    tcl=f'''gds read {out}/tile.gds
load compact_tile
flatten flat
load flat
select top cell
set idx 1
foreach pin {{{' '.join(PORTS)}}} {{
 catch {{port $pin make $idx}}
 port $pin index $idx
 incr idx
}}
drc check
drc catchup
puts "TILE_DRC_COUNT=[drc list count total]"
set report [open drc-details.txt w]
puts $report [drc listall why]
close $report
extract do capacitance
extract do coupling
extract do resistance
extresist threshold 1000
extresist minres 100
extresist mindelay 0
extract all
ext2spice lvs
ext2spice subcircuits top on
ext2spice extresist off
ext2spice -o direct.spice
ext2spice cthresh 0
ext2spice extresist on
ext2spice -o raw-rc.spice
save flat
quit -noprompt
'''
    (out/'extract.tcl').write_text(tcl)
    checks.command(['magic','-dnull','-noconsole','-rcfile',checks.PDK/'magic/gf180mcuD.magicrc',out/'extract.tcl'],out,'extract.log')
    count=int(re.search(r'TILE_DRC_COUNT=(\d+)',(out/'extract.log').read_text())[1])
    build=dict(scope=__doc__,magic_drc_errors=count,bbox_um=str(top.dbbox()),ports=PORTS,
               clear_aperture_um=[18,18],source_hashes={str(path.relative_to(ROOT)):sha(path) for path in sources})
    (out/'build.json').write_text(json.dumps(build,indent=2)+'\n')
    assert count==0, 'Magic DRC failed; retained evidence'
    checks.drc(out,'tile.gds','compact_tile','main-drc.lyrdb','klayout.log')
    raw=re.sub(r'\n\+',' ',(out/'raw-rc.spice').read_text())
    assert re.search(r'(?im)^\.subckt flat (.+)',raw)[1].split()==PORTS
    records=[l.split() for l in raw.splitlines() if l and l[0] not in '*.']
    assert all(r[0][0] in 'XDRC' for r in records)
    parent={};graph=defaultdict(list)
    def find(n):
        parent.setdefault(n,n)
        if parent[n]!=n:parent[n]=find(parent[n])
        return parent[n]
    for r in records:
        if r[0][0]=='R':
            v=float(r[3]);assert v>0
            parent[find(r[1])]=find(r[2]);graph[r[1]].append((r[2],v));graph[r[2]].append((r[1],v))
    canon={find(n):n for n in PORTS};assert len(canon)==len(PORTS)
    diode,=[r for r in records if r[0][0]=='D']
    canon[find(diode[2])]='SENSE'
    follow,=[r for r in records if r[0][0]=='X' and len(r)>5 and r[5]=='nfet_03v3' and find(r[2])==find(diode[2])]
    canon[find(follow[3])]='SF'
    def terminals(r):return 2 if r[0][0]=='D' or r[3].startswith('cap_mim_') else 4
    collapsed=[]
    for r in records:
        if r[0][0] not in 'XD':continue
        n=terminals(r);collapsed.append([r[0]]+[canon[find(x)] for x in r[1:n+1]]+r[n+1:])
    def normalized(r):
        n=terminals(r);return tuple(r[1:n+2])+tuple(sorted(r[n+2:]))
    expected=[line.split() for line in reference if line[0] in 'XD']
    assert Counter(map(normalized,collapsed))==Counter(map(normalized,expected))
    assert len(collapsed)==19
    (out/'collapsed.spice').write_text('.subckt collapsed '+' '.join(PORTS)+'\n'+'\n'.join(' '.join(r) for r in collapsed)+'\n.ends collapsed\n')
    for name,sub in [('direct','flat'),('collapsed','collapsed')]:
        checks.command(['netgen','-batch','lvs',f'{out}/{name}.spice {sub}',f'{out}/reference.spice reference',checks.PDK/'netgen/gf180mcuD_setup.tcl',out/f'{name}-lvs.log'],out,f'{name}-netgen.log')
        assert 'Circuits match uniquely' in (out/f'{name}-lvs.log').read_text()
    def value(s):
        m=re.fullmatch(r'([+-]?[\d.]+(?:e[+-]?\d+)?)([fp]?)',s,re.I);assert m,s
        return float(m[1])*{'':1,'f':1e-15,'p':1e-12}[m[2].lower()]
    caps=[r for r in records if r[0][0]=='C']
    negative=[r for r in caps if value(r[3])<0]
    assert all(r[2] in ['GND','0'] for r in negative)
    affected=sorted({canon[find(r[1])] for r in negative})
    assert set(affected)<=set(PORTS),affected
    approximations=[];removed=set()
    for net in affected:
        shunts=[r for r in caps if r[2] in ['GND','0'] and find(r[1])==find(net)]
        total=sum(value(r[3]) for r in shunts);assert total>0,(net,total)
        dist={net:0};queue=[(0,net)]
        while queue:
            v,node=heapq.heappop(queue)
            if v!=dist[node]:continue
            for other,resistance in graph[node]:
                trial=v+resistance
                if trial<dist.get(other,float('inf')):dist[other]=trial;heapq.heappush(queue,(trial,other))
        far=max(dist,key=dist.get);removed.update(r[0] for r in shunts)
        approximations.append(dict(net=net,shunts=shunts,total_F=total,far_node=far,far_path_ohm=dist[far]))
    def matrix(cs):
        pairs=defaultdict(float)
        for r in cs:
            pair=tuple(sorted(find('GND' if x=='0' else x) for x in r[1:3]))
            if pair[0]!=pair[1]:pairs[pair]+=value(r[3])
        return pairs
    original=matrix(caps);variants={'port':set(),'far':set(affected)}
    for net in affected:variants[net.lower()+'-far']={net}
    for mode,far_nets in variants.items():
        derived=[r.copy() for r in records if r[0] not in removed]
        for r in derived:
            if r[0][0]=='C':r[1:3]=['GND' if x=='0' else x for x in r[1:3]]
        for i,approx in enumerate(approximations):
            node=approx['far_node'] if approx['net'] in far_nets else approx['net']
            derived.append([f'CFIX{i}',node,'GND',f'{approx["total_F"]:.17g}'])
        after=matrix([r for r in derived if r[0][0]=='C'])
        assert original.keys()==after.keys() and max(abs(original[key]-after[key]) for key in original)<1e-25
        assert all(value(r[3])>=0 for r in derived if r[0][0]=='C')
        (out/f'rc-{mode}.spice').write_text('.subckt tile '+' '.join(PORTS)+'\n'+'\n'.join(' '.join(r) for r in derived)+'\n.ends tile\n')
    report=dict(**build,klayout_main_drc_errors=0,direct_and_resistor_collapsed_lvs=True,
                mos=10,mim=8,diodes=1,resistors=sum(r[0][0]=='R' for r in records),capacitors=len(caps),
                pixel_roles=dict(sense=diode[2],anode=diode[1],vdd=follow[1]),
                negative_capacitors=negative,shunt_approximations=approximations,
                hashes={path.name:sha(path) for path in out.glob('*.spice')},gds_sha256=sha(out/'tile.gds'))
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
