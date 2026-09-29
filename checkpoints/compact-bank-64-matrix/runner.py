"""Build a compact shared pixel/capture bank and audit its extracted connections.

Unfilled development control with physical reference MOS and shared wiring.
Reference resistors, control drivers and ADC remain external fixtures.
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
LOCAL=['COL','STORE','CBUF','SEL','SELB']
RAILS={name:14+2*i for i,name in enumerate(['GND','STORE','CBUF','COL','BUF','SC','SCB','SEL','SELB','BIAS','PREF','VDD'])}
BUS_Y=dict(GND=-10,VDD=-20,BIAS=-30,PREF=-40,SC=-50,SCB=-60,BUF=-70)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pixel',type=Path,default=ROOT/'build/compact-pixel-v1-20260926')
    p.add_argument('--column',type=Path,default=ROOT/'build/compact-capture-v4-20260926')
    p.add_argument('--columns',type=int,default=2)
    p.add_argument('--ground-bus-width-um',type=float,choices=[2,4,8],default=2,
                   help='Physical M4 ground bus width; other shared routes retain their original widths')
    p.add_argument('--ground-return-grid',action='store_true',
                   help='Add three 24 um M4 top/left ground rails and M5 returns to every column ground plate trunk')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();assert 2<=a.columns<=64
    PORTS=['VDD','VRESET','GND','RST0','ROW0','BUF','SC','SCB','BIAS','PREF']+[f'{n}{c}' for c in range(a.columns) for n in LOCAL]
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'physical-check-helper.py').write_bytes((ROOT/'scripts/check-compact-capture.py').read_bytes())
    assert json.loads((a.column/'verification.json').read_text())['direct_and_resistor_collapsed_lvs']
    ly=k.Layout()
    sources=[a.column/'column.gds',a.pixel/'pixel.gds']
    for path in sources:ly.read(str(path))
    top=ly.create_cell('compact_bank');dbu=ly.dbu
    for c in range(a.columns):
        top.insert(k.CellInstArray(ly.cell('capture_column').cell_index(),k.Trans(round(40*c/dbu),0)))
        top.insert(k.CellInstArray(ly.cell('pixel_physical').cell_index(),k.Trans(round(40*c/dbu),round(-120/dbu))))
    ground_grid_geometry=[];record_grid=False
    def box(metal,x0,y0,x1,y1):
        top.shapes(ly.layer(metal,0)).insert(k.Box(*[round(v/dbu) for v in [x0,y0,x1,y1]]))
        if record_grid:ground_grid_geometry.append([metal,x0,y0,x1,y1])
    def wire(metal,x0,y0,x1,y1,width):
        assert x0==x1 or y0==y1
        box(metal,min(x0,x1)-width/2,min(y0,y1)-width/2,max(x0,x1)+width/2,max(y0,y1)+width/2)
    def via(level,x,y):
        low,cut,high={1:(34,35,36),2:(36,38,42),3:(42,40,46),4:(46,41,81)}[level]
        half=.24 if level==1 else .3
        for metal in [low,high]:box(metal,x-half,y-half,x+half,y+half)
        box(cut,x-.13,y-.13,x+.13,y+.13)
    # Every column has a local COL join; row controls and pixel supplies abut.
    for c in range(a.columns):
        x=40*c
        wire(42,x+38.5,-81.6,x+38.5,-80,.4);via(3,x+38.5,-80)
        wire(46,x+20,-80,x+38.5,-80,.4);via(3,x+20,-80)
        wire(42,x+20,-80,x+20,0,.4)
    for net,x,pixel_y in [('GND',-10,-90),('VDD',-4,-82.8)]:
        wire(36,x,pixel_y,0,pixel_y,.4);via(2,x,pixel_y)
        wire(42,x,pixel_y,x,BUS_Y[net],2);via(3,x,BUS_Y[net])
    # One physical diode-connected reference pair, outside the repeated pitch.
    reference_rails={'BIAS':-48,'PREF':-43,'VDD':-38,'GND':-33}
    for cell,y,nets,dx,gy,by in [
        ('bias_nfet',20,['BIAS','BIAS','GND','GND'],1.26,1.28,-2.04),
        ('mirror_pfet',100,['PREF','PREF','VDD','VDD'],1.26,10.40,-11.04)]:
        x=-65
        top.insert(k.CellInstArray(ly.cell(cell).cell_index(),k.Trans(round(x/dbu),round(y/dbu))))
        for (tx,ty,offset),net in zip([(x+dx,y,0),(x,y+gy,0),(x-dx,y,-.8),(x,y+by,-.4)],nets):
            via(1,tx,ty)
            if offset:wire(36,tx,ty,tx,ty+offset,.4)
            wire(36,tx,ty+offset,reference_rails[net],ty+offset,.4)
            via(2,reference_rails[net],ty+offset)
    for net,x in reference_rails.items():
        wire(42,x,BUS_Y[net],x,125,2 if net in ['VDD','GND'] else .4)
        via(3,x,BUS_Y[net])
    right=40*(a.columns-1)+38
    for net,y in BUS_Y.items():
        wire(46,-50,y,right,y,a.ground_bus_width_um if net=='GND' else 2)
        for c in range(a.columns):
            x=40*c+RAILS[net]
            wire(42,x,y,x,0,2 if net=='GND' else .8 if net=='VDD' else .6 if net=='BUF' else .4)
            via(3,x,y)
    if a.ground_return_grid:
        column_meta=json.loads((a.column/'verification.json').read_text())
        assert column_meta['column_pitch_um']==40 and column_meta['plate_dimensions_um']==[32,77.76]
        assert a.ground_bus_width_um==8
        record_grid=True
        # 24 um stripes stay below the 30 um unslotted-metal width rule.
        # Square-ended vertical rails avoid the neighboring VDD/BIAS buses.
        for x in [-90,-62,-34]:box(46,x-12,-8,x+12,940)
        wire(46,-90,-10,-20,-10,8)
        plate_ground_x=17.2+16.67
        for y in [884,912,940]:wire(46,-90,y,40*(a.columns-1)+plate_ground_x,y,24)
        for c in range(a.columns):
            x=40*c+plate_ground_x
            wire(81,x,821,x,940,1)
            for y in [884,912,940]:via(4,x,y)
        record_grid=False
    top.flatten(True)
    for layer in ly.layer_indices():
        for shape in list(top.shapes(layer).each()):
            if shape.is_text():shape.delete()
    def label(name,x,y,metal):
        top.shapes(ly.layer(metal,10)).insert(k.Text(name,k.Trans(round(x/dbu),round(y/dbu))))
    for c in range(a.columns):
        for net in LOCAL:label(f'{net}{c}',40*c+RAILS[net],0,42)
    for name,y in [('RST0',-86.4),('ROW0',-85.2),('VRESET',-84)]:label(name,0,y,36)
    for name,y in BUS_Y.items():label(name,reference_rails.get(name,-20),y,46)
    for c in range(a.columns):
        aperture=k.Region(k.Box(*[round(v/dbu) for v in [40*c+5,-116,40*c+23,-98]]))
        for metal in [34,36,42,46,81]:
            assert (k.Region(top.begin_shapes_rec(ly.layer(metal,0))) & aperture).is_empty()
    top.write(str(out/'bank.gds'))
    reference=['.subckt reference '+' '.join(PORTS)]
    contract=(ROOT/'checkpoints/capture-column-preparation/capture-column.spice').read_text()
    body=contract.split('.subckt capture_column ',1)[1].split('\n',1)[1].split('.ends',1)[0]
    for c in range(a.columns):
        reference += [
            f'Xpixel_reset{c} VRESET RST0 SENSE{c} GND nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
            f'Xpixel_follow{c} VDD SENSE{c} SF{c} GND nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
            f'Xpixel_select{c} SF{c} ROW0 COL{c} GND nfet_03v3 w=1u l=0.5u ad=0.44p as=0.44p pd=2.88u ps=2.88u',
            f'Dpixel{c} GND SENSE{c} diode_nd2ps_03v3 area=0.4n pj=80u']
        local={n:n+str(c) for n in LOCAL}
        for line in body.splitlines():
            if not line.startswith('X'):continue
            fields=line.split();fields[0]=f'Xcolumn{c}_'+fields[0][1:]
            fields[1:5]=[local.get(n,n) for n in fields[1:5]]
            reference.append(' '.join(fields))
        reference += [f'Xplate{c}_{i} STORE{c} GND cap_mim_2f0_m4m5_noshield c_width=32u c_length=77.76u' for i in range(8)]
    reference += contract.split('.subckt capture_references ',1)[1].split('\n',1)[1].split('.ends',1)[0].strip().splitlines()
    reference.append('.ends reference')
    (out/'reference.spice').write_text('\n'.join(reference)+'\n')
    tcl=f'''gds read {out}/bank.gds
load compact_bank
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
    build=dict(scope=__doc__,columns=a.columns,column_pitch_um=40,bus_y_um=BUS_Y,ground_bus_width_um=a.ground_bus_width_um,magic_drc_errors=count,bbox_um=str(top.dbbox()),ports=PORTS,
               clear_aperture_um=[18,18],source_hashes={str(path.relative_to(ROOT)):sha(path) for path in sources})
    if a.ground_return_grid:
        build.update(ground_return_grid=True,ground_grid_added_rectangles_um=ground_grid_geometry,
                     ground_grid_scope='Three 24 um M4 rails at y=884/912/940 and x=-90/-62/-34; M5 returns attach each existing ground-plate trunk at y=821.')
    (out/'build.json').write_text(json.dumps(build,indent=2)+'\n')
    assert count==0, 'Magic DRC failed; retained evidence'
    checks.drc(out,'bank.gds','compact_bank','main-drc.lyrdb','klayout.log')
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
    pixel_roles={}
    for diode in [r for r in records if r[0][0]=='D']:
        follow,=[r for r in records if r[0][0]=='X' and len(r)>5 and r[5]=='nfet_03v3' and find(r[2])==find(diode[2])]
        select,=[r for r in records if r[0][0]=='X' and len(r)>5 and r[5]=='nfet_03v3' and find(r[1])==find(follow[3]) and find(r[2])==find('ROW0')]
        net=canon[find(select[3])];assert net.startswith('COL')
        c=int(net[3:]);assert c not in pixel_roles
        canon[find(diode[2])]=f'SENSE{c}';canon[find(follow[3])]=f'SF{c}'
        pixel_roles[c]=dict(sense=diode[2],anode=diode[1],vdd=follow[1])
    assert set(pixel_roles)==set(range(a.columns))
    def terminals(r):return 2 if r[0][0]=='D' or r[3].startswith('cap_mim_') else 4
    collapsed=[]
    for r in records:
        if r[0][0] not in 'XD':continue
        n=terminals(r);collapsed.append([r[0]]+[canon[find(x)] for x in r[1:n+1]]+r[n+1:])
    def normalized(r):
        n=terminals(r);return tuple(r[1:n+2])+tuple(sorted(r[n+2:]))
    expected=[line.split() for line in reference if line[0] in 'XD']
    assert Counter(map(normalized,collapsed))==Counter(map(normalized,expected))
    assert len(collapsed)==19*a.columns+2
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
                mos=10*a.columns+2,mim=8*a.columns,diodes=a.columns,resistors=sum(r[0][0]=='R' for r in records),capacitors=len(caps),
                pixel_roles=pixel_roles,
                negative_capacitors=negative,shunt_approximations=approximations,
                hashes={path.name:sha(path) for path in out.glob('*.spice')},gds_sha256=sha(out/'bank.gds'))
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
