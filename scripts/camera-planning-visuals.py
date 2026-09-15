"""Scientific sampling illustration and conceptual floorplan; no sensor prediction."""
from pathlib import Path
import numpy as np,json,base64
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
root=Path(__file__).resolve().parents[1];assets=root/'docs/assets'
a=plt.imread(assets/'resolution-source.png')[...,:3].astype(float)
if a.max()>1:a/=255
linear=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
lum=linear@np.array([.2126,.7152,.0722])
def weights(length,n):
 e=np.linspace(0,length,n+1);p=np.arange(length)
 return np.maximum(0,np.minimum(e[1:,None],p+1)-np.maximum(e[:-1,None],p))/(length/n)
def display(x):return np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055)
sizes=[3,8,16,32,64,96,128,256];frames={}
fig,axes=plt.subplots(3,3,figsize=(11,12),layout='constrained')
for ax,n in zip(axes.flat,sizes):
 small=weights(lum.shape[0],n)@lum@weights(lum.shape[1],n).T
 pix=np.rint(np.clip(display(small),0,1)*255).astype('uint8')
 assert pix.shape==(n,n)
 frames[str(n)]=base64.b64encode(pix.tobytes()).decode()
 ax.imshow(pix,cmap='gray',vmin=0,vmax=255,interpolation='nearest');ax.set_title(f'{n} × {n} = {n*n:,} pixels');ax.axis('off')
axes.flat[-1].imshow(display(lum),cmap='gray',vmin=0,vmax=1);axes.flat[-1].set_title('Full-resolution synthetic source');axes.flat[-1].axis('off')
fig.suptitle('Same scene, same field of view — only the sampling grid changes\nIdeal grayscale sampling; not simulated GF180 camera output',fontsize=14)
fig.savefig(assets/'resolution-comparison.png',dpi=150);plt.close(fig)
(root/'simulations/resolution-demo.json').write_text(json.dumps({'sizes':sizes,'frames_gray8_base64':frames,'method':'Linear-light area averaging, sRGB display encoding, nearest-neighbor enlargement. AI-generated source; no noise, optics or GF180 response model.'})+'\n')
fig,ax=plt.subplots(figsize=(7,8),layout='constrained')
for x,y,w,h,color,label in [(0,0,3.93,5.12,'#d5dce6',''),(.44,.44,3.05,4.24,'#f8fafc',''),(.70,1.65,2.56,2.56,'#80c8dc','64 × 64 array\n40 µm pitch (proposed)\n2.56 × 2.56 mm'),(.7,.65,2.56,.7,'#f6ce82','Column circuits, mux, buffer\nSpace reservation only'),(.46,1.65,.18,2.56,'#b5d69b','')]:
 ax.add_patch(Rectangle((x,y),w,h,facecolor=color,edgecolor='#334155',linewidth=1.3))
 if label:ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10 if x else 0)
ax.text(1.965,4.91,'Pads / protection / seal ring around perimeter',ha='center',fontsize=10)
ax.text(1.965,4.40,'Core: 3.05 × 4.24 mm',ha='center',fontsize=11)
ax.text(.55,2.93,'Row control',rotation=90,ha='center',va='center',fontsize=8)
ax.set(xlim=(-.1,4.05),ylim=(-.1,5.23),xlabel='mm',ylabel='mm',title='Concept only — full slot with reserved periphery\nNot a routed or verified chip floorplan');ax.set_aspect('equal')
fig.savefig(assets/'camera-floorplan-concept.png',dpi=150);plt.close(fig)
print('Wrote sampling comparison, interactive pixel data and conceptual floorplan.')
