gds read /foss/designs/build/column_readout.gds
load column_readout
select top cell
set idx 1
foreach pin {GND BIAS COL0 COL1 COL2 OUT SEL0 SEL1 SEL2} {
 catch {port $pin make $idx}
 port $pin index $idx
 incr idx
}
drc check
drc catchup
puts "READOUT_DRC_COUNT=[drc list count total]"
puts "READOUT_DRC_DETAILS=[drc listall why]"
extract all
ext2spice lvs
ext2spice hierarchy on
ext2spice subcircuits top on
ext2spice -o readout_extracted.spice
quit -noprompt
