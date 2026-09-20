from pathlib import Path
import json,difflib,hashlib
P=Path('build/wafer-space-version-audit');A=Path('/foss/pdks/gf180mcuD');B=P/'reference/gf180mcuD'
r='libs.tech/magic/gf180mcuD.tech';d=''.join(difflib.unified_diff((A/r).read_text().splitlines(True),(B/r).read_text().splitlines(True),fromfile='installed',tofile='template'));(P/'magic-tech.diff').write_text(d);print(d[:10000])
def strip_dates(data):
 b=bytearray(data);i=0;n=0
 while i<len(b):
  size=int.from_bytes(b[i:i+2],'big');assert size>=4
  if b[i+2] in [1,5]:b[i+4:i+size]=bytes(size-4);n+=1
  i+=size
 assert i==len(b)
 return b,n
r='libs.ref/gf180mcu_fd_io/gds/gf180mcu_fd_io.gds';a,na=strip_dates((A/r).read_bytes());b,nb=strip_dates((B/r).read_bytes());result=dict(gds_equal_excluding_BGNLIB_BGNSTR_dates=a==b,installed_timestamp_records=na,reference_timestamp_records=nb,installed_normalized_sha256=hashlib.sha256(a).hexdigest(),reference_normalized_sha256=hashlib.sha256(b).hexdigest());print(result);(P/'gds-comparison.json').write_text(json.dumps(result,indent=2))
