"""Repack unchanged GF180 primitives at 40 um pitch and verify small arrays.

Development geometry only: no fill, process aperture waiver or chip signoff.
Run in the pinned EDA container; every output directory must be new.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import xml.etree.ElementTree as ET
import klayout.db as k

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('strips', ROOT/'scripts/prepare-array-strips.py')
strips = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strips)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for source in [Path(__file__), ROOT/'scripts/prepare-array-strips.py']:
        (out/source.name).write_bytes(source.read_bytes())
    ly = k.Layout()
    sources = [ROOT/'build/layout-probe-verified/nfet_probe.gds',
               ROOT/'build/size-study/20um/build/array-primitives/photodiode.gds']
    for source in sources:
        ly.read(str(source))
    # Magic FIXED_BBOX annotations are not fabricated geometry.
    ly.clear_layer(ly.layer(0, 0))
    pixel = ly.create_cell('pixel_physical')
    dbu = ly.dbu

    def box(metal, x0, y0, x1, y1):
        pixel.shapes(ly.layer(metal, 0)).insert(k.Box(*[round(v/dbu) for v in (x0,y0,x1,y1)]))

    def wire(metal, x0, y0, x1, y1):
        assert x0 == x1 or y0 == y1
        box(metal, min(x0,x1)-.2, min(y0,y1)-.2, max(x0,x1)+.2, max(y0,y1)+.2)

    def via(x, y, upper=False):
        low, cut, high, size = (36,38,42,.6) if upper else (34,35,36,.48)
        for metal in [low, high]:
            box(metal, x-size/2, y-size/2, x+size/2, y+size/2)
        box(cut, x-.13, y-.13, x+.13, y+.13)

    rails = dict(zip(['GND','sense','sf','RST','ROW','VRESET','VDD','COL'],
                     [30,31.2,32.4,33.6,34.8,36,37.2,38.4]))
    for name, y in rails.items():
        x0,x1 = (0,40) if name in ['GND','RST','ROW','VRESET','VDD'] else (2,38.5)
        wire(36,x0,y,x1,y)

    def terminal(x,y,track,net):
        via(x,y)
        wire(36,x,y,track,y)
        via(track,y,True)
        wire(42,track,y,track,rails[net])
        via(track,rails[net],True)

    for x,nets in [(6,('VRESET','RST','sense')),
                   (14,('VDD','sense','sf')),(22,('sf','ROW','COL'))]:
        pixel.insert(k.CellInstArray(ly.cell('nfet_probe').cell_index(),k.Trans(round(x/dbu),round(28/dbu))))
        terminal(x+.51,28,x+2,nets[0])
        terminal(x,28.94,x,nets[1])
        terminal(x-.51,28,x-2,nets[2])
        terminal(x,26.46,x+3.2,'GND')
    pixel.insert(k.CellInstArray(ly.cell('photodiode').cell_index(),k.Trans(round(14/dbu),round(13/dbu))))
    terminal(23.5,13,27,'sense')
    terminal(14,2.51,28.5,'GND')
    via(38.5,38.4,True)
    source = out/'pixel.gds'
    ly.write(str(source))
    # Central 18 x 18 um clear area is a geometric audit, not a foundry aperture rule.
    aperture = k.Region(k.Box(*[round(v/dbu) for v in (5,4,23,22)]))
    metals = k.Region()
    for metal in [34,36,42,46,81]:
        metals += k.Region(pixel.begin_shapes_rec(ly.layer(metal,0)))
    assert (metals & aperture).is_empty(), 'Metal obstructs central aperture'
    bbox = pixel.dbbox()
    assert bbox.left >= -.2 and bbox.right <= 40.2 and bbox.bottom >= 0 and bbox.top <= 40
    report = dict(pixel_pitch_um=[40,40], pixel_bbox_um=str(bbox),
                  diode_area_um2=400, diode_perimeter_um=80,
                  nfet_W_um=1, nfet_L_um=.5, central_clear_aperture_um=[18,18],
                  source_sha256={str(p.relative_to(ROOT)):strips.sha(p) for p in sources},
                  pixel_sha256=strips.sha(source), cases=[],
                  scope='Unfilled compact pixel and small boundary controls; no electrical transient or full-chip signoff.',
                  excluded_drc_decks=['antenna','density','cup'])
    (out/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    for nr,nc in [(1,1),(2,2)]:
        result = strips.build(out,nr,nc,pixel_source=source,pitch=(40,40),rail_y=rails,column_x=38.5)
        d = out/f'r{nr}c{nc}'
        strips.run(['klayout','-b','-r',str(strips.PDK/'klayout/tech/drc/gf180mcu.drc'),
                    '-rd',f'input={d}/strip.gds','-rd',f'report={d}/main-drc.lyrdb',
                    '-rd','topcell=strip','-rd','variant=gf180mcuD','-rd','threads=2',
                    '-rd','decks=all,-antenna,-density,-cup'],d,'klayout.log')
        errors = len(ET.parse(d/'main-drc.lyrdb').getroot().find('items'))
        result['klayout_main_drc_errors'] = errors
        report['cases'].append(result)
        (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        assert errors == 0, (d,errors)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
