"""Independent physical metal/via checks, without joining matching labels."""
from pathlib import Path
import json,argparse
import klayout.db as k
R=Path(__file__).resolve().parents[1];B=R/'build/routed-demonstrator';m=json.loads((B/'routing.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--gds',type=Path,default=B/'demonstrator_routed.gds');parser.add_argument('--report',type=Path,default=B/'connectivity.json');args=parser.parse_args()
L=k.Layout();L.read(str(args.gds));T=L.cell('demonstrator_routed')
n=k.LayoutToNetlist(k.RecursiveShapeIterator(L,T,[]));layers={z:n.make_polygon_layer(L.layer(z,0),'m'+str(z)) for z in [34,36,42,46,81]}
for region in layers.values():n.connect(region)
for z,lo,hi in [(35,34,36),(38,36,42),(40,42,46),(41,46,81)]:
 via=n.make_polygon_layer(L.layer(z,0),'v'+str(z));n.connect(layers[lo],via);n.connect(via,layers[hi])
n.extract_netlist()
def probe(z,point):
 net=n.probe_net(layers[z],k.DPoint(*point));assert net is not None,(z,point)
 return (net.circuit().name,net.cluster_id)
core={name:probe(z,[x,y]) for name,(x,y,z) in m['ports'].items()};checks=[]
def check(name,ok,detail=None):checks.append(dict(check=name,passed=bool(ok),detail=detail))
check('19 distinct core metal nets',len(set(core.values()))==19,core)
for name,net in core.items():
 matches=[other for other,value in core.items() if value==net and other!=name]
 if matches:print('Shared core net',name,matches)
bonds={p['pad_id']:probe(81,[p['pad_label_x_um'],p['pad_label_y_um']]) for p in m['pad_map']}
for p in m['supply_probes']:check('supply '+p['pad'],bonds[p['pad']]==core[p['net']])
for e in m['protected']:
 target=core[e['net']];bond=bonds[e['pad']];side=probe(36,e['pad_side']);local=probe(36,e['secondary_core'])
 check(e['net']+' pad to secondary input',bond==side)
 check(e['net']+' secondary output to core',local==target)
 check(e['net']+' no metal bypass of series resistor',side!=local)
 check(e['net']+' secondary VDD',probe(36,e['secondary_vdd'])==core['VDD'])
 check(e['net']+' secondary GND',probe(36,e['secondary_gnd'])==core['GND'])
 check(e['net']+' bond not shorted to any core metal net',bond not in core.values())
check('All distinct signal-pad metal nets',len({bonds[p['pad_id']] for p in m['pad_map'] if p['core_net'] not in ['VDD','GND']})==17)
for p in m['pad_map']:
 if p['core_net'] in ['COL0','COL1','COL2','OUT']:check('diagnostic isolated '+p['pad_id'],bonds[p['pad_id']] not in core.values())
for inst in T.each_inst():
 if not inst.cell.name.startswith('gf180mcu_fd_io__'):continue
 for z in [42,46,81]:
  for s in inst.cell.shapes(L.layer(z,10)).each():
   if not s.is_text() or s.text.string not in ['VDD','DVDD','VSS','DVSS']:continue
   v=s.text.trans.disp;pt=inst.cplx_trans*k.Point(v.x,v.y);pt=pt.to_dtype(L.dbu)
   check('macro rail '+inst.cell.name+' '+s.text.string,probe(z,[pt.x,pt.y])==core['VDD' if s.text.string in ['VDD','DVDD'] else 'GND'])
report=dict(passed=all(c['passed'] for c in checks),checks=checks,method='M1–M5 and vias only; no label-based joining, no transistor/diode/poly-resistor device extraction; not LVS')
args.report.write_text(json.dumps(report,indent=2)+'\n')
print('Physical checks',len(checks),'failed',sum(not c['passed'] for c in checks))
for c in checks:
 if not c['passed']:print(c)
assert report['passed']
