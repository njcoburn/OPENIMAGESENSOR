"""Main DRC/LVS for a compact capture column plus a 40 um abutment control.

Run in the pinned EDA container. No density/antenna/CUP or shared-bank claims.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import klayout.db as k

ROOT = Path(__file__).resolve().parents[1]
PDK = Path('/foss/pdks/gf180mcuD/libs.tech')


def command(args, directory, log):
    result = subprocess.run(list(map(str, args)), cwd=directory,
                            capture_output=True, text=True, timeout=600)
    (directory/log).write_text(result.stdout+result.stderr)
    assert result.returncode == 0, log


def drc(directory, gds, top, report, log):
    command(['klayout', '-b', '-r', PDK/'klayout/tech/drc/gf180mcu.drc',
             '-rd', f'input={directory/gds}', '-rd', f'report={directory/report}',
             '-rd', f'topcell={top}', '-rd', 'variant=gf180mcuD', '-rd', 'threads=2',
             '-rd', 'decks=all,-antenna,-density,-cup'], directory, log)
    count = len(ET.parse(directory/report).getroot().find('items'))
    assert count == 0, (report, count)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--regression', type=Path)
    a = p.parse_args()
    d = a.run.resolve()
    (d/'check-compact-capture.py').write_bytes(Path(__file__).read_bytes())
    (d/'verify-capture-column-stack3.py').write_bytes((ROOT/'scripts/verify-capture-column-stack3.py').read_bytes())
    drc(d, 'column.gds', 'capture_column', 'main-drc.lyrdb', 'klayout.log')
    command([sys.executable, ROOT/'scripts/verify-capture-column-stack3.py', '--run', d], d, 'verification.log')
    ly = k.Layout()
    ly.read(str(d/'column.gds'))
    top = ly.create_cell('abutment')
    for x in [0, 40]:
        top.insert(k.CellInstArray(ly.cell('capture_column').cell_index(), k.Trans(round(x/ly.dbu), 0)))
    ly.write(str(d/'abutment.gds'))
    drc(d, 'abutment.gds', 'abutment', 'abutment-drc.lyrdb', 'abutment-klayout.log')
    result = dict(main_drc_pass=True, direct_and_rc_collapsed_lvs_pass=True,
                  abutment_main_drc_pass=True, abutment_pitch_um=40,
                  abutment_scope='Two independent column instances; shared routing and bank connectivity unimplemented.')
    if a.regression:
        old = k.Layout()
        old.read(str(ROOT/'build/capture-column-routed-v8-20260925/column.gds'))
        new = k.Layout()
        new.read(str(a.regression/'column.gds'))
        assert old.dbu == new.dbu
        layers = set(old.layer_infos()) | set(new.layer_infos())
        for info in layers:
            before = k.Region(old.cell('capture_column').begin_shapes_rec(old.layer(info)))
            after = k.Region(new.cell('capture_column').begin_shapes_rec(new.layer(info)))
            assert (before ^ after).is_empty(), str(info)
        assert (a.regression/'direct.spice').read_bytes() == (ROOT/'build/capture-column-routed-v8-20260925/direct.spice').read_bytes()
        result['default_geometry_xor_empty_all_layers'] = True
        result['default_direct_netlist_byte_identical'] = True
    result['hashes'] = {name: hashlib.sha256((d/name).read_bytes()).hexdigest()
                        for name in ['column.gds', 'abutment.gds', 'main-drc.lyrdb', 'abutment-drc.lyrdb']}
    (d/'compact-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
