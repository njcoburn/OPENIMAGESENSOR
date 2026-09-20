"""Fresh final-GDS device/lumped-C baseline; intentionally no distributed wire R.
This does not bypass the separate full-chip RC-model acceptance gate.
"""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];B=R/'build/filled-electrical-baseline';B.mkdir(exist_ok=True)
g=R/'build/filled-demonstrator/demonstrator_filled.gds';expected=json.loads((R/'simulations/full-chip-qualification.json').read_text())['gds_sha256'];assert hashlib.sha256(g.read_bytes()).hexdigest()==expected
s=(R/'build/filled-demonstrator/extract-flat.tcl').read_text().replace('extract no capacitance','extract do capacitance').replace('extract no coupling','extract do coupling').replace('ext2spice lvs','ext2spice lvs\next2spice cthresh 0').replace('routed_extracted.spice','filled_lumped.spice')
(B/'extract.tcl').write_text(s)
with (B/'extract.log').open('w') as log:p=subprocess.run(['magic','-dnull','-noconsole','-rcfile','/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc','extract.tcl'],cwd=B,stdout=log,stderr=subprocess.STDOUT,timeout=900)
assert p.returncode==0
n=B/'filled_lumped.spice';assert n.exists();lines=n.read_text().splitlines();counts={c:sum(x.startswith(c) for x in lines) for c in ['X','D','R','C']}
meta=dict(gds_sha256=expected,netlist_sha256=hashlib.sha256(n.read_bytes()).hexdigest(),counts=counts,scope='Fresh device and lumped wiring-capacitance baseline; no distributed wire resistance; extraction and charge audits pending',accepted_full_chip_rc=False)
(B/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
