"""Add explanatory callouts to the authenticated KLayout view, without changing GDS."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/assets'
metadata = json.loads((ROOT / 'simulations/current-bank-layout-view.json').read_text())
view = metadata['views'][0]
left, bottom, right, top = view['view_box_um']
background, ink, accent = '#0b1725', '#edf5fc', '#72e1d1'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'text.color': ink})
fig = plt.figure(figsize=(16, 9), facecolor=background)
ax = fig.add_axes([0.035, 0.19, 0.91, 0.66])
ax.imshow(mpimg.imread(ROOT / view['image']), extent=(left, right, bottom, top))
ax.set_axis_off()
fig.text(0.045, 0.956, 'Current implemented sensor layout', fontsize=24, weight='bold')
fig.text(0.045, 0.911, '64-column readout bank + one pixel row  |  GF180  |  40 µm column pitch', fontsize=15)
fig.text(0.045, 0.873, 'Exact GDS view. The complete 64 × 64 chip remains to be assembled.', fontsize=12, color=accent)

markers = [
    ('1', (1294, -106), (1294, -45), 'Pixel row · 64 photodiodes'),
    ('2', (1215, 100), (1115, 100), 'Analog capture and readout'),
    ('3', (1515, 500), (1620, 500), 'Storage · 512 MIM plates'),
    ('4', (2300, 912), (2300, 825), 'Ground grid · top and left rails'),
    ('5', (-65, 90), (-65, 230), 'Shared reference MOS pair'),
    ('6', (500, -40), (500, 40), 'Shared supply / control / output buses'),
]
for number, target, label, description in markers:
    ax.annotate(number, xy=target, xytext=label, ha='center', va='center',
                fontsize=14, weight='bold', color=background,
                bbox=dict(boxstyle='circle,pad=0.35', fc=accent, ec=background, lw=1.5),
                arrowprops=dict(arrowstyle='-', color=ink, lw=1.8), zorder=5)
    index = int(number) - 1
    x, y = 0.045 + (index % 3) * 0.32, 0.12 - (index // 3) * 0.047
    fig.text(x, y, number, fontsize=12, weight='bold', color=accent)
    fig.text(x + 0.018, y, description, fontsize=11)

x0, y0, x1, y1 = metadata['bbox_um']
ax.annotate('', xy=(x0, -155), xytext=(x1, -155), annotation_clip=False,
            arrowprops=dict(arrowstyle='|-|', color=ink, lw=1))
ax.text((x0 + x1) / 2, -185, '2,667.87 µm (2.668 mm)', ha='center', va='top', fontsize=12)
ax.annotate('', xy=(2640, y0), xytext=(2640, y1), annotation_clip=False,
            arrowprops=dict(arrowstyle='|-|', color=ink, lw=1))
ax.text(2660, (y0 + y1) / 2, '1,069.80 µm (1.070 mm)', rotation=90,
        ha='left', va='center', fontsize=12)
fig.text(0.045, 0.024, 'Unfilled development layout · scoped DRC/LVS evidence · not a fabrication release',
         fontsize=10, color='#a9bed1')
fig.savefig(ASSETS / 'current-bank-layout-labeled.png', dpi=150, facecolor=background)
plt.close(fig)
