"""Prepare a hierarchy-preserving final-GDS capacitance extraction fallback.
Preparation only: does not launch Magic or certify extraction. Avoid flattening
all repeated pad/fill geometry; validate hierarchy/device and capacitance results
before use. Run after any flat extraction has stopped, not concurrently.
"""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];B=R/'build/filled-electrical-hierarchical';B.mkdir(exist_ok=True)
g=R/'build/filled-demonstrator/demonstrator_filled.gds';h=hashlib.sha256(g.read_bytes()).hexdigest();assert h==json.loads((R/'simulations/full-chip-qualification.json').read_text())['gds_sha256']
s=(R/'build/filled-demonstrator/extract-flat.tcl').read_text();s=s.replace('flatten routed_flat\nload routed_flat\nselect top cell\n','').replace('extract no capacitance','extract do capacitance').replace('extract no coupling','extract do coupling').replace('ext2spice lvs','ext2spice lvs\next2spice cthresh 0').replace('ext2spice -o routed_extracted.spice routed_flat','ext2spice -o filled_hierarchical.spice demonstrator_routed')
(B/'extract.tcl').write_text(s);(B/'inputs.json').write_text(json.dumps(dict(gds_sha256=h,scope='Prepared hierarchy-preserving device/lumped-C extraction; not run or audited; no wire R'),indent=2)+'\n');print('Prepared',B/'extract.tcl')
