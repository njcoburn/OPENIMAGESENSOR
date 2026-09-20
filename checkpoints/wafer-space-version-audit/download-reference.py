import json,urllib.request,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
p=Path(__file__).resolve().parent;rev='f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7';d=json.loads((p/(rev+'-release.json')).read_text())
def fetch(a):
 f=p/a['name'];urllib.request.urlretrieve(a['browser_download_url'],f);h=hashlib.file_digest(f.open('rb'),'sha256').hexdigest();assert f.stat().st_size==a['size'];assert not a.get('digest') or a['digest']=='sha256:'+h;print(a['name'],h,flush=True)
with ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(fetch,[a for a in d['assets'] if a['name'] in ['common.tar.zst','gf180mcu_fd_io.tar.zst']]))
