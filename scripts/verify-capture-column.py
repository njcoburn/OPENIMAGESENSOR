"""Verify isolated column connectivity, MIM geometry and independent DRC."""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import heapq
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import klayout.db as k

ROOT=Path(__file__).resolve().parents[1]
PDK=Path('/foss/pdks/gf180mcuD/libs.tech')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();d=a.run.resolve()
    build=json.loads((d/'build.json').read_text())
    assert build['magic_drc_count']==0
    width,length=build.get('plate_dimensions_um',[64,38.88])
    assert (width,length) in [(64,38.88),(32,77.76)]
    assert len(ET.parse(d/'main-drc.lyrdb').getroot().find('items'))==0
    raw=re.sub(r'\n\+',' ',(d/'raw-rc.spice').read_text())
    ports=re.search(r'(?im)^\.subckt flat (.+)',raw)[1].split()
    records=[line.split() for line in raw.splitlines() if line and line[0] not in '*.']
    assert all(r[0][0] in 'XRC' for r in records)
    parent={}
    def find(n):
        parent.setdefault(n,n)
        if parent[n]!=n:parent[n]=find(parent[n])
        return parent[n]
    for r in records:
        if r[0].startswith('R'):
            assert float(r[3])>0
            parent[find(r[1])]=find(r[2])
    canonical={find(n):n for n in ports}
    assert len(canonical)==len(ports)
    collapsed=[]
    for r in records:
        if not r[0].startswith('X'):continue
        count=2 if r[3].startswith('cap_mim_') else 4
        collapsed.append([r[0]]+[canonical[find(n)] for n in r[1:1+count]]+r[1+count:])
    contract=(ROOT/'checkpoints/capture-column-preparation/capture-column.spice').read_text()
    body=contract.split('.subckt capture_column ',1)[1].split('\n',1)[1].split('.ends',1)[0]
    reference=[line.split() for line in body.splitlines() if line.startswith('X')]
    reference += [[f'Xplate{i}','STORE','GND','cap_mim_2f0_m4m5_noshield',f'c_width={width:g}u',f'c_length={length:g}u'] for i in range(8)]
    def normalized(r):
        count=2 if r[3].startswith('cap_mim_') else 4
        return tuple(r[1:count+2])+tuple(sorted(r[count+2:]))
    assert Counter(map(normalized,reference))==Counter(map(normalized,collapsed))
    for name,body in [('reference',reference),('collapsed',collapsed)]:
        (d/f'{name}.spice').write_text(f'.subckt {name} '+ ' '.join(ports)+'\n'+'\n'.join(' '.join(r) for r in body)+f'\n.ends {name}\n')
    for name,sub in [('direct','flat'),('collapsed','collapsed')]:
        result=subprocess.run(['netgen','-batch','lvs',f'{d}/{name}.spice {sub}',f'{d}/reference.spice reference',str(PDK/'netgen/gf180mcuD_setup.tcl'),str(d/f'{name}-lvs.log')],cwd=d,capture_output=True,text=True,timeout=120)
        (d/f'{name}-netgen.log').write_text(result.stdout+result.stderr)
        assert result.returncode==0
        assert 'Circuits match uniquely' in (d/f'{name}-lvs.log').read_text()
    ly=k.Layout();ly.read(str(d/'column.gds'));top=ly.cell('capture_column')
    plates=k.Region(top.begin_shapes_rec(ly.layer(75,0))).merged()
    bottom=k.Region(top.begin_shapes_rec(ly.layer(46,0))).merged()
    plate_areas=[poly.area()*ly.dbu**2 for poly in plates.each()]
    assert len(plate_areas)==8 and all(abs(area-width*length)<1e-6 for area in plate_areas)
    if build.get('compact'):
        assert top.dbbox().left>=0 and top.dbbox().right<=40
        assert top.dbbox().height()<900, 'Leave space within the 1100 um bank budget for shared routing'
    groups=[]
    for island in bottom.each():
        overlaps=k.Region(island)&plates
        if overlaps.is_empty():continue
        area=overlaps.area()*ly.dbu**2
        assert area<=10000
        groups.append(area)
    assert len(groups)==8
    assert (k.Region(top.begin_shapes_rec(ly.layer(40,0))) & bottom & plates).is_empty()
    mim=sum(1 for r in collapsed if r[3].startswith('cap_mim_'))
    caps=[r for r in records if r[0].startswith('C')]
    def capvalue(v):
        match=re.fullmatch(r'([+-]?[0-9.]+(?:e[+-]?[0-9]+)?)([fp]?)',v,re.I)
        assert match,v
        return float(match[1])*{'':1,'f':1e-15,'p':1e-12}[match[2].lower()]
    capacitances=[capvalue(r[3]) for r in caps]
    negative_caps=[r for r,c in zip(caps,capacitances) if c<0]
    # Preserve signed shunt totals and all other records. Compact placement
    # also produces a negative BIAS correction; qualify each placement separately.
    nets=['COL','BIAS'] if build.get('compact') else ['COL']
    assert all(any(find(r[1])==find(net) for net in nets) and r[2]=='GND' for r in negative_caps)
    graph={}
    for r in records:
        if r[0].startswith('R'):
            graph.setdefault(r[1],[]).append((r[2],float(r[3])))
            graph.setdefault(r[2],[]).append((r[1],float(r[3])))
    approximations=[];removed=set()
    for net in nets:
        shunts=[r for r in caps if find(r[1])==find(net) and r[2]=='GND']
        total=sum(capvalue(r[3]) for r in shunts);assert total>0
        distance={net:0};queue=[(0,net)]
        while queue:
            value,node=heapq.heappop(queue)
            if value!=distance[node]:continue
            for other,resistance in graph.get(node,[]):
                trial=value+resistance
                if trial<distance.get(other,float('inf')):
                    distance[other]=trial;heapq.heappush(queue,(trial,other))
        far=max(distance,key=distance.get)
        removed.update(r[0] for r in shunts)
        approximations.append(dict(net=net,removed_shunts=shunts,total_fF=total*1e15,
            placements=[net,far],far_path_ohm=distance[far],all_resistors_retained=True,
            scope='Total shunt capacitance preserved; distributed placement approximated and requires sensitivity test.'))
    variants={'rc-port':set(),'rc-far':set(nets)}
    if build.get('compact'):
        variants.update({'rc-col-far':{'COL'},'rc-bias-far':{'BIAS'}})
    def matrix(capacitors):
        pairs={}
        for r in capacitors:
            key=tuple(sorted([find(r[1]),find(r[2])]))
            if key[0]!=key[1]:pairs[key]=pairs.get(key,0)+capvalue(r[3])
        return pairs
    original=matrix(caps);matrix_error=0
    for name,far_nets in variants.items():
        lines=[line for line in raw.splitlines() if not line.split() or line.split()[0] not in removed]
        index=next(i for i,line in enumerate(lines) if line.lower().startswith('.ends'))
        for approximation in approximations:
            net=approximation['net'];node=approximation['placements'][int(net in far_nets)]
            total=sum(capvalue(r[3]) for r in approximation['removed_shunts'])
            lines.insert(index,f'C{net.lower()}distributed {node} GND {total:.17g}')
        after_caps=[line.split() for line in lines if line.startswith('C')]
        assert all(capvalue(r[3])>=0 for r in after_caps)
        after=matrix(after_caps);assert original.keys()==after.keys()
        matrix_error=max(matrix_error,max(abs(original[key]-after[key]) for key in original))
        assert matrix_error<1e-25
        (d/(name+'.spice')).write_text('\n'.join(lines)+'\n')
    report=dict(scope='Unfilled isolated column; 2 fF MIM candidate, nominal wire RC; no optical array or shared peripheral grid.',
        magic_drc_errors=0,klayout_main_drc_errors=0,
        excluded_drc_decks=['antenna','density','cup'],
        direct_and_resistor_collapsed_lvs=True,exact_device_parameters_match=True,
        mos=7,mim_devices=mim,resistors=sum(r[0].startswith('R') for r in records),
        parasitic_capacitors=len(caps),sum_all_parasitic_capacitances_pF=sum(capacitances)*1e12,
        negative_parasitic_capacitors=negative_caps,
        raw_rc_passivity_qualified=not negative_caps,
        capacitance_approximation=approximations[0],
        capacitance_approximations=approximations,
        collapsed_capacitance_matrix_max_error_F=matrix_error,
        placement_model_hashes={name:hashlib.sha256((d/(name+'.spice')).read_bytes()).hexdigest() for name in variants},
        mim_plate_areas_um2=plate_areas,separate_bottom_plate_groups=len(groups),
        lower_via_overlap_with_plate_um2=0,bbox_um=str(top.dbbox()),
        plate_dimensions_um=[width,length],column_pitch_um=build.get('column_pitch_um',80),
        geometry_storage_model_pF_at_25C=8*(.00199*width*1e-6*length*1e-6+2.383e-10*2*(width+length)*1e-6)*1e12,
        hashes={name:hashlib.sha256((d/name).read_bytes()).hexdigest() for name in ['column.gds','direct.spice','raw-rc.spice','rc-port.spice','rc-far.spice','reference.spice','collapsed.spice','main-drc.lyrdb']})
    (d/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
