"""Explicit MOS-corner selection; diode, MIM and wire corners stay independent."""
import hashlib
from pathlib import Path
import re

CORNERS = ('typical', 'ss', 'ff', 'fs', 'sf')
PDK = Path('/foss/pdks/gf180mcuD/libs.tech/ngspice')


def pdk_provenance(root=PDK):
    root = Path(root)
    files = sorted(p for p in root.rglob('*') if p.is_file())
    assert files and (root/'design.ngspice').exists() and (root/'sm141064.ngspice').exists()
    library = (root/'sm141064.ngspice').read_text()
    sections = set(re.findall(r'^\s*\.lib\s+(\S+)\s*$', library, re.M | re.I))
    assert set(CORNERS) | {'diode_typical', 'mimcap_typical'} <= sections
    return dict(root=str(root), files={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                mos_corners=list(CORNERS), diode_corner='typical', mim_corner='typical',
                scope='Hash all installed ngspice model-directory files; MOS selection only, no supply/wire/diode/MIM corner sweep')


def validate_models(deck, corner):
    assert corner in CORNERS, 'Unsupported MOS corner'
    libraries = [line.strip() for line in deck.splitlines() if line.strip().lower().startswith('.lib ')]
    assert libraries == [f'.lib {PDK}/sm141064.ngspice {corner}',
                         f'.lib {PDK}/sm141064.ngspice diode_typical',
                         f'.lib {PDK}/sm141064.ngspice mimcap_typical'], 'Unexpected process/diode/MIM libraries'
    assert f'.include {PDK}/design.ngspice' in deck.splitlines()


def compare_process_only(typical, candidate, corner):
    """Prove that a MOS-corner deck changes only one library selection."""
    validate_models(typical, 'typical')
    validate_models(candidate, corner)
    def normalized(text):
        return re.sub(r'^\.include .*/tile\.spice$', '.include CANONICAL/tile.spice', text, flags=re.M)
    expected = typical.replace(f'.lib {PDK}/sm141064.ngspice typical\n',
                               f'.lib {PDK}/sm141064.ngspice {corner}\n')
    assert normalized(expected) == normalized(candidate), 'Process change altered other circuit or timing settings'
