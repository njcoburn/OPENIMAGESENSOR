"""Render actual joined-tile polygons and a zoom of the pixel/column wiring."""
from pathlib import Path
import argparse
import klayout.db as k
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle,Patch
from matplotlib.collections import PatchCollection


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();ly=k.Layout();ly.read(str(a.layout/'tile.gds'));top=ly.cell('compact_tile')
    layers=[(21,'Well','#ddbbe8'),(22,'Diffusion','#78ba80'),(30,'Poly','#eea752'),
            (34,'M1','#6483c9'),(36,'M2','#179ca3'),(42,'M3','#ab62ad'),
            (46,'M4','#df676d'),(75,'MIM','#c6af6c'),(81,'M5','#566e87')]
    fig,axes=plt.subplots(1,2,figsize=(9,9),layout='constrained',gridspec_kw={'width_ratios':[1,1.5]})
    for ax in axes:
        for layer,name,color in layers:
            polygons=[]
            for poly in k.Region(top.begin_shapes_rec(ly.layer(layer,0))).merged().each():
                # Bridge holes into the contour so metal rings do not paint
                # over the actual clear optical region in the visualization.
                contour=poly.resolved_holes()
                polygons.append(Polygon([(v.x*ly.dbu,v.y*ly.dbu) for v in contour.each_point_hull()],closed=True))
            ax.add_collection(PatchCollection(polygons,facecolor=color,edgecolor='none',alpha=.8,rasterized=True))
        ax.add_patch(Rectangle((5,-76),18,18,fill=False,edgecolor='#09692c',lw=1.2,ls='--'))
        ax.set_aspect('equal');ax.set_xlabel('x (µm)');ax.set_ylabel('y (µm)');ax.grid(alpha=.12)
    axes[0].set(xlim=(-20,65),ylim=(-90,875),title='One physical pixel and capture column')
    axes[0].annotate('Eight MIM plates',xy=(18,500),xytext=(55,520),rotation=90,ha='center',fontsize=9)
    axes[0].add_patch(Rectangle((-13,-82),55,94,fill=False,edgecolor='#222',lw=1))
    axes[1].set(xlim=(-15,45),ylim=(-83,10),title='Extracted joining routes')
    for label,x,y in [('VDD',-4,-10),('GND',-10,-20),('COL',30,-30)]:
        axes[1].annotate(label,xy=(x,y),xytext=(x+3,y+4),fontsize=10,arrowprops=dict(arrowstyle='-',lw=.7))
    axes[1].text(14,-68,'18 × 18 µm\nmetal-clear region',ha='center',va='center',fontsize=8)
    fig.legend(handles=[Patch(color=color,label=name) for _,name,color in layers],loc='outside lower center',ncol=5,fontsize=8)
    fig.suptitle('Compact joined tile • actual GDS geometry\nUnfilled development layout; no foundry optical-opening approval',fontsize=12)
    a.out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.out,dpi=180);plt.close(fig)


if __name__=='__main__':main()
