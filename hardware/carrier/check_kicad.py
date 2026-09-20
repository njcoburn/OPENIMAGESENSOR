"""Native KiCad load/DRC and independent exported-schematic pin/net comparison."""
from pathlib import Path
import json,subprocess,xml.etree.ElementTree as ET,re,hashlib
import pcbnew as p
R=Path(__file__).resolve().parent;OUT=R/'reports';OUT.mkdir(exist_ok=True)
results={}
for name in ['tester_dock','die_carrier']:
 d=R/'kicad'/name;pcb=d/(name+'.kicad_pcb');sch=d/(name+'.kicad_sch');pro=d/(name+'.kicad_pro')
 subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(OUT/(name+'.xml')),str(sch)],check=True)
 subprocess.run(['kicad-cli','sch','export','svg','-o',str(OUT)+'/',str(sch)],check=True)
 subprocess.run(['kicad-cli','sch','export','pdf','-o',str(OUT/(name+'-schematic.pdf')),str(sch)],check=True)
 sm=p.GetSettingsManager();sm.LoadProject(str(pro));b=p.LoadBoard(str(pcb))
 try:b.SetProject(sm.GetProject(str(pro)))
 except TypeError:b.SetProject(sm.GetProject())
 ds=b.GetDesignSettings();ds.m_MinClearance=p.FromMM(.15);ds.m_TrackMinWidth=p.FromMM(.15);ds.m_CopperEdgeClearance=p.FromMM(.3)
 expected={}
 for net in ET.parse(OUT/(name+'.xml')).findall('.//nets/net'):
  for node in net.findall('node'):expected[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name'].removeprefix('/')
 actual={(f.GetReference(),pad.GetNumber()):pad.GetNetname() for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetCode()>0}
 # Explicit no-connect flags may produce singleton unconnected-(...) net names in exports.
 expected={k:v for k,v in expected.items() if not v.startswith('unconnected-')}
 diff=[(str(k),expected.get(k),actual.get(k)) for k in sorted(expected.keys()|actual.keys()) if expected.get(k)!=actual.get(k)]
 assert not diff,diff
 print(name,'schematic/PCB pin nets match',len(actual),flush=True)
 ok=p.WriteDRCReport(b,str(OUT/(name+'-drc.txt')),p.EDA_UNITS_MILLIMETRES,True)
 assert ok,'No DRC report generated'
 subprocess.run(['kicad-cli','pcb','export','svg','--layers','F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts,User.Drawings','--page-size-mode','2','--exclude-drawing-sheet','-o',str(OUT/(name+'-pcb.svg')),str(pcb)],check=True)
 txt=(OUT/(name+'-drc.txt')).read_text();results[name]=dict(schematic_pin_net_match=True,pin_count=len(actual),drc_summary=re.findall(r'^\*\*.*',txt,re.M),kicad_version=p.GetBuildVersion(),error_count=len(re.findall(r'Severity: error',txt)),warning_count=len(re.findall(r'Severity: warning',txt)),pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),schematic_sha256=hashlib.sha256(sch.read_bytes()).hexdigest(),erc='Not run: use KiCad GUI')
 print(results[name],flush=True)
(OUT/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
