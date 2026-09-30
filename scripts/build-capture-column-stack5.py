"""Build a separate physical five-NMOS capture-switch column revision.

Run in the pinned EDA container. The manufacturing option remains unselected.
Shared references, clocks and row/ADC fixtures are external to this test cell.
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
PORTS = ['COL','STORE','CBUF','BUF','SC','SCB','SEL','SELB','BIAS','PREF','VDD','GND']


def run(command, out, log):
    result = subprocess.run(command, cwd=out, capture_output=True, text=True, timeout=600)
    (out/log).write_text(result.stdout+result.stderr)
    assert result.returncode == 0, (command, result.returncode)
    return result.stdout+result.stderr


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--compact',action='store_true',help='Repack at 40 um pitch using eight 32 x 77.76 um plates; conditional development MIM option.')
    parser.add_argument('--wide-power',action='store_true',help='Use 2 um supply rails, 1.2 um current-carrying branches and distributed vias.')
    parser.add_argument('--wide-output',action='store_true',help='Use widened CBUF/BUF rails controlled by --output-width-um.')
    parser.add_argument('--output-width-um',type=float,default=2.0,help='CBUF/BUF width with --wide-output; default 2 um.')
    parser.add_argument('--vdd-width-um',type=float,default=2.0,help='VDD trunk width with --wide-power; ground remains 2 um.')
    args=parser.parse_args();assert args.compact;assert .4<=args.output_width_um<=2 and .4<=args.vdd_width_um<=2
    assert args.wide_power or args.vdd_width_um==2
    out=args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    primitive=out/'primitives'; primitive.mkdir()
    generator=(ROOT/'layout/capture-primitives.tcl').read_text()
    if args.compact:generator='set plate_width_um 32.0\nset plate_length_um 77.76\n'+generator
    (primitive/'generator.tcl').write_text(generator)
    log=run(['magic','-dnull','-noconsole','-rcfile',str(PDK/'magic/gf180mcuD.magicrc'),str(primitive/'generator.tcl')],primitive,'magic.log')
    assert 'PLATE_DRC_COUNT=0' in log and 'PFET_DRC_COUNT=0' in log
    assert '.subckt capture_plate STORE GND' in (primitive/'capture_plate.spice').read_text()
    ly=k.Layout(); ly.dbu=.001
    inputs=[ROOT/'build/readout-primitives/bias_nfet.gds',
            ROOT/'build/layout-probe-verified/nfet_probe.gds',
            ROOT/'build/buffer-primitives/mirror_pfet.gds',
            ROOT/'build/buffer-primitives/buffer_pfet.gds',
            primitive/'capture_pfet.gds',primitive/'capture_plate.gds']
    for path in inputs: ly.read(str(path))
    # Magic's FIXED_BBOX export is an oversized annotation on layer 0/0.
    # It is not process geometry; exclude it from placed-area accounting.
    ly.clear_layer(ly.layer(0,0))
    top=ly.create_cell('capture_column'); dbu=ly.dbu
    def box(layer,x0,y0,x1,y1):
        top.shapes(ly.layer(*layer)).insert(k.Box(*[round(v/dbu) for v in (x0,y0,x1,y1)]))
    def wire(layer,x0,y0,x1,y1,width=.4):
        assert x0==x1 or y0==y1
        box(layer,min(x0,x1)-width/2,min(y0,y1)-width/2,max(x0,x1)+width/2,max(y0,y1)+width/2)
    def via(level,x,y):
        low,cut,high={1:(34,35,36),2:(36,38,42),3:(42,40,46),4:(46,41,81)}[level]
        size=.48 if level==1 else .6
        for metal in (low,high):box((metal,0),x-size/2,y-size/2,x+size/2,y+size/2)
        box((cut,0),x-.13,y-.13,x+.13,y+.13)
    def power_via(x,y):
        for metal in (36,42):box((metal,0),x-.6,y-.6,x+.6,y+.6)
        for dx in [-.3,.3]:
            for dy in [-.3,.3]:box((38,0),x+dx-.13,y+dy-.13,x+dx+.13,y+dy+.13)
    rail_start,rail_pitch,rail_top=(14,2,165) if args.compact else (30,3,285)
    rails={name:rail_start+rail_pitch*i for i,name in enumerate(['GND','STORE','CBUF','COL','BUF','SC','SCB','SEL','SELB','BIAS','PREF','VDD'])}
    rails.update(HN1=10,HN2=12,HN3=8,HN4=7)
    for name,x in rails.items():
        width=2.0 if args.wide_power and name in ['GND','VDD'] else args.output_width_um if args.wide_output and name in ['CBUF','BUF'] else .4
        if args.wide_power and name=='VDD':width=args.vdd_width_um
        wire((42,0),x,0,x,182 if name in ['SC','HN3','HN4'] else rail_top,width)
        if name in PORTS:top.shapes(ly.layer(42,10)).insert(k.Text(name,k.Trans(round(x/dbu),0)))
    placements=[('bias_nfet',('COL','BIAS','GND','GND'),1.26,1.28,-2.04),
        ('nfet_probe',('COL','SC','HN1','GND'),.51,.94,-1.54),
        ('capture_pfet',('COL','SCB','STORE','VDD'),.51,1.44,-2.04),
        ('mirror_pfet',('CBUF','PREF','VDD','VDD'),1.26,10.40,-11.04),
        ('buffer_pfet',('GND','STORE','CBUF','VDD'),.51,10.40,-11.04),
        ('nfet_probe',('BUF','SEL','CBUF','GND'),.51,.94,-1.54),
        ('capture_pfet',('BUF','SELB','CBUF','VDD'),.51,1.44,-2.04),
        ('nfet_probe',('HN1','SC','HN2','GND'),.51,.94,-1.54),
        ('nfet_probe',('HN2','SC','HN3','GND'),.51,.94,-1.54),
        ('nfet_probe',('HN3','SC','HN4','GND'),.51,.94,-1.54),
        ('nfet_probe',('HN4','SC','STORE','GND'),.51,.94,-1.54)]
    for index,(cell,nets,dx,gy,by) in enumerate(placements):
        x,y=(5,[20,32,44,68,96,120,132,144,156,168,180][index]) if args.compact else (15,20+40*index)
        top.insert(k.CellInstArray(ly.cell(cell).cell_index(),k.Trans(round(x/dbu),round(y/dbu))))
        for terminal,((tx,ty,offset),net) in enumerate(zip([(x+dx,y,0),(x,y+gy,0),(x-dx,y,-.8),(x,y+by,-.4)],nets)):
            if args.wide_power and terminal in [0,2] and net in ['GND','VDD']:
                offset=3 if terminal==0 else -3
                shifts=[0,.6,1.2] if terminal==0 else [-.6,0,.6]
                for shift in shifts:via(1,tx,ty+shift)
                for metal in (34,36):box((metal,0),tx-.24,ty+min(shifts)-.24,tx+.24,ty+max(shifts)+.24)
                wire((36,0),tx,ty+max(shifts),tx,ty+offset,.48)
                wire((36,0),tx,ty+offset,rails[net],ty+offset,1.2)
                power_via(rails[net],ty+offset)
                continue
            if args.wide_power and terminal==3 and index==0:offset=-4
            via(1,tx,ty)
            if offset:wire((36,0),tx,ty,tx,ty+offset,.48 if args.wide_power and terminal==3 else .4)
            wire((36,0),tx,ty+offset,rails[net],ty+offset)
            via(2,rails[net],ty+offset)
    plate_x,plate_y,plate_pitch=(17.2,240,83) if args.compact else (33.2,350,44)
    for index in range(8):
        top.insert(k.CellInstArray(ly.cell('capture_plate').cell_index(),k.Trans(round(plate_x/dbu),round((plate_y+plate_pitch*index)/dbu))))
    # Ground plate islands connect only through upper-metal contacts/routes.
    ground_x=plate_x+(16.67 if args.compact else 32.67)
    for net,x,y in [('GND',ground_x,rail_top+15),('STORE',plate_x,rail_top+25)]:
        wire((42,0),rails[net],rail_top,rails[net],y)
        via(3,rails[net],y)
        wire((46,0),rails[net],y,x,y)
        via(4,x,y)
        wire((81,0),x,y,x,plate_y+7*plate_pitch,1.0)
    ly.write(str(out/'column.gds'))
    tcl=f'''gds read {out}/column.gds
load capture_column
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
puts "COLUMN_DRC_COUNT=[drc list count total]"
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
    log=run(['magic','-dnull','-noconsole','-rcfile',str(PDK/'magic/gf180mcuD.magicrc'),str(out/'extract.tcl')],out,'extract.log')
    count=int(re.search(r'COLUMN_DRC_COUNT=(\d+)',log)[1])
    data=dict(capture_series_devices=5,magic_drc_count=count,bbox_um=str(top.dbbox()),wide_power=args.wide_power,wide_output=args.wide_output,output_width_um=args.output_width_um if args.wide_output else .4,
        compact=args.compact,plate_dimensions_um=[32,77.76] if args.compact else [64,38.88],
        vdd_width_um=args.vdd_width_um if args.wide_power else .4,
        column_pitch_um=40 if args.compact else 80,
        scope=__doc__,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    (out/'build.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))


if __name__=='__main__':main()
