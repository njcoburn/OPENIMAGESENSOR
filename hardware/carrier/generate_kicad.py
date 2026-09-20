"""Generate native KiCad 7 tester/carrier design from explicit pin maps.
Run in the isolated KiCad container. Mechanical/bond dimensions are provisional.
"""
from pathlib import Path
import csv,json,math,uuid
import pcbnew as p
R=Path(__file__).resolve().parent;OUT=R/'kicad';OUT.mkdir(exist_ok=True)
MM=p.FromMM;V=lambda x,y:p.VECTOR2I(MM(x),MM(y))
uid=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'openimagesensor/carrier/revA/'+s))
q=lambda s:json.dumps(str(s))
def layer_set(*layers):
 z=p.LSET()
 for a in layers:z.AddLayer(a)
 return z
components=[]
def add(ref,val,fp,xy,nets,names=None,types=None,rotation=0,custom=None,side='F',note=''):
 components.append(dict(ref=ref,value=val,footprint=fp,xy=xy,nets={str(a):b for a,b in nets.items()},names=names or {},types=types or {},rotation=rotation,custom=custom,side=side,note=note))
def resistor(ref,val,a,b,x,y):add(ref,val,'Resistor_SMD:R_0805_2012Metric',(x,y),{1:a,2:b})
def capacitor(ref,val,a,b,x,y):add(ref,val,'Capacitor_SMD:C_0805_2012Metric',(x,y),{1:a,2:b})
padrows=list(csv.DictReader((R.parents[1]/'docs/routed-pad-map.csv').open()))
padnet={int(r['pad_id'][1:]):r['original_core_net'] if not r['external_net'].startswith('NC_') else None for r in padrows}
# Board view always looks from +Z toward the die; no mirrored contact numbering.
def contact(i):
 side,j=divmod(i-1,6);v=41.25+3.5*j
 return [(v,64.5),(64.5,100-v),(100-v,35.5),(35.5,v)][side]
def custom_fp(board,kind,ref):
 f=p.FOOTPRINT(board);f.SetFPID(p.LIB_ID('OIS',kind))
 def pad(number,x,y,w,h,drill=0):
  z=p.PAD(f);z.SetNumber(str(number));z.SetPosition(V(x,y));z.SetPos0(V(x,y));z.SetSize(V(w,h));z.SetShape(p.PAD_SHAPE_CIRCLE if w==h else p.PAD_SHAPE_RECT)
  if drill:z.SetAttribute(p.PAD_ATTRIB_PTH);z.SetDrillSize(V(drill,drill));z.SetLayerSet(layer_set(p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu,p.F_Mask,p.B_Mask))
  else:z.SetAttribute(p.PAD_ATTRIB_SMD);z.SetLayerSet(layer_set(p.F_Cu,p.F_Mask))
  f.Add(z)
 def rect(x0,y0,x1,y1,layer):
  s=p.FP_SHAPE(f);s.SetShape(p.SHAPE_T_RECT);s.SetStart(V(x0,y0));s.SetEnd(V(x1,y1));s.SetLocalCoord();s.SetLayer(layer);s.SetWidth(MM(.1));f.Add(s)
 if kind=='Pogo_0906_0':pad(1,0,0,1.6,1.6,.6);rect(-1.05,-1.05,1.05,1.05,p.F_CrtYd)
 elif kind=='Target_2p4':pad(1,0,0,2.4,2.4);rect(-1.4,-1.4,1.4,1.4,p.F_CrtYd)
 elif kind=='Bond_3x3_PROVISIONAL':
  for i in range(1,25):
   side,j=divmod(i-1,6);v=-1.375+.55*j
   x,y=[(v,2.4),(2.4,-v),(-v,-2.4),(-2.4,v)][side]
   pad(i,x,y,.32 if side%2==0 else 1.2,1.2 if side%2==0 else .32)
  rect(-.605,-.605,.605,.605,p.F_Fab);rect(-1,-1,1,1,p.Dwgs_User)
  rect(-3.2,-3.2,3.2,3.2,p.F_CrtYd)
 return f

def build(name,bounds,cutout=None):
 folder=OUT/name;folder.mkdir(exist_ok=True);lib=folder/'OIS.pretty';lib.mkdir(exist_ok=True)
 b=p.BOARD();b.SetCopperLayerCount(4)
 for layer,label in [(p.F_Cu,'F.Cu'),(p.In1_Cu,'In1.Cu'),(p.In2_Cu,'In2.Cu'),(p.B_Cu,'B.Cu')]:b.SetLayerName(layer,label)
 netnames=sorted({n for c in components for n in c['nets'].values() if n})
 nets={}
 for i,n in enumerate(netnames,1):z=p.NETINFO_ITEM(b,n,i);b.Add(z);nets[n]=z
 def outline(box):
  x0,y0,x1,y1=box
  for a,e in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
   s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*e));s.SetWidth(MM(.05));s.SetLayer(p.Edge_Cuts);b.Add(s)
 outline(bounds)
 if cutout:outline(cutout)
 for c in components:
  if c['custom']:f=custom_fp(b,c['custom'],c['ref'])
  else:
   library,part=c['footprint'].split(':');f=p.FootprintLoad('/usr/share/kicad/footprints/'+library+'.pretty',part);assert f,c
  # Copy footprints locally: project remains editable without external libraries.
  fpname=c['custom'] or c['footprint'].replace(':','_');f.SetFPID(p.LIB_ID('OIS',fpname));p.FootprintSave(str(lib),f)
  c['local_footprint']='OIS:'+fpname
  f.SetReference(c['ref']);f.SetValue(c['value']);f.SetPosition(V(*c['xy']));f.SetOrientationDegrees(c['rotation'])
  if c['side']=='B':f.Flip(f.GetPosition(),False)
  f.SetPath(p.KIID_PATH('/'+uid(name)+'/'+uid(name+'/'+c['ref'])))
  for pad in f.Pads():
   n=c['nets'].get(pad.GetNumber())
   if n:pad.SetNet(nets[n])
  if c['ref'].startswith('P'):
   x,y=c['xy'];dx=x-50;dy=y-50
   f.Reference().SetPosition(V(x+(2.2 if dx>0 else -2.2) if abs(dx)>abs(dy) else x,y if abs(dx)>abs(dy) else y+(2.2 if dy>0 else -2.2)))
  if c['ref'].startswith('P'):
   side=(int(c['ref'][1:])-1)//6
   if side%2:f.Reference().SetTextAngle(p.EDA_ANGLE(90,p.DEGREES_T))
   if c['ref'] in ['P18','P6']:f.Reference().SetPosition(V(c['xy'][0],c['xy'][1]+(-2.2 if side==0 else 2.2)))
  if c['ref']=='C2' and name=='tester_dock':f.Reference().SetPosition(V(61.5,14))
  if c['ref']=='U1' and name=='die_carrier':f.Reference().SetVisible(False)
  f.Reference().SetTextSize(V(.8,.8));f.Reference().SetTextThickness(MM(.12));f.Value().SetVisible(False)
  b.Add(f)
 # Screws register the carrier; asymmetric round/slot features key its orientation.
 for i,(x,y) in enumerate([(34,34),(66,34),(66,66),(34,66),(42,32),(58,68)],1):
  f=p.FOOTPRINT(b);f.SetReference('H'+str(i));f.SetValue('M3 clearance' if i<=4 else 'Alignment round' if i==5 else 'Alignment slot');f.Reference().SetVisible(False);f.Value().SetVisible(False)
  z=p.PAD(f);z.SetAttribute(p.PAD_ATTRIB_NPTH);z.SetShape(p.PAD_SHAPE_CIRCLE);size=3.2 if i<=4 else 2.05;z.SetSize(V(size,size));z.SetDrillSize(V(size,size));z.SetLayerSet(layer_set(p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu,p.F_Mask,p.B_Mask))
  if i==6:z.SetDrillShape(p.PAD_DRILL_SHAPE_OBLONG);z.SetSize(V(3.05,2.05));z.SetDrillSize(V(3.05,2.05));z.SetShape(p.PAD_SHAPE_OVAL)
  f.Add(z);kind='Mechanical_'+str(i);f.SetFPID(p.LIB_ID('OIS',kind));p.FootprintSave(str(lib),f);f.SetPosition(V(x,y));b.Add(f)
 def text(s,x,y,size=1,layer=p.F_SilkS):
  t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(V(x,y));t.SetTextSize(V(size,size));t.SetTextThickness(MM(.15));t.SetLayer(layer);b.Add(t)
 text('OIS / '+name, (bounds[0]+bounds[2])/2,bounds[1]+1.5,.8)
 text('REV A / POWER OFF TO SWAP',(bounds[0]+bounds[2])/2,bounds[3]-1.2 if cutout else 60.5,.8)
 if cutout:
  text('OPTICAL APERTURE 22 x 22',50,37.8,.8)
  # Carrier outline is assembly information, not a second board outline.
  s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_RECT);s.SetStart(V(30,30));s.SetEnd(V(70,70));s.SetWidth(MM(.15));s.SetLayer(p.Dwgs_User);b.Add(s)
 else:text('BOND GEOMETRY / FINISH REQUIRE PROVIDER APPROVAL',50,72 if bounds[3]>73 else 61,.55,p.Dwgs_User)
 p.SaveBoard(str(folder/(name+'.kicad_pcb')),b)
 (folder/'fp-lib-table').write_text('(fp_lib_table (lib (name "OIS")(type "KiCad")(uri "${KIPRJMOD}/OIS.pretty")(options "")(descr "Vendored project footprints")))\n')
 project={'meta':{'filename':name+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.3},'defaults':{'copper_line_width':.2}}},'net_settings':{'classes':[{'name':'Default','clearance':.15,'track_width':.2,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.25,'diff_pair_via_gap':.25}],'meta':{'version':3}}}
 (folder/(name+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
 schematic(name,folder)
 (folder/'design.json').write_text(json.dumps(dict(name=name,bounds=bounds,aperture=cutout,components=components),indent=2)+'\n')
 with (folder/'bom.csv').open('w') as file:
  w=csv.writer(file);w.writerow(['Reference','Value_or_MPN','Footprint','Note'])
  for c in components:w.writerow([c['ref'],c['value'],c['local_footprint'],c['note']])
 print(name,len(components),'components',len(nets),'nets',flush=True)

def schematic(name,folder):
 # Self-contained library symbols; all pins explicitly numbered and named.
 libs=[];symbols=[];wires=[]
 for index,c in enumerate(components):
  ref=c['ref'];symbolname='Part_'+ref;libid='OIS:'+symbolname;pinlist=list(c['nets']);count=len(pinlist);half=(count+1)//2;h=max(2.54,(half-1)*1.27+2.54);pins=[];coords={}
  for j,num in enumerate(pinlist):
   left=j<half;k=j if left else j-half;x=-12.7 if left else 12.7;y=(half-1)*1.27-k*2.54;angle=0 if left else 180
   coords[num]=(x,y,left);pn=c['names'].get(num,c['names'].get(int(num),num));pt=c['types'].get(num,c['types'].get(int(num),'passive'))
   pins.append(f'(pin {pt} line (at {x} {y} {angle})(length 2.54)(name {q(pn)} (effects (font (size .9 .9))))(number {q(num)} (effects (font (size .9 .9)))))')
  libs.append(f'''(symbol {q(libid)} (pin_names (offset .5))(in_bom yes)(on_board yes)
  (property "Reference" {q(ref[0])} (at 0 {h+2} 0)(effects (font (size 1.27 1.27))))
  (property "Value" {q(c['value'])} (at 0 {-h-2} 0)(effects (font (size 1 1))))
  (symbol {q(symbolname+'_0_1')} (rectangle (start -10.16 {h})(end 10.16 {-h})(stroke (width .254)(type default))(fill (type background))))
  (symbol {q(symbolname+'_1_1')} {''.join(pins)}))''')
  x=45+(index%10)*77;y=48+(index//10)*62
  fields=f'(property "Reference" {q(ref)} (at {x} {y-h-3} 0)(effects (font (size 1.27 1.27))))(property "Value" {q(c["value"])} (at {x} {y+h+3} 0)(effects (font (size 1 1))))(property "Footprint" {q(c["local_footprint"])} (at {x} {y} 0)(effects (font (size 1 1)) hide))'
  inst=f'(instances (project {q(name)} (path "/{uid(name)}" (reference {q(ref)})(unit 1))))'
  symbols.append(f'(symbol (lib_id {q(libid)})(at {x} {y} 0)(unit 1)(in_bom yes)(on_board yes)(dnp no)(uuid {uid(name+"/"+ref)}){fields}'+''.join(f'(pin {q(n)}(uuid {uid(name+ref+n)}))' for n in pinlist)+inst+')')
  for num,net in c['nets'].items():
   px,py,left=coords[num];ax=x+px;ay=y-py;bx=ax+(-6 if left else 6)
   if net:
    wires.append(f'(wire (pts (xy {ax} {ay})(xy {bx} {ay}))(stroke (width 0)(type default))(uuid {uid(name+ref+num+"wire")}))')
    wires.append(f'(label {q(net)} (at {bx} {ay} 0)(effects (font (size .9 .9))(justify {"right" if left else "left"} bottom))(uuid {uid(name+ref+num+"label")}))')
   else:wires.append(f'(no_connect (at {ax} {ay})(uuid {uid(name+ref+num+"nc")}))')
 s=f'(kicad_sch (version 20230121)(generator eeschema)(uuid {uid(name)})(paper "A1")(title_block (title "{name} - engineering review Rev A")(date "2026-09-19")(rev "A"))(lib_symbols {"".join(libs)})'+''.join(symbols+wires)+')\n'
 (folder/(name+'.kicad_sch')).write_text(s)

# ---------------- reusable tester ----------------
for i in range(1,25):
 n=padnet[i];n=None if n in ['BIAS','PREF'] else n
 add('P'+str(i),'0906-0-15-20-76-14-11-0','OIS:Pogo_0906_0',contact(i),{1:n},custom='Pogo_0906_0',side='B',note='Bottom-facing spring; compression height must be confirmed')
# controller 2x10, nine timing lines alternating grounds; 19 = VIO sense
signals=['RST0','RST1','RST2','ROW0','ROW1','ROW2','SEL0','SEL1','SEL2']
j={}
for i,s in enumerate(signals):j[2*i+1]='CTL_'+s;j[2*i+2]='GND'
j[19]='VDD';j[20]='GND'
add('J1','CONTROLLER_TIMING','Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical',(18,32),j)
add('J2','3V3_INPUT_ONLY','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',(18,18),{1:'VDD',2:'GND'},types={1:'power_out',2:'power_out'},note='Regulated current-limited 3.3 V bench source; no onboard regulator')
add('J3','I2C_AND_ENABLE','Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',(100,22),{1:'VDD',2:'GND',3:'SDA',4:'SCL',5:'ADC_RDY',6:'IO_OE_N'})
add('J4','FAST_ADC_ANALOG','Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',(103,65),{1:'FAST_OUT',2:'GND',3:'VRESET'},note='Analog expansion; no 50-ohm termination; external ADC requires load review')
inputs=[2,4,6,8,11,13,15,17];outputs=[18,16,14,12,9,7,5,3]
for k,pos in enumerate([(34,20),(59,20)]):
 ns={1:'IO_OE_N',19:'IO_OE_N',10:'GND',20:'VDD'};types={1:'input',19:'input',10:'power_in',20:'power_in'};names={1:'1OE_N',19:'2OE_N',10:'GND',20:'VCC'}
 for j,(ip,op) in enumerate(zip(inputs,outputs)):
  index=k*8+j;ns[ip]='CTL_'+signals[index] if index<9 else 'GND';ns[op]='DRV_'+signals[index] if index<9 else None;types[ip]='input';types[op]='tri_state';names[ip]=('1' if j<4 else '2')+'A'+str(j%4+1);names[op]=('1' if j<4 else '2')+'Y'+str(j%4+1)
 add('U'+str(k+1),'SN74LVC244APW','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',pos,ns,names,types)
 capacitor('C'+str(k+1),'100n','VDD','GND',pos[0],pos[1]-6)
for i,s in enumerate(signals):
 # Series resistors and chip-side default pulls: resets high; selects low.
 x=27+i*5;y=27
 resistor('R'+str(i+1),'100','DRV_'+s,s,x,y)
 resistor('R'+str(i+11),'100k',s,'VDD' if s.startswith('RST') else 'GND',x,74)
 resistor('R'+str(i+31),'100k','CTL_'+s,'GND',x,79)
resistor('R21','10k','IO_OE_N','VDD',81,24)
# Dual precision follower: A = pixel buffer, B = reset reference.
add('U3','OPA2320AID','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',(77,52),{1:'BUF_DRV',2:'BUF_DRV',3:'BUF',4:'GND',5:'RESET_DIV',6:'VRESET',7:'VRESET',8:'VDD'},names={1:'OUT_A',2:'IN-_A',3:'IN+_A',4:'V-',5:'IN+_B',6:'IN-_B',7:'OUT_B',8:'V+'},types={1:'output',2:'input',3:'input',4:'power_in',5:'input',6:'input',7:'output',8:'power_in'})
resistor('R22','13k 0.1%','VDD','RESET_DIV',72,60);resistor('R23','20k 0.1%','RESET_DIV','GND',78,60)
capacitor('C3','100n','VDD','GND',77,45);capacitor('C4','10n','RESET_DIV','GND',84,60)
add('U4','ADS1115IDGSR','Package_SO:VSSOP-10_3x3mm_P0.5mm',(95,48),{1:'GND',2:'ADC_RDY',3:'GND',4:'ADC_IN',5:'GND',6:'GND',7:'GND',8:'VDD',9:'SDA',10:'SCL'},names={1:'ADDR',2:'ALERT_RDY',3:'GND',4:'AIN0',5:'AIN1',6:'AIN2',7:'AIN3',8:'VDD',9:'SDA',10:'SCL'},types={1:'input',2:'open_collector',3:'power_in',4:'input',5:'input',6:'input',7:'input',8:'power_in',9:'bidirectional',10:'input'})
capacitor('C5','100n','VDD','GND',95,41);capacitor('C6','1u','VDD','GND',100,41)
resistor('R24','100','BUF_DRV','ADC_IN',87,52);capacitor('C7','10n','ADC_IN','GND',90,56)
resistor('R25','100','BUF_DRV','FAST_OUT',95,65)
for ref,net,x in [('R26','SDA',86),('R27','SCL',91),('R28','ADC_RDY',96)]:resistor(ref,'4.7k',net,'VDD',x,37)
capacitor('C8','10u','VDD','GND',23,18)
build('tester_dock',(10,10,110,90),(39,39,61,61))
# ---------------- replaceable die carrier ----------------
components.clear()
for i in range(1,25):add('P'+str(i),'POGO_TARGET','OIS:Target_2p4',contact(i),{1:None if padnet[i] in ['BIAS','PREF'] else padnet[i]},custom='Target_2p4')
add('U1','OIS_3x3_BARE_DIE_PROVISIONAL','OIS:Bond_3x3_PROVISIONAL',(50,50),padnet,custom='Bond_3x3_PROVISIONAL',note='Landing pad positions/finish and die attach subject to wire-bond provider; not die pad centers')
resistor('R1','5.1M 1%','VDD','BIAS',45,56);resistor('R2','49.9k 1%','PREF','GND',55,56)
capacitor('C1','100n','VDD','GND',45,44)
build('die_carrier',(30,30,70,70))
(OUT/'mechanical.json').write_text(json.dumps(dict(units='mm',dock_bounds=[10,10,110,90],carrier_bounds=[30,30,70,70],aperture=[39,39,61,61],screws=[[34,34],[66,34],[66,66],[34,66]],alignment_round=[42,32],alignment_slot=[58,68],contacts={str(i):contact(i) for i in range(1,25)},stack='Dock above carrier; carrier die faces up through dock opening; springs on dock underside face down.',fabrication_status='PROVISIONAL - bond finish/geometry and standoff stack require approval'),indent=2)+'\n')
