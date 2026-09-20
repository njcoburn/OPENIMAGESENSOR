import urllib.request,json
from pathlib import Path
p=Path(__file__).resolve().parent
for repo in ['gf180mcu-project-template','gf180mcu-precheck']:
 for file in ['Makefile','flake.lock']:
  u=f'https://raw.githubusercontent.com/wafer-space/{repo}/main/{file}'
  try:
   data=urllib.request.urlopen(u,timeout=25).read();(p/(repo+'-'+file)).write_bytes(data)
   if file=='flake.lock':
    d=json.loads(data);print(repo,{k:v.get('locked',{}) for k,v in d['nodes'].items() if k in ['librelane','nix-eda','nixpkgs']})
  except Exception as e:print(str(e))
for rev in ['f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7','d658698bd8bcf4e05fc7b5991a701247ba0d744c','b344c97eacc2aaf8e14ae7e43e2e9dc0871de2c0']:
 u=f'https://api.github.com/repos/fossi-foundation/ciel-releases/releases/tags/gf180mcu-{rev}'
 try:
  d=json.load(urllib.request.urlopen(u,timeout=25));(p/(rev+'-release.json')).write_text(json.dumps(d,indent=2));print(rev,d.get('published_at'),[(a['name'],a['size']) for a in d.get('assets',[])][:15])
 except Exception as e:print(rev,str(e))
