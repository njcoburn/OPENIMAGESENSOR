"""Label bond nets and generate an independent hierarchical assembly reference."""
from pathlib import Path
import json
import klayout.db as k
R=Path(__file__).resolve().parents[1];B=R/'build/routed-demonstrator';m=json.loads((B/'routing.json').read_text());L=k.Layout();L.read(str(B/'demonstrator_routed.gds'));T=L.cell('demonstrator_routed')
external=[];mapping={}
for p in m['pad_map']:
 net=p['core_net'];name=net if net in ['VDD','GND'] else 'NC_'+p['pad_id'] if net in ['COL0','COL1','COL2','OUT'] else 'PAD_'+net
 if name not in external:external.append(name)
 mapping[p['pad_id']]=name
 T.shapes(L.layer(81,10)).insert(k.Text(name,k.Trans(round(p['pad_label_x_um']/L.dbu),round(p['pad_label_y_um']/L.dbu))))
sp=['* Independent functional reference for the routed 24-pad working layout.','* Four diagnostic pad diodes are present but disconnected from sensor diagnostics.', '.include /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/spice/gf180mcu_fd_io.spice','.include /foss/designs/circuits/integrated.spice','.include /foss/designs/circuits/analog-secondary.spice','.subckt demonstrator_routed '+' '.join(external)]
coreports=next(l.split()[2:] for l in (R/'circuits/integrated.spice').read_text().splitlines() if l.startswith('.subckt sensor_3x3 '))
sp+=['Xcore '+' '.join(n if n in ['VDD','GND'] else 'CORE_'+n for n in coreports)+' sensor_3x3']
for p in m['pad_map']:
 net=p['core_net'];name=mapping[p['pad_id']];tag=p['pad_id']
 if net=='VDD':sp.append(f'X{tag} VDD GND GND gf180mcu_fd_io__dvdd')
 elif net=='GND':sp.append(f'X{tag} VDD GND VDD gf180mcu_fd_io__dvss')
 else:
  sp.append(f'X{tag} {name} VDD GND VDD GND gf180mcu_fd_io__asig_5p0')
  if net not in ['COL0','COL1','COL2','OUT']:sp.append(f'Xprotect_{tag} {name} CORE_{net} VDD GND analog_secondary')
for i in range(4):sp.append(f'Xcorner{i} VDD GND VDD GND gf180mcu_fd_io__cor')
for i in range(20):sp.append(f'Xfill{i} VDD GND VDD GND gf180mcu_fd_io__fill10')
sp.append('.ends demonstrator_routed');(R/'circuits/demonstrator-routed.spice').write_text('\n'.join(sp)+'\n')
options=k.SaveLayoutOptions();options.add_cell(T.cell_index());L.write(str(B/'demonstrator_routed.gds'),options)
(B/'external-ports.json').write_text(json.dumps(dict(ports=external,pad_nets=mapping),indent=2)+'\n')
tcl=['gds read /foss/designs/build/routed-demonstrator/demonstrator_routed.gds','load demonstrator_routed','select top cell']
for i,name in enumerate(external,1):tcl+=['catch {port '+name+' make '+str(i)+'}','port '+name+' index '+str(i)]
tcl+=['drc check','drc catchup','puts "ROUTED_DRC_COUNT=[drc list count total]"','if {[drc list count total] > 0} {puts "ROUTED_DRC_DETAILS=[drc listall why]"}','flatten routed_flat','load routed_flat','select top cell','extract no capacitance','extract no coupling','extract no resistance','extract all','ext2spice lvs','ext2spice extresist off','ext2spice short resistor','ext2spice subcircuits top on','ext2spice -o routed_extracted.spice routed_flat','quit -noprompt']
(B/'verify.tcl').write_text('\n'.join(tcl)+'\n')
print('Generated reference and',len(external),'external logical nets, including four unconnected diagnostic pads.')
