"""Place qualified capture columns and route a shared peripheral bank.

Development layout, conditional 2 fF MIM option. External bias resistors and
control drivers remain fixtures. Run inside the pinned tools container.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import klayout.db as k

ROOT = Path(__file__).resolve().parents[1]
PDK = Path('/foss/pdks/gf180mcuD/libs.tech')
LOCAL = ['COL', 'STORE', 'CBUF', 'SEL', 'SELB']
RAILS = {name: 30+3*i for i, name in enumerate(
    ['GND','STORE','CBUF','COL','BUF','SC','SCB','SEL','SELB','BIAS','PREF','VDD'])}
BUS_Y = {'VDD': -30, 'GND': -85, 'BIAS': -125, 'PREF': -140,
         'SC': -155, 'SCB': -170, 'BUF': -185}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--column', type=Path, default=ROOT/'build/capture-column-routed-v8-20260925')
    p.add_argument('--columns', type=int, default=64)
    p.add_argument('--reinforced-routing', action='store_true',
                   help='Reinforce supply distribution and reference branches; feed references beside their devices.')
    p.add_argument('--reinforced-buffer', action='store_true',
                   help='Reinforce the local CBUF current path without changing devices.')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert 1 <= a.columns <= 64
    bus_y = (dict(VDD=-50, GND=-145, BIAS=-205, PREF=-220,
                  SC=-235, SCB=-250, BUF=-265) if a.reinforced_routing else BUS_Y)
    strap_offsets = list(range(-40, 41, 10)) if a.reinforced_routing else [-20,-10,0,10,20]
    out = a.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    source = a.column.resolve()
    check = json.loads((source/'verification.json').read_text())
    assert check['direct_and_resistor_collapsed_lvs']
    assert check['magic_drc_errors'] == check['klayout_main_drc_errors'] == 0
    ly = k.Layout(); ly.read(str(source/'column.gds'))
    column = ly.cell('capture_column'); top = ly.create_cell('capture_bank')
    dbu = ly.dbu
    def box(layer, x0, y0, x1, y1):
        top.shapes(ly.layer(*layer)).insert(k.Box(*[round(v/dbu) for v in (x0,y0,x1,y1)]))
    def wire(metal,x0,y0,x1,y1,width):
        assert x0==x1 or y0==y1
        box((metal,0),min(x0,x1)-width/2,min(y0,y1)-width/2,
            max(x0,x1)+width/2,max(y0,y1)+width/2)
    def via(level,x,y,array=1):
        low,cut,high={1:(34,35,36),2:(36,38,42),3:(42,40,46),4:(46,41,81)}[level]
        size=.48 if level==1 else .6
        span=(array-1)*.6+size
        for metal in (low,high): box((metal,0),x-span/2,y-span/2,x+span/2,y+span/2)
        for i in range(array):
            for j in range(array):
                dx=(i-(array-1)/2)*.6;dy=(j-(array-1)/2)*.6
                box((cut,0),x+dx-.13,y+dy-.13,x+dx+.13,y+dy+.13)
    def label(name,x,y,metal):
        top.shapes(ly.layer(metal,10)).insert(k.Text(name,k.Trans(round(x/dbu),round(y/dbu))))
    for c in range(a.columns):
        top.insert(k.CellInstArray(column.cell_index(), k.Trans(round(80*c/dbu),0)))
        if a.reinforced_buffer:
            # Parallel branches join the existing mirror drain and follower
            # source routes. M4 reinforces CBUF without touching STORE plates.
            rail=80*c+RAILS['CBUF']
            wire(46,rail,0,rail,280,2)
            for tap in range(0,281,40): via(3,rail,tap,3)
            for tx,ty,offset,shifts in [
                    (80*c+16.26,140,3,[0,.6,1.2]),
                    (80*c+14.49,180,-3,[-.6,0,.6])]:
                for shift in shifts: via(1,tx,ty+shift)
                for metal in (34,36):
                    box((metal,0),tx-.24,ty+min(shifts)-.24,tx+.24,ty+max(shifts)+.24)
                wire(36,tx,ty+max(shifts),tx,ty+offset,.48)
                wire(36,tx,ty+offset,rail,ty+offset,1.2)
                via(2,rail,ty+offset,2)
                via(3,rail,ty+offset,3)
    # Place each shared reference once, outside the repeated column pitch.
    reference_rails = {'BIAS':-48,'PREF':-43,'VDD':-38,'GND':-33}
    for cell,y,nets,dx,gy,by in [
        ('bias_nfet',20,['BIAS','BIAS','GND','GND'],1.26,1.28,-2.04),
        ('mirror_pfet',100,['PREF','PREF','VDD','VDD'],1.26,10.40,-11.04)]:
        x=-65
        top.insert(k.CellInstArray(ly.cell(cell).cell_index(),k.Trans(round(x/dbu),round(y/dbu))))
        for terminal,((tx,ty,offset),net) in enumerate(zip([(x+dx,y,0),(x,y+gy,0),(x-dx,y,-.8),(x,y+by,-.4)],nets)):
            if a.reinforced_routing and terminal==2:
                offset=-3
                shifts=[-.6,0,.6]
                for shift in shifts: via(1,tx,ty+shift)
                for metal in (34,36):
                    box((metal,0),tx-.24,ty+min(shifts)-.24,tx+.24,ty+max(shifts)+.24)
                wire(36,tx,ty+max(shifts),tx,ty+offset,.48)
                wire(36,tx,ty+offset,reference_rails[net],ty+offset,1.2)
                via(2,reference_rails[net],ty+offset,2)
                continue
            if a.reinforced_routing and terminal==3 and cell=='bias_nfet': offset=-4
            via(1,tx,ty)
            if offset: wire(36,tx,ty,tx,ty+offset,.48 if a.reinforced_routing and terminal==3 else .4)
            wire(36,tx,ty+offset,reference_rails[net],ty+offset,.4)
            via(2,reference_rails[net],ty+offset)
    for net,x in reference_rails.items():
        wire(42,x,bus_y[net],x,125,2 if a.reinforced_routing or net in ['VDD','GND'] else .4)
    right=80*(a.columns-1)+70
    for net,y in bus_y.items():
        supply=net in ['VDD','GND']
        # Parallel 8 um M5 straps avoid an unslotted wide metal plate.
        # M4 crossbars at each feed join the straps through distributed vias.
        if supply:
            for dy in strap_offsets: wire(81,-80,y+dy,right,y+dy,8)
        else: wire(46,-80,y,right,y,4)
        for c in range(a.columns):
            x=80*c+RAILS[net]
            wire(42,x,y,x,0,2 if supply else .6 if net=='BUF' else .4)
            via(3,x,y,3 if supply else 1)
            if supply:
                wire(46,x,y+min(strap_offsets),x,y+max(strap_offsets),2)
                for dy in strap_offsets: via(4,x,y+dy,3)
                if a.reinforced_routing:
                    # M4 crosses the opposite M5 supply without a via. M5
                    # uprights begin at y=0, clear of both horizontal supplies.
                    wire(46,x,y,x,280,2)
                    wire(81,x,0,x,280,8)
                    for tap in range(0,281,40):
                        via(3,x,tap,3)
                        via(4,x,tap,3)
        if net in reference_rails:
            via(3,reference_rails[net],y,3 if supply else 1)
            if supply:
                wire(46,reference_rails[net],y+min(strap_offsets),reference_rails[net],y+max(strap_offsets),2)
                for dy in strap_offsets: via(4,reference_rails[net],y+dy,3)
                if a.reinforced_routing:
                    x=reference_rails[net]
                    wire(46,x,y,x,125,2)
                    for tap in [0,20,60,100,125]: via(3,x,tap,3)
    # Remove all inherited terminal labels before naming the actual bank nets.
    top.flatten(True)
    for layer in ly.layer_indices():
        for shape in list(top.shapes(layer).each()):
            if shape.is_text(): shape.delete()
    for c in range(a.columns):
        for net in LOCAL: label(f'{net}{c}',80*c+RAILS[net],0,42)
    for net,y in bus_y.items():
        feed_x=reference_rails[net] if a.reinforced_routing and net in ['BIAS','PREF'] else (right-80)/2
        label(net,feed_x,y,81 if net in ['VDD','GND'] else 46)
    top.write(str(out/'bank.gds'))
    pins=list(bus_y)+[f'{net}{c}' for c in range(a.columns) for net in LOCAL]
    # Build an independent flat schematic from the previously audited contract.
    contract=(ROOT/'checkpoints/capture-column-preparation/capture-column.spice').read_text()
    body=contract.split('.subckt capture_column ',1)[1].split('\n',1)[1].split('.ends',1)[0]
    reference=['.subckt reference '+' '.join(pins)]
    for c in range(a.columns):
        for line in body.splitlines():
            if not line.startswith('X'): continue
            f=line.split(); f[0]+=str(c)
            f[1:5]=[n+str(c) if n in LOCAL else n for n in f[1:5]]
            reference.append(' '.join(f))
        for i in range(8):
            reference.append(f'Xplate{c}_{i} STORE{c} GND cap_mim_2f0_m4m5_noshield c_width=64u c_length=38.88u')
    reference += contract.split('.subckt capture_references ',1)[1].split('\n',1)[1].split('.ends',1)[0].strip().splitlines()
    reference.append('.ends reference')
    (out/'reference.spice').write_text('\n'.join(reference)+'\n')
    tcl=f'''gds read {out}/bank.gds
load capture_bank
flatten flat
load flat
select top cell
set idx 1
foreach pin {{{' '.join(pins)}}} {{
 catch {{port $pin make $idx}}
 port $pin index $idx
 incr idx
}}
drc check
drc catchup
puts "BANK_DRC_COUNT=[drc list count total]"
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
    report=dict(columns=a.columns,ports=pins,bbox_um=str(top.dbbox()),
        bus_y_um=bus_y,supply_parallel_straps=len(strap_offsets),supply_strap_width_um=8,
        reinforced_routing=a.reinforced_routing,
        reinforced_buffer=a.reinforced_buffer,
        reference_feed='beside-reference-devices' if a.reinforced_routing else 'bus-center',
        supply_strap_pitch_um=10,signal_width_um=4,column_pitch_um=80,
        scope=__doc__,column_source=str(source),
        column_gds_sha256=hashlib.sha256((source/'column.gds').read_bytes()).hexdigest())
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'extract.log').open('w') as log:
        result=subprocess.run(['magic','-dnull','-noconsole','-rcfile',str(PDK/'magic/gf180mcuD.magicrc'),str(out/'extract.tcl')],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
    assert result.returncode==0
    report['magic_drc_count']=int(re.search(r'BANK_DRC_COUNT=(\d+)',(out/'extract.log').read_text())[1])
    report['gds_sha256']=hashlib.sha256((out/'bank.gds').read_bytes()).hexdigest()
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__': main()
