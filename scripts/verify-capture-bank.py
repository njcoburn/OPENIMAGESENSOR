"""Audit bank devices, both LVS paths, main DRC, and explicit RC topology.

Negative substrate-shunt corrections are preserved in raw evidence. Diagnostic
near/far models conserve each affected net's total shunt and every resistor;
their transient placement sensitivity must be qualified separately.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import hashlib
import heapq
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import klayout.db as k

PDK=Path('/foss/pdks/gf180mcuD/libs.tech')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();d=a.run.resolve()
    (d/'verify-runner.py').write_bytes(Path(__file__).read_bytes())
    build=json.loads((d/'build.json').read_text());nc=build['columns']
    assert build['magic_drc_count']==0
    items=ET.parse(d/'main-drc.lyrdb').getroot().find('items')
    assert items is not None and len(items)==0, 'KLayout main DRC failed'
    raw=re.sub(r'\n\+',' ',(d/'raw-rc.spice').read_text())
    ports=re.search(r'(?im)^\.subckt flat (.+)',raw)[1].split()
    assert ports==build['ports']
    records=[l.split() for l in raw.splitlines() if l and l[0] not in '*.']
    assert all(r[0][0] in 'XRC' for r in records)
    assert len({r[0].lower() for r in records})==len(records)
    parent={}
    def find(n):
        parent.setdefault(n,n)
        if parent[n]!=n: parent[n]=find(parent[n])
        return parent[n]
    graph=defaultdict(list)
    resistors=[r for r in records if r[0].startswith('R')]
    for r in resistors:
        value=float(r[3]);assert value>0
        parent[find(r[1])]=find(r[2])
        graph[r[1]].append((r[2],value));graph[r[2]].append((r[1],value))
    assert resistors
    canon={find(n):n for n in ports}
    assert len(canon)==len(ports),'Bank port short'
    def normalized(r):
        count=2 if r[3].startswith('cap_mim_') else 4
        return tuple(r[1:count+2])+tuple(sorted(r[count+2:]))
    collapsed=[];roles=defaultdict(dict)
    for r in records:
        if not r[0].startswith('X'):continue
        count=2 if r[3].startswith('cap_mim_') else 4
        c=[r[0]]+[canon[find(n)] for n in r[1:count+1]]+r[count+1:]
        collapsed.append(c)
        if count==4 and c[2].startswith('STORE'):
            column=int(c[2][5:]);assert 'follower' not in roles[column]
            roles[column]['follower']=dict(zip(['drain','gate','source','body'],r[1:5]))
        if count==4 and c[2]=='BIAS' and c[1].startswith('COL'):
            column=int(c[1][3:]);roles[column]['bias']=dict(zip(['drain','gate','source','body'],r[1:5]))
        if count==4 and c[2]=='SC':
            column=int(c[1][3:]);roles[column]['capture']=dict(zip(['drain','gate','source','body'],r[1:5]))
    reference=[l.split() for l in (d/'reference.spice').read_text().splitlines() if l.startswith('X')]
    assert Counter(map(normalized,collapsed))==Counter(map(normalized,reference))
    assert len(collapsed)==nc*15+2 and len(roles)==nc
    (d/'collapsed.spice').write_text('.subckt collapsed '+' '.join(ports)+'\n'+
        '\n'.join(' '.join(r) for r in collapsed)+'\n.ends collapsed\n')
    for name,sub in [('direct','flat'),('collapsed','collapsed')]:
        command=['netgen','-batch','lvs',f'{d}/{name}.spice {sub}',f'{d}/reference.spice reference',str(PDK/'netgen/gf180mcuD_setup.tcl'),str(d/f'{name}-lvs.log')]
        result=subprocess.run(command,cwd=d,capture_output=True,text=True,timeout=300)
        (d/f'{name}-netgen.log').write_text(result.stdout+result.stderr)
        assert result.returncode==0 and 'Circuits match uniquely' in (d/f'{name}-lvs.log').read_text()
    ly=k.Layout();ly.read(str(d/'bank.gds'));top=ly.cell('capture_bank')
    plates=k.Region(top.begin_shapes_rec(ly.layer(75,0))).merged()
    bottom=k.Region(top.begin_shapes_rec(ly.layer(46,0))).merged()
    areas=[poly.area()*ly.dbu**2 for poly in plates.each()]
    assert len(areas)==8*nc and all(abs(v-64*38.88)<1e-6 for v in areas)
    groups=[]
    for island in bottom.each():
        overlap=k.Region(island)&plates
        if overlap.is_empty():continue
        area=overlap.area()*ly.dbu**2;assert area<=10000
        groups.append(area)
    assert len(groups)==8*nc
    assert (k.Region(top.begin_shapes_rec(ly.layer(40,0))) & bottom & plates).is_empty()
    def capvalue(v):
        return float(v[:-1])*{'f':1e-15,'p':1e-12}[v[-1]] if v[-1] in 'fp' else float(v)
    caps=[r for r in records if r[0].startswith('C')]
    negative=[r for r in caps if capvalue(r[3])<0]
    # Magic represents the common substrate shunts using global node 0 in this
    # flat bank. Bind it explicitly to the bank's GND feed in derived models.
    assert all(r[2] in ['0','GND'] for r in negative)
    affected=sorted({canon[find(r[1])] for r in negative})
    approximations=[];removed=set()
    distances={}
    for net in ports:
        dist={net:0};queue=[(0,net)]
        while queue:
            value,node=heapq.heappop(queue)
            if value!=dist[node]:continue
            for other,resistance in graph[node]:
                trial=value+resistance
                if trial<dist.get(other,float('inf')):
                    dist[other]=trial;heapq.heappush(queue,(trial,other))
        distances[net]=dist
    for net in affected:
        shunts=[r for r in caps if r[2] in ['0','GND'] and find(r[1])==find(net)]
        total=sum(capvalue(r[3]) for r in shunts);assert total>0,(net,total)
        removed.update(r[0] for r in shunts)
        far=max(distances[net],key=distances[net].get)
        approximations.append(dict(net=net,removed_shunts=shunts,total_F=total,far_node=far,
                                   far_path_ohm=distances[net][far]))
    for placement in ['port','far']:
        lines=['* Diagnostic substrate-shunt placement; see verification.json.',
               '.subckt bank '+' '.join(ports)]
        for r in records:
            if r[0] in removed:continue
            c=r.copy()
            if c[0].startswith('C'):c[1:3]=['GND' if n=='0' else n for n in c[1:3]]
            lines.append(' '.join(c))
        for i,approx in enumerate(approximations):
            node=approx['net'] if placement=='port' else approx['far_node']
            lines.append(f'Cshunt{i} {node} GND {approx["total_F"]:.17g}')
        lines.append('.ends bank')
        (d/f'rc-{placement}.spice').write_text('\n'.join(lines)+'\n')
    report=dict(columns=nc,mos=7*nc+2,mim_devices=8*nc,resistors=len(resistors),
        parasitic_capacitors=len(caps),negative_parasitic_capacitors=negative,
        magic_drc_errors=0,klayout_main_drc_errors=0,direct_and_resistor_collapsed_lvs=True,
        exact_device_parameters_match=True,distinct_connected_ports=len(ports),
        separate_bottom_plate_groups=len(groups),plate_area_um2=64*38.88,
        bbox_um=build['bbox_um'],roles=roles,
        max_shortest_resistive_path_ohm={n:max(dist.values()) for n,dist in distances.items()},
        negative_shunt_approximations=approximations,
        all_resistors_retained=True,raw_rc_passivity_qualified=not negative,
        substrate_assumption='Global substrate capacitance node 0 is explicitly bound to the bank GND feed; substrate spreading resistance is not extracted.',
        placement_sensitivity_qualified=False,full_row_transient_qualified=False,
        scope='Standalone shared capture bank; nominal wire RC, conditional 2 fF MIM; no attached physical row, drivers, pads, fill or manufacturing qualification.',
        excluded_drc_decks=['antenna','density','cup'],
        hashes={name:hashlib.sha256((d/name).read_bytes()).hexdigest() for name in
            ['bank.gds','raw-rc.spice','direct.spice','reference.spice','collapsed.spice','rc-port.spice','rc-far.spice','main-drc.lyrdb']})
    (d/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ['columns','mos','mim_devices','resistors','parasitic_capacitors','magic_drc_errors','klayout_main_drc_errors','direct_and_resistor_collapsed_lvs']}),flush=True)


if __name__=='__main__':main()
