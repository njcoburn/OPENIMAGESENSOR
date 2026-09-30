"""Label the exact pixel crop after rendering it with KLayout."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/assets'
metadata = json.loads((ROOT / 'simulations/current-pixel-layout-view.json').read_text())
bounds = metadata['view_box_um']
background, ink, accent = '#0b1725', '#edf5fc', '#72e1d1'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'text.color': ink})
fig = plt.figure(figsize=(16, 9), facecolor=background)
ax = fig.add_axes([0.035, 0.13, 0.56, 0.73])
left, bottom, right, top = bounds
ax.imshow(mpimg.imread(ASSETS / 'current-pixel-layout.png'), extent=(left, right, bottom, top))
ax.set_axis_off()
fig.text(0.045, 0.953, 'One pixel, labeled', fontsize=25, weight='bold')
fig.text(0.045, 0.908, 'Row 0, column 0 · exact crop of the implemented GDS · 40 µm pixel pitch', fontsize=14)
markers = [
    ('1', (6, -92), (6, -95)),
    ('2', (14, -92), (14, -95)),
    ('3', (22, -92), (22, -95)),
    ('4', (14, -107), (14, -107)),
    ('5', (32, -85.2), (33, -90)),
]
for number, target, label in markers:
    ax.annotate(number, xy=target, xytext=label, ha='center', va='center',
                fontsize=12, weight='bold', color=background,
                bbox=dict(boxstyle='circle,pad=0.25', fc=accent, ec=background, lw=1.2),
                arrowprops=dict(arrowstyle='-', color=ink, lw=1.5), zorder=5)
ax.add_patch(Rectangle((5, -116), 18, 18, fill=False, edgecolor=accent,
                       linewidth=2, linestyle='--'))
ax.annotate('', xy=(0, -123), xytext=(40, -123), annotation_clip=False,
            arrowprops=dict(arrowstyle='|-|', color=ink))
ax.text(20, -124, '40 µm column pitch', fontsize=12, ha='center', va='top')
labels = [
    ('1  Reset transistor', 'RST0 connects the sense node to VRESET.\nThis initializes the pixel before exposure.'),
    ('2  Source follower', 'Buffers the photodiode sense voltage.\nIts drain connects to VDD.'),
    ('3  Row-select transistor', 'ROW0 connects the buffered pixel signal\nto the COL0 readout line.'),
    ('4  Photodiode / sensing region', '20 × 20 µm junction. Dashed outline:\n18 × 18 µm area clear of M1–M5 metal.'),
    ('5  Pixel wiring and shared rails', 'Reset, row select, supplies and signal wiring.\nCOL0 leaves the pixel near the right edge.'),
]
for index, (title, description) in enumerate(labels):
    y = 0.79 - index * 0.137
    fig.text(0.62, y, title, fontsize=16, weight='bold', color=accent)
    fig.text(0.62, y - 0.061, description, fontsize=12, linespacing=1.6)
fig.text(0.045, 0.035, 'Three-transistor pixel · annotations are explanatory overlays · optical opening and final-chip checks remain open',
         fontsize=11, color='#a9bed1')
fig.savefig(ASSETS / 'current-pixel-layout-labeled.png', dpi=150, facecolor=background)
plt.close(fig)
