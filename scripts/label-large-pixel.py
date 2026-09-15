"""Code-native SVG callouts over an unmodified VNC screenshot.
Coordinates mapped from the 20um layout: x_screen=363+4.04*x_um,
y_screen=838-4.04*y_um; representative pixel is column0, physical row2.
"""
from pathlib import Path
import base64,html
root=Path(__file__).resolve().parents[1]
b=base64.b64encode((root/'docs/assets/large-pixel-vnc.png').read_bytes()).decode()
labels=[(1,403,394,380,210,'#48ef81','Reset transistor','Charges the sensing node'),(2,464,394,455,210,'#ff7272','Source-follower transistor','Buffers the sensing voltage'),(3,525,394,530,210,'#ffe666','Row-select transistor','Connects the pixel to its column'),(4,605,414,720,210,'#38e4ff','Photodiode / photocell','20 × 20 µm N+/substrate junction'),(5,460,317,870,210,'#ef81ff','Horizontal metal buses','Control, power and local signals'),(6,666,340,1020,210,'#ffb34e','Column output wire','Shared vertical readout'),(7,780,300,1170,210,'#ffffff','Dummy fill','Density pattern around devices')]
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="1330" viewBox="0 0 1680 1330"><title>Labeled 20 micrometre photodiode array</title><rect width="1680" height="1330" fill="#101923"/><image width="1680" height="1050" href="data:image/png;base64,{b}"/>']
for n,x,y,lx,ly,color,title,desc in labels:
 s.append(f'<path d="M {lx} {ly+17} L {x} {y}" fill="none" stroke="#000" stroke-width="6"/><path d="M {lx} {ly+17} L {x} {y}" fill="none" stroke="{color}" stroke-width="2"/><circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{color}" stroke-width="2"/><circle cx="{lx}" cy="{ly}" r="18" fill="#101923" stroke="{color}" stroke-width="3"/><text x="{lx}" y="{ly+7}" text-anchor="middle" fill="white" font-family="sans-serif" font-size="22">{n}</text>')
 col=(n-1)//4;row=(n-1)%4;tx=35+col*835;ty=1120+row*45
 s.append(f'<text x="{tx}" y="{ty}" fill="{color}" font-family="sans-serif" font-size="21">{n}. {html.escape(title)} — {html.escape(desc)}</text>')
s.append('<rect x="565" y="374" width="80" height="80" fill="none" stroke="#38e4ff" stroke-width="2"/><text x="35" y="1082" fill="white" font-family="sans-serif" font-size="25">Inside one pixel — the same three transistors and photodiode repeat nine times</text><text x="35" y="1310" fill="#ccd6e2" font-family="sans-serif" font-size="19">Original VNC screenshot with source-coordinate callouts. Dark diode clearance keeps fill away; it is not extra junction area.</text></svg>')
(root/'docs/assets/large-pixel-labeled.svg').write_text(''.join(s))
