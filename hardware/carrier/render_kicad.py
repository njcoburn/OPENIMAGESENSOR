"""Render actual PCB geometry to portable review PNGs (not fabrication plots)."""
from pathlib import Path
import pcbnew as p
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(n):
 try:return ImageFont.truetype(fontpath,n)
 except OSError:return ImageFont.load_default()
for name in ['tester_dock','die_carrier']:
 b=p.LoadBoard(str(R/'kicad'/name/(name+'.kicad_pcb')))
 import json
 meta=json.loads((R/'kicad'/name/'design.json').read_text());x0,y0,x1,y1=meta['bounds'];scale=14 if name=='tester_dock' else 28;margin=65
 w=round((x1-x0)*scale)+2*margin;h=round((y1-y0)*scale)+2*margin+100
 im=Image.new('RGB',(w,h),'#edf2f7');d=ImageDraw.Draw(im)
 def xy(x,y):return (round((x-x0)*scale)+margin,round((y-y0)*scale)+margin+45)
 def pt(v):return xy(p.ToMM(v.x),p.ToMM(v.y))
 d.text((margin,15),name.replace('_',' ').upper()+' — REVIEW PROTOTYPE',fill='#10263b',font=font(25))
 d.rectangle([xy(x0,y0),xy(x1,y1)],fill='#143d39',outline='#071c22',width=3)
 if meta['aperture']:
  a,c,e,f=meta['aperture'];d.rectangle([xy(a,c),xy(e,f)],fill='#edf2f7',outline='black',width=3)
  d.text(xy(40,48),'OPTICAL\nOPENING',fill='#10263b',font=font(18))
 colors={p.B_Cu:'#7294ea',p.In2_Cu:'#9c789d',p.In1_Cu:'#638d80',p.F_Cu:'#ea8953'}
 tracks=list(b.GetTracks())
 for layer,color in colors.items():
  for t in tracks:
   if t.GetClass()=='PCB_VIA' or t.GetLayer()!=layer:continue
   d.line([pt(t.GetStart()),pt(t.GetEnd())],fill=color,width=max(1,round(p.ToMM(t.GetWidth())*scale)))
 for t in tracks:
  if t.GetClass()!='PCB_VIA':continue
  x,y=pt(t.GetPosition());r=p.ToMM(t.GetWidth())*scale/2;d.ellipse((x-r,y-r,x+r,y+r),fill='#cfb873');r=p.ToMM(t.GetDrillValue())*scale/2;d.ellipse((x-r,y-r,x+r,y+r),fill='#102328')
 for f in b.GetFootprints():
  for pad in f.Pads():
   x,y=pt(pad.GetPosition());sx=p.ToMM(pad.GetSize().x)*scale/2;sy=p.ToMM(pad.GetSize().y)*scale/2
   if abs(pad.GetOrientationDegrees())%180==90:sx,sy=sy,sx
   color='#e5c875' if pad.GetNetCode() else '#938467'
   if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:color='#edf2f7'
   box=(x-sx,y-sy,x+sx,y+sy)
   if pad.GetShape() in [p.PAD_SHAPE_CIRCLE,p.PAD_SHAPE_OVAL]:d.ellipse(box,fill=color)
   else:d.rectangle(box,fill=color)
   if pad.GetAttribute()==p.PAD_ATTRIB_PTH:
    r=p.ToMM(pad.GetDrillSize().x)*scale/2;d.ellipse((x-r,y-r,x+r,y+r),fill='#102328')
  if f.GetReference().startswith('H'):continue
  if f.Reference().IsVisible():d.text(pt(f.Reference().GetPosition()),f.GetReference(),fill='white',font=font(13),anchor='mm')
 if name=='die_carrier':
  d.rectangle([xy(49.395,49.395),xy(50.605,50.605)],fill='#3c4467',outline='white',width=2)
  d.text(xy(46.5,48),'DIE / BOND AREA',fill='white',font=font(15))
 d.text((margin,h-38),'Actual PCB geometry • all copper layers shown • bond and mechanical review pending',fill='#10263b',font=font(16))
 im.save(R/'reports'/(name+'-layout.png'))
