"""Build isolated 64-pixel strips and short controls; extract and verify explicit RC.
Run inside the pinned tools container. Existing release layouts are untouched.
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess
import klayout.db as k

R=Path(__file__).resolve().parents[1]
PDK=Path('/foss/pdks/gf180mcuD/libs.tech')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,d,log):
    p=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=600)
    (d/log).write_text(p.stdout+p.stderr)
    assert p.returncode==0,(cmd,p.returncode,(p.stdout+p.stderr)[-2000:])
    return p.stdout+p.stderr
class Union:
    def __init__(self): self.p={}
    def find(self,n):
        self.p.setdefault(n,n)
        if self.p[n]!=n:self.p[n]=self.find(self.p[n])
        return self.p[n]
    def join(self,a,b):self.p[self.find(a)]=self.find(b)

def build(out,nr,nc,power_width=.4,upper_power_grid=False,*,pixel_source=None,
          pitch=(80,50),rail_y=None,column_x=75):
    d=out/f'r{nr}c{nc}';d.mkdir()
    src=pixel_source or R/'build/size-study/20um/build/pixel_physical.gds'
    px,py=pitch
    rail_y=rail_y or dict(GND=20,VRESET=35,VDD=38,RST=29,ROW=32)
    bus_top=py*nr-(.5 if pixel_source else 5)
    assert not upper_power_grid or (pitch==(80,50) and pixel_source is None)
    ly=k.Layout();ly.read(str(src));pixel=ly.cell('pixel_physical');top=ly.create_cell('strip');dbu=ly.dbu
    def box(layer,x0,y0,x1,y1):top.shapes(ly.layer(*layer)).insert(k.Box(*[round(v/dbu) for v in (x0,y0,x1,y1)]))
    def wire(layer,x0,y0,x1,y1):box(layer,min(x0,x1)-.2,min(y0,y1)-.2,max(x0,x1)+.2,max(y0,y1)+.2)
    def label(name,x,y,metal):top.shapes(ly.layer(metal,10)).insert(k.Text(name,k.Trans(round(x/dbu),round(y/dbu))))
    for r in range(nr):
        for c in range(nc):top.insert(k.CellInstArray(pixel.cell_index(),k.Trans(round(px*c/dbu),round(py*r/dbu))))
    for c in range(nc):
        x=column_x+px*c;wire((42,0),x,0,x,bus_top);label(f'COL{c}',x,0,42)
    for name,x in [('GND',-10),('VRESET',-7),('VDD',-4)]:
        box((42,0),x-power_width/2,-.2,x+power_width/2,bus_top+.2);label(name,x,0,42)
        for r in range(nr):
            y=rail_y[name]+py*r;wire((36,0),x,y,0,y)
            if power_width>.4:box((36,0),x-power_width/2,y-power_width/2,px*nc+.2,y+power_width/2)
            for metal in (36,42):box((metal,0),x-.3,y-.3,x+.3,y+.3)
            box((38,0),x-.13,y-.13,x+.13,y+.13)
    if upper_power_grid:
        assert nr == 1 and power_width == 2, 'Initial upper-grid experiment is a 2 um rail, single row'
        # M5 power straps occupy y=16..24 and 34..42, above the diode's
        # y=-5..15 optical junction. M3/M4 landing islands at x=78 mod 80
        # clear the existing column wire at x=75. Three-by-three cut arrays
        # connect M2 through M5 at the source and at every fourth pixel.
        feeds = sorted(set([78+80*c for c in range(0,nc,4)]+[78+80*(nc-1)]))
        for name,source_x,y in [('GND',-10,20),('VDD',-4,38)]:
            box((81,0),source_x-1,y-4,80*nc+.2,y+4)
            for x in [source_x]+feeds:
                for metal in (42,46):box((metal,0),x-1,y-1,x+1,y+1)
                for via in (38,40,41):
                    for dx in [-.62,0,.62]:
                        for dy in [-.62,0,.62]:
                            box((via,0),x+dx-.13,y+dy-.13,x+dx+.13,y+dy+.13)
    for r in range(nr):
        label(f'RST{r}',0,rail_y['RST']+py*r,36);label(f'ROW{r}',0,rail_y['ROW']+py*r,36)
    ly.write(str(d/'strip.gds'))
    pins=['VDD','VRESET','GND']+[f'RST{r}' for r in range(nr)]+[f'ROW{r}' for r in range(nr)]+[f'COL{c}' for c in range(nc)]
    tcl=f'''puts "MAGIC_VERSION=[version]"
gds read {d}/strip.gds
load strip
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
puts "STRIP_DRC_COUNT=[drc list count total]"
set report [open drc-details.txt w]
puts $report [drc listall why]
close $report
extract do capacitance
extract do coupling
extract do resistance
extresist threshold 1000
extresist minres 100
extresist mindelay 0
puts "EXTRACT_STYLE=[extract style]"
extract all
ext2spice lvs
ext2spice subcircuits top on
ext2spice extresist off
ext2spice -o direct-devices.spice
ext2spice cthresh 0
ext2spice extresist on
ext2spice -o raw-rc.spice
quit -noprompt
'''
    (d/'extract.tcl').write_text(tcl)
    log=run(['magic','-dnull','-noconsole','-rcfile',str(PDK/'magic/gf180mcuD.magicrc'),str(d/'extract.tcl')],d,'extract.log')
    drc=int(re.search(r'STRIP_DRC_COUNT=(\d+)',log)[1]);assert drc==0,drc
    joined=re.sub(r'\n\+',' ',(d/'raw-rc.spice').read_text())
    records=[l.split() for l in joined.splitlines() if l and l[0] not in '*+.']
    ports=re.search(r'(?im)^\.subckt\s+\S+\s+(.+)$',joined)[1].split();assert set(ports)==set(pins)
    devices=[t for t in records if t[0][0] in 'XD'];res=[t for t in records if t[0][0]=='R'];caps=[t for t in records if t[0][0]=='C']
    assert len(devices)==4*nr*nc and len(res)>0 and len(caps)>0
    assert all(t[0][0] in 'XDRC' for t in records)
    uf=Union()
    for t in res:
        assert float(t[3])>0
        uf.join(t[1],t[2])
    assert len({uf.find(p) for p in pins})==len(pins)
    canon={uf.find(p):p for p in pins};roles={}
    mos=[t for t in devices if t[0][0]=='X']
    for diode in (t for t in devices if t[0][0]=='D'):
        sense=uf.find(diode[2])
        rst=next(t for t in mos if sense in (uf.find(t[1]),uf.find(t[3])) and uf.find('VRESET') in (uf.find(t[1]),uf.find(t[3])))
        r=next(r for r in range(nr) if uf.find(rst[2])==uf.find(f'RST{r}'))
        sf=next(t for t in mos if uf.find(t[2])==sense and uf.find(t[1])==uf.find('VDD'))
        sel=next(t for t in mos if uf.find(t[2])==uf.find(f'ROW{r}') and uf.find(sf[3]) in (uf.find(t[1]),uf.find(t[3])))
        c=next(c for c in range(nc) if uf.find(f'COL{c}') in (uf.find(sel[1]),uf.find(sel[3])))
        key=f'{r}_{c}';assert key not in roles
        roles[key]={'sense':diode[2],'anode':diode[1],'reset_gate':rst[2],'select_gate':sel[2],'vdd':sf[1],'gnd':sf[4],'column':next(n for n in (sel[1],sel[3]) if uf.find(n)==uf.find(f'COL{c}'))}
        canon[sense]=f's{r}_{c}';canon[uf.find(sf[3])]=f'f{r}_{c}'
    assert len(roles)==nr*nc
    for t in records:
        for n in t[1:5] if t[0][0]=='X' else t[1:3]:
            key=uf.find(n)
            if key not in canon:canon[key]=f'floating{len(canon)}'
    modes={}
    for mode in ['rc','capacitance','devices']:
        output=['* Extracted unfilled strip; '+mode,'.subckt array '+' '.join(ports)]
        for t in records:
            kind=t[0][0]
            if mode!='rc' and kind=='R':continue
            if mode=='devices' and kind=='C':continue
            x=t.copy()
            if mode!='rc':
                for i in range(1,5 if kind=='X' else 3):x[i]=canon[uf.find(t[i])]
            if kind=='C' and x[1]==x[2]:continue
            output.append(' '.join(x))
        output.append('.ends array');(d/f'{mode}.spice').write_text('\n'.join(output)+'\n')
        modes[mode]={key:{role:(n if mode=='rc' else canon[uf.find(n)]) for role,n in v.items()} for key,v in roles.items()}
    ref=['.subckt reference '+' '.join(pins)]
    for r in range(nr):
        for c in range(nc):
            ref += [f'Xr{r}_{c} VRESET RST{r} s{r}_{c} GND nfet_03v3 w=1u l=0.5u',f'Xf{r}_{c} VDD s{r}_{c} f{r}_{c} GND nfet_03v3 w=1u l=0.5u',f'Xs{r}_{c} f{r}_{c} ROW{r} COL{c} GND nfet_03v3 w=1u l=0.5u',f'D{r}_{c} GND s{r}_{c} diode_nd2ps_03v3 area=400p pj=80u']
    ref.append('.ends reference');(d/'reference.spice').write_text('\n'.join(ref)+'\n')
    for model,sub in [('devices','array'),('direct-devices','flat')]:
        run(['netgen','-batch','lvs',f'{d}/{model}.spice {sub}',f'{d}/reference.spice reference',str(PDK/'netgen/gf180mcuD_setup.tcl'),str(d/f'{model}-lvs.log')],d,f'{model}-netgen.log')
        assert 'Circuits match uniquely' in (d/f'{model}-lvs.log').read_text()
    data={'rows':nr,'columns':nc,'pixel_pitch_um':list(pitch),'power_width_um':power_width,'pixel_source_sha256':sha(src),'drc_count':drc,'lvs_direct_and_rc_collapsed':True,'ports':ports,'roles':modes,'resistors':len(res),'capacitors':len(caps),'mos':len(mos),'diodes':len(devices)-len(mos),'bbox_um':str(top.dbbox()),'hashes':{p.name:sha(p) for p in d.glob('*.spice')},'gds_sha256':sha(d/'strip.gds'),'scope':'Unfilled strip; explicit Magic integrated wire resistance and capacitance; no pad/clamp/fill or peripheral wiring extraction. Resistance threshold 1 ohm, minres 0.1 ohm, mindelay 0.'}
    data['upper_power_grid'] = ({'metal':5,'width_um':8,'feed_columns':sorted(set(list(range(0,nc,4))+[nc-1])), 'via_array':[3,3],'via_pitch_um':.62,'nets':['GND','VDD']} if upper_power_grid else None)
    (d/'extraction.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({key:data[key] for key in ['rows','columns','drc_count','lvs_direct_and_rc_collapsed','resistors','capacitors']}),flush=True)
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--power-width-um',type=float,default=.4);p.add_argument('--upper-power-grid',action='store_true');p.add_argument('--cases',nargs='+',default=['r1c3','r3c1','r1c64','r64c1']);a=p.parse_args();assert .4<=a.power_width_um<=2
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'prepare-script.py').write_bytes(Path(__file__).read_bytes())
    result=[]
    for case in a.cases:
        match=re.fullmatch(r'r(\d+)c(\d+)',case);assert match,case
        nr,nc=map(int,match.groups())
        result.append(build(out,nr,nc,a.power_width_um,a.upper_power_grid));(out/'extraction.json').write_text(json.dumps(result,indent=2)+'\n')
