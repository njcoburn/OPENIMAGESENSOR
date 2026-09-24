"""Isolated unfilled array layout, C-only extraction and row-scan scaling experiment.
Run inside the tools container; never overwrites production layout artifacts.
"""
from pathlib import Path
import argparse, subprocess, json, re, hashlib
import numpy as np
import klayout.db as k
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
source=root/'build/size-study/20um/build/pixel_physical.gds'
pdk=Path('/foss/pdks/gf180mcuD/libs.tech')
results=[]
def run(cmd,cwd,log):
 r=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=180)
 (cwd/log).write_text(r.stdout+r.stderr)
 if r.returncode: raise RuntimeError((r.stdout+r.stderr)[-2000:])
 return r.stdout+r.stderr
for nr,nc in [(3,3),(4,3),(3,4),(4,4)]:
 d=out/f'r{nr}c{nc}';d.mkdir();ly=k.Layout();ly.read(str(source));pixel=ly.cell('pixel_physical');top=ly.create_cell('array_core');dbu=ly.dbu
 def box(layer,x0,y0,x1,y1):top.shapes(ly.layer(*layer)).insert(k.Box(*[round(v/dbu) for v in (x0,y0,x1,y1)]))
 def wire(layer,x0,y0,x1,y1):box(layer,min(x0,x1)-.2,min(y0,y1)-.2,max(x0,x1)+.2,max(y0,y1)+.2)
 def label(name,x,y,metal):top.shapes(ly.layer(metal,10)).insert(k.Text(name,k.Trans(round(x/dbu),round(y/dbu))))
 for r in range(nr):
  for c in range(nc):top.insert(k.CellInstArray(pixel.cell_index(),k.Trans(round(80*c/dbu),round(50*r/dbu))))
 for c in range(nc):
  x=75+80*c;wire((42,0),x,0,x,50*nr-5);label(f'COL{c}',x,0,42)
 for name,x,y0 in [('GND',-10,20),('VRESET',-7,35),('VDD',-4,38)]:
  wire((42,0),x,0,x,50*nr-5);label(name,x,0,42)
  for r in range(nr):
   y=y0+50*r;wire((36,0),x,y,0,y)
   for metal in (36,42):box((metal,0),x-.3,y-.3,x+.3,y+.3)
   box((38,0),x-.13,y-.13,x+.13,y+.13)
 for r in range(nr):
  label(f'RST{r}',0,29+50*r,36);label(f'ROW{r}',0,32+50*r,36)
 ly.write(str(d/'array.gds'))
 pins=['VDD','VRESET','GND']+[f'RST{r}' for r in range(nr)]+[f'ROW{r}' for r in range(nr)]+[f'COL{c}' for c in range(nc)]
 tcl=f'''gds read {d}/array.gds
load array_core
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
puts "ARRAY_DRC_COUNT=[drc list count total]"
set report [open drc-details.txt w]
puts $report [drc listall why]
close $report
extract all
ext2spice lvs
ext2spice subcircuits top on
ext2spice -o devices.spice
ext2spice cthresh 0
ext2spice extresist off
ext2spice -o capacitance.spice
quit -noprompt
'''
 (d/'extract.tcl').write_text(tcl);log=run(['magic','-dnull','-noconsole','-rcfile',str(pdk/'magic/gf180mcuD.magicrc'),str(d/'extract.tcl')],d,'extract.log')
 drc=int(re.search(r'ARRAY_DRC_COUNT=(\d+)',log)[1])
 raw=(d/'capacitance.spice').read_text();joined=re.sub(r'\n\+', ' ',raw)
 header=re.search(r'(?im)^\.subckt\s+(\S+)\s+(.+)$',joined);sub=header[1];ports=header[2].split();assert set(ports)==set(pins),(ports,pins)
 devices=[l.split() for l in joined.splitlines() if l.startswith(('X','D'))]
 assert len([x for x in devices if x[0].startswith('X')])==3*nr*nc
 assert len([x for x in devices if x[0].startswith('D')])==nr*nc
 senses={}
 for diode in [x for x in devices if x[0].startswith('D')]:
  sense=diode[2]
  reset=next(x for x in devices if x[0].startswith('X') and sense in (x[1],x[3]) and 'VRESET' in (x[1],x[3]))
  r=int(reset[2][3:]);sf=next(x for x in devices if x[0].startswith('X') and x[2]==sense);f=sf[3] if sf[1]=='VDD' else sf[1]
  sel=next(x for x in devices if x[0].startswith('X') and f in (x[1],x[3]) and x[2]==f'ROW{r}')
  col=next(v for v in (sel[1],sel[3]) if v.startswith('COL'));c=int(col[3:]);senses[r,c]=sense
 assert len(senses)==nr*nc
 # Independently generated ideal wiring reference for LVS.
 ref=['.subckt reference '+' '.join(pins)]
 for r in range(nr):
  for c in range(nc):
   ref += [f'Xr{r}_{c} VRESET RST{r} s{r}_{c} GND nfet_03v3 w=1u l=0.5u',f'Xf{r}_{c} VDD s{r}_{c} f{r}_{c} GND nfet_03v3 w=1u l=0.5u',f'Xs{r}_{c} f{r}_{c} ROW{r} COL{c} GND nfet_03v3 w=1u l=0.5u',f'D{r}_{c} GND s{r}_{c} diode_nd2ps_03v3 area=400p pj=80u']
 ref+=['.ends reference'];(d/'reference.spice').write_text('\n'.join(ref)+'\n')
 run(['netgen','-batch','lvs',f'{d}/devices.spice {sub}',f'{d}/reference.spice reference',str(pdk/'netgen/gf180mcuD_setup.tcl'),str(d/'lvs.log')],d,'netgen.log')
 lvs='Circuits match uniquely' in (d/'lvs.log').read_text();assert lvs,(d/'lvs.log').read_text()[-3000:]
 entry={'rows':nr,'columns':nc,'drc_count':drc,'lvs_match':lvs,'capacitors':len(re.findall(r'(?m)^C',raw)),'runs':{}}
 for mode in ['devices','capacitance']:
  period=nr*.001;stop=period*3+.00005
  lines=['Array extension isolated row scan',f'.include {pdk}/ngspice/design.ngspice',f'.lib {pdk}/ngspice/sm141064.ngspice typical',f'.lib {pdk}/ngspice/sm141064.ngspice diode_typical',f'.include {d}/{mode}.spice','.options gmin=1e-17 abstol=1e-16 reltol=1e-5 chgtol=1e-18 trtol=1 method=gear','Vdd VDD 0 3.3','Vreset VRESET 0 2', 'Xarray '+' '.join('0' if n=='GND' else n for n in ports)+' '+sub]
  pattern=[[ [0,80,240][(c+2*r)%3] for c in range(nc)] for r in range(nr)]
  for r in range(nr):
   delay=50+1000*r
   lines += [f'Vr{r} DRST{r} 0 PULSE(0 3.3 {delay}u 10n 10n 20u {nr}m)',f'Vs{r} DROW{r} 0 PULSE(0 3.3 {delay+920}u 10n 10n 60u {nr}m)',f'Rrst{r} DRST{r} RST{r} 100',f'Rrow{r} DROW{r} ROW{r} 100']
   for c in range(nc):lines += [f'Ilight{r}_{c} xarray.{senses[r,c]} 0 {pattern[r][c]}p']
  for c in range(nc):lines += [f'Rload{c} COL{c} 0 1Meg',f'Cload{c} COL{c} 0 1p']
  wave=d/f'{mode}.txt';lines+=['.control','set num_threads=1','set wr_singlescale','set wr_vecnames',f'tran 0.2u {stop} 0 0.2u',f'wrdata {wave} '+' '.join(f'v(COL{c})' for c in range(nc)),'quit','.endc','.end']
  tb=d/f'{mode}-tb.spice';tb.write_text('\n'.join(lines)+'\n');slog=run(['ngspice','-b',str(tb)],d,f'{mode}-sim.log')
  if re.search('timestep too small|simulation.*aborted',slog,re.I):
   entry['runs'][mode]={'completed':False,'reason':'ngspice transient aborted; see log'};continue
  data=np.loadtxt(wave,skiprows=1);assert np.isfinite(data).all() and data[-1,0]>=stop-1e-12
  frames=[[[float(np.interp(f*period+r*.001+.00102,data[:,0],data[:,c+1])) for c in range(nc)] for r in range(nr)] for f in range(3)]
  monotonic=all(all(frames[-1][r][c]>frames[-1][r][j] for c in range(nc) for j in range(nc) if pattern[r][c]<pattern[r][j]) for r in range(nr))
  entry['runs'][mode]={'completed':True,'stop_s':float(data[-1,0]),'brightness_order_correct':monotonic,'frames_V':frames,'last_two_frames_max_change_V':float(np.max(np.abs(np.array(frames[-1])-np.array(frames[-2]))))}
 entry['photocurrent_pA']=pattern;results.append(entry);print(json.dumps(entry),flush=True)
 (out/'results.json').write_text(json.dumps({'pixel_source':str(source),'pixel_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Unfilled array core; extracted devices versus C-only PEX; ideal supplies, 100-ohm control drivers, independent 1Meg || 1p column loads; no shared readout, pads/clamps, fill or wire resistance. Three frames.','cases':results},indent=2)+'\n')
